from fastapi import APIRouter, Depends, UploadFile, File, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse
import pandas as pd
from io import BytesIO
import time
import json
import asyncio
from api.core.logging_config import logger
from api import agent, db, llm, schema
from sqlmodel import Session
from typing import Annotated
import math
from uuid import uuid4
from api.core.config import settings
import websockets

# Global queue for streaming
test_queue = asyncio.Queue()
SessionDep = Annotated[Session, Depends(db.get_session)]

router = APIRouter()

score_llm = llm.get_chat_model(
    model_name=settings.SUMMARIZATION_SCORE_MODEL, cache=True
)
score_chain = llm.create_chain_for_task(
    task="summary score", llm=score_llm, output_schema=schema.ScoreResponse
)


@router.get("/run_tests_stream/")
async def run_tests_stream():
    async def event_generator():
        try:
            while True:
                result = await test_queue.get()
                yield f"data: {json.dumps(result)}\n\n"
                test_queue.task_done()
                if "error" in result:
                    break
        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/count_test_cases/")
async def count_test_cases(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))
        return {"total_cases": len(df)}
    except Exception as e:
        logger.error(f"Error counting test cases: {e}")
        raise HTTPException(
            status_code=400, detail=f"Error counting test cases: {str(e)}"
        )


@router.post("/preview_test_cases/")
async def preview_test_cases(file: UploadFile = File(...)):
    try:
        content = await file.read()
        df = pd.read_excel(BytesIO(content))

        # Ensure expected columns exist
        expected_columns = [
            "Sl No",
            "Input",
            "Actual Intent",
            "Actual Response",
            "Directives",
        ]
        missing_columns = [col for col in expected_columns if col not in df.columns]
        if missing_columns:
            logger.error(f"Missing columns in Excel file: {missing_columns}")
            raise HTTPException(
                status_code=400, detail=f"Missing columns: {missing_columns}"
            )

        # Sanitize DataFrame for JSON compliance
        df = df.copy()  # Avoid modifying the original DataFrame
        # Replace NaN with None
        df = df.where(df.notna(), None)
        # Handle Inf/-Inf in numeric columns
        for col in df.select_dtypes(include=["float64", "float32"]).columns:
            df[col] = df[col].apply(
                lambda x: (
                    None if x is not None and (math.isinf(x) or math.isnan(x)) else x
                )
            )
        # Convert Sl No to integer, filling None with 0
        if "Sl No" in df.columns:
            df["Sl No"] = (
                pd.to_numeric(df["Sl No"], errors="coerce").fillna(0).astype(int)
            )
        # Ensure string columns are strings
        for col in ["Input", "Actual Intent", "Actual Response", "Directives"]:
            df[col] = df[col].astype(str).replace("nan", "")

        # Convert to JSON-compatible dictionary
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error previewing test cases: {e}")
        raise HTTPException(
            status_code=400, detail=f"Error previewing test cases: {str(e)}"
        )


