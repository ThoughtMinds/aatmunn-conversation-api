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

# Assume in llm.py, there is a prompt for task="score_summary" that uses the query, directives, and summary to generate analysis and score.

# Global queue for streaming
test_queue = asyncio.Queue()
SessionDep = Annotated[Session, Depends(db.get_session)]

router = APIRouter()

chat_model = llm.get_ollama_chat_model()
score_chain = llm.create_chain_for_task(
    task="summary score", llm=chat_model, output_schema=schema.ScoreResponse
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
                # directives = row.get("Directives", "")
                # TODO: Add directives
                directives = "SCORE THIS SUMMARY"

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

                            chained = False  # TODO: Accept input

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
                                            # "directives": directives,
                                            "summary": summarized,
                                        }
                                    )
                                )
                                summarization_score = score_response.score
                                logger.info(f"Score: {score_response}")
                                # Sanitize summarization_score
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

                            # TODO: Task Execution use graph
                            # elif predicted_intent == "task_execution":
                            #     logger.info(f"[[Task Execution]]")

                            #     graph_result = await agent.get_task_execution_response(
                            #         query=query, chained=True
                            #     )
                            #     tool_calls = graph_result.get("tool_calls", [])
                            #     predicted_response = json.dumps(tool_calls)
                            #     if predicted_response != expected_response:
                            #         status = "Failure"

                    except Exception as e:
                        logger.error(f"Error processing row {index + 1}: {e}")
                        await test_queue.put(
                            {"error": f"Error processing row {index + 1}: {str(e)}"}
                        )
                        continue

                tat = f"{(time.time() - start_time):.1f} s"

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