@router.post("/run_tests/")
async def run_tests(
    session: SessionDep, background_tasks: BackgroundTasks, file: UploadFile = File(...)
):
    async def process_file(file_content: bytes):
        try:
            df = pd.read_excel(BytesIO(file_content))

            for index, row in df.iterrows():
                start_time = time.time()
                query = row.get("Input", "")
                expected_intent = row.get("Actual Intent", "")
                expected_response = row.get("Actual Response", "")
                directives = row.get("Directives", "")

                if not query or not expected_intent:
                    await test_queue.put(
                        {
                            "error": f"Invalid row {index + 1}: Missing query or expected intent"
                        }
                    )
                    continue

                orch_response = await agent.get_orchestrator_response(query)

                predicted_intent = orch_response.category if orch_response else "error"
                logger.info(
                    f"{index+1}) Input: {query} | Predicted: {predicted_intent} | Actual: {expected_intent}"
                )

                predicted_response = ""
                summarization_analysis = ""
                summarization_score = None
                status = "Failure"

                if predicted_intent != expected_intent:
                    status = "Failure"
                else:
                    status = "Success"
                    try:
                        if predicted_intent == "navigation":
                            logger.info(f"[[Navigation]]")
                            graph_result = await agent.navigation_graph.ainvoke(
                                {"query": query}
                            )
                            nav = graph_result["navigation"]
                            predicted_response_id = nav.id
                            predicted_response = db.get_intent_name_by_chroma_id_db(
                                chroma_id=predicted_response_id, session=session
                            )
                            if predicted_response != expected_response:
                                status = "Failure"

                        elif predicted_intent == "summarization":
                            logger.info(f"[[Summarization]]")
                            chained = False
                            initial_state = {
                                "query": query,
                                "chained": chained,
                                "tool_calls": [],
                                "tool_response": "",
                                "summarized_response": "",
                                "is_moderated": False,
                                "final_response": "",
                            }
                            graph_result = await agent.summarization_graph.ainvoke(
                                initial_state
                            )
                            predicted_response = graph_result["final_response"]
                            is_moderated = graph_result["is_moderated"]
                            summarized = graph_result["summarized_response"]
                            if is_moderated:
                                status = "Failure"
                                summarization_analysis = "Flagged by content policy"
                                summarization_score = 0
                            elif directives:
                                score_response: schema.ScoreResponse = (
                                    score_chain.invoke(
                                        {
                                            "query": query,
                                            "summary": summarized,
                                            "directive": directives,
                                        }
                                    )
                                )
                                summarization_score = score_response.score
                                logger.info(f"Score: {score_response}")
                                if isinstance(summarization_score, float) and (
                                    math.isnan(summarization_score)
                                    or math.isinf(summarization_score)
                                ):
                                    summarization_score = None
                                    summarization_analysis = (
                                        "Invalid score returned by LLM"
                                    )
                                    status = "Failure"
                                else:
                                    summarization_analysis = score_response.analysis
                                    if summarization_score < 50:
                                        status = "Failure"
                            else:
                                summarization_analysis = "No directives provided"
                                summarization_score = None

                        elif predicted_intent == "task_execution":
                            logger.info(f"[[Task Execution]]")
                            # Parse directives for chained parameter
                            chained = False
                            # if directives.lower() in ["chained=true", "chained"]:
                            #     chained = True
                            # Execute task using WebSocket
                            thread_id = uuid4().hex
                            ws_url = f"ws://localhost:8000/api/task_execution/ws/task_execution/"
                            predicted_response = ""
                            requires_approval = False
                            try:
                                async with websockets.connect(ws_url) as websocket:
                                    # Send initial data
                                    initial_data = {
                                        "query": query,
                                        "chained": chained,
                                        "thread_id": thread_id,
                                    }
                                    await websocket.send(json.dumps(initial_data))
                                    while True:
                                        try:
                                            message = await asyncio.wait_for(
                                                websocket.recv(), timeout=300.0
                                            )
                                            event_data = json.loads(message)
                                            logger.debug(
                                                f"Received WebSocket event: {event_data}"
                                            )

                                            if event_data.get("error"):
                                                status = "Failure"
                                                summarization_analysis = event_data[
                                                    "error"
                                                ]
                                                await test_queue.put(
                                                    {
                                                        "id": str(index + 1),
                                                        "predicted_intent": predicted_intent,
                                                        "predicted_response": predicted_response,
                                                        "actual_response": expected_response,
                                                        "status": status,
                                                        "summarization_analysis": summarization_analysis,
                                                        "summarization_score": None,
                                                        "tat": f"{(time.time() - start_time):.1f} s",
                                                    }
                                                )
                                                break

                                            if event_data.get("interrupt"):
                                                # Simulate automatic approval for testing
                                                requires_approval = True
                                                approval_response = {
                                                    "thread_id": thread_id,
                                                    "resume": "true",
                                                }
                                                await websocket.send(
                                                    json.dumps(approval_response)
                                                )
                                                continue

                                            if event_data.get(
                                                "requires_approval"
                                            ) and event_data.get("actions_to_review"):
                                                requires_approval = True
                                                # Simulate automatic approval for testing
                                                approval_response = {
                                                    "thread_id": thread_id,
                                                    "resume": "true",
                                                }
                                                await websocket.send(
                                                    json.dumps(approval_response)
                                                )
                                                continue

                                            predicted_response = event_data.get(
                                                "response", ""
                                            )
                                            if event_data.get("is_final"):
                                                predicted_response = event_data[
                                                    "response"
                                                ]
                                                identified_actions = (
                                                    json.loads(predicted_response)
                                                    if predicted_response
                                                    else []
                                                )
                                                predicted_json = [
                                                    {
                                                        "name": item["tool"],
                                                        "args": {
                                                            key: value
                                                            for key, value in item[
                                                                "parameters"
                                                            ].items()
                                                            if value not in [None, ""]
                                                        },
                                                    }
                                                    for item in identified_actions
                                                ]
                                                predicted_response = json.dumps(
                                                    predicted_json
                                                )
                                                try:
                                                    expected_json = json.loads(
                                                        expected_response.replace(
                                                            "'", '"'
                                                        )
                                                    )
                                                    if json.dumps(
                                                        predicted_json, sort_keys=True
                                                    ) != json.dumps(
                                                        expected_json, sort_keys=True
                                                    ):
                                                        status = "Failure"
                                                except json.JSONDecodeError as e:
                                                    logger.error(
                                                        f"JSON decode error: {e}"
                                                    )
                                                    status = "Failure"
                                                    summarization_analysis = f"Invalid JSON in response: {str(e)}"
                                                break

                                        except asyncio.TimeoutError:
                                            status = "Failure"
                                            summarization_analysis = (
                                                "WebSocket operation timed out"
                                            )
                                            await test_queue.put(
                                                {
                                                    "id": str(index + 1),
                                                    "predicted_intent": predicted_intent,
                                                    "predicted_response": predicted_response,
                                                    "actual_response": expected_response,
                                                    "status": status,
                                                    "summarization_analysis": summarization_analysis,
                                                    "summarization_score": None,
                                                    "tat": f"{(time.time() - start_time):.1f} s",
                                                }
                                            )
                                            break

                                    tat = f"{(time.time() - start_time):.1f} s"
                                    summarization_analysis = (
                                        "Identified actions retrieved, approval required"
                                        if requires_approval
                                        else "Identified actions retrieved"
                                    )
                                    await test_queue.put(
                                        {
                                            "id": str(index + 1),
                                            "predicted_intent": predicted_intent,
                                            "predicted_response": predicted_response,
                                            "actual_response": expected_response,
                                            "status": status,
                                            "summarization_analysis": summarization_analysis,
                                            "summarization_score": None,
                                            "tat": tat,
                                        }
                                    )

                            except Exception as e:
                                logger.error(
                                    f"WebSocket error for row {index + 1}: {e}"
                                )
                                status = "Failure"
                                summarization_analysis = f"WebSocket error: {str(e)}"
                                await test_queue.put(
                                    {
                                        "id": str(index + 1),
                                        "predicted_intent": predicted_intent,
                                        "predicted_response": predicted_response,
                                        "actual_response": expected_response,
                                        "status": status,
                                        "summarization_analysis": summarization_analysis,
                                        "summarization_score": None,
                                        "tat": f"{(time.time() - start_time):.1f} s",
                                    }
                                )

                    except Exception as e:
                        logger.error(f"Error processing row {index + 1}: {e}")
                        await test_queue.put(
                            {"error": f"Error processing row {index + 1}: {str(e)}"}
                        )
                        continue

                tat = f"{(time.time() - start_time):.1f} s"

                if predicted_intent != "task_execution":
                    result = {
                        "id": str(index + 1),
                        "predicted_intent": predicted_intent,
                        "predicted_response": predicted_response,
                        "actual_response": expected_response,
                        "status": status,
                        "summarization_analysis": summarization_analysis,
                        "summarization_score": summarization_score,
                        "tat": tat,
                    }
                    await test_queue.put(result)
        except Exception as e:
            logger.error(f"Error in file processing: {e}")
            await test_queue.put({"error": f"Error in file processing: {str(e)}"})

    try:
        file_content = await file.read()
        background_tasks.add_task(process_file, file_content)
        return {"message": "Testing started"}
    except Exception as e:
        logger.error(f"Error initiating tests: {e}")
        raise HTTPException(status_code=400, detail=f"Error initiating tests: {str(e)}")
