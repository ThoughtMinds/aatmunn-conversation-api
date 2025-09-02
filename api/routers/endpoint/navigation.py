from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from api import agent, db, schema
import pandas as pd
from typing import Annotated
from sqlmodel import Session
from time import time
import json
from api.db.log import create_log_entry


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/get_navigation/", response_model=schema.NavigationAgentResponse)
async def get_navigation(
    intent: schema.NavigationQuery, session: SessionDep
) -> schema.NavigationAgentResponse:
    """
    Get navigation information for a given query.

    This endpoint takes a user's query, invokes the agent graph to determine the
    appropriate navigation, and enriches the response with the intent name from the database.

    Args:
        intent (schema.NavigationQuery): The user's query for navigation.
        session (SessionDep): The database session dependency.

    Returns:
        schema.NavigationAgentResponse: The navigation response, including the predicted intent.
    """
    query = intent.query
    print(f"Request: {query}")
    start_time = time()
    
    try:
        navigation: schema.Navigation = agent.get_navigation_response(query=query)
        print(f"Response: {navigation}")

        predicted_intent = db.get_intent_name_by_chroma_id_db(
            chroma_id=navigation.id, session=session
        )
        navigation_response = schema.NavigationAgentResponse(
            id=navigation.id, reasoning=navigation.reasoning, intent_name=predicted_intent
        )
        
        end_time = time()
        processing_time = end_time - start_time
        create_log_entry(
            session=session,
            intent_type="navigation",
            request_data=query,
            response_data=navigation_response.model_dump_json(),
            status="success",
            processing_time=processing_time,
        )
        return navigation_response
    except Exception as e:
        end_time = time()
        processing_time = end_time - start_time
        create_log_entry(
            session=session,
            intent_type="navigation",
            request_data=query,
            response_data=str(e),
            status="error",
            processing_time=processing_time,
        )
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test_navigation/")
async def upload_navigation_excel(
    session: SessionDep,
    file: UploadFile = File(...),
) -> StreamingResponse:
    """
    Test navigation intents by uploading an Excel file.

    This endpoint allows for batch testing of navigation intents. It accepts an
    Excel file containing 'Query' and 'Intent' columns. It processes each query,
    runs it through the navigation agent, and compares the predicted intent with
    the actual intent. The results are streamed back to the client.

    Args:
        session (SessionDep): The database session dependency.
        file (UploadFile): The Excel file containing test data.

    Returns:
        StreamingResponse: A stream of server-sent events with the test results.

    Raises:
        HTTPException: If the file is not a valid Excel file, is missing the
                       'Query' column, or if any other processing error occurs.
    """
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(
            status_code=400, detail="Only Excel files (.xlsx, .xls) are supported"
        )

    try:
        df = pd.read_excel(file.file)

        if "Query" not in df.columns:
            raise HTTPException(
                status_code=400, detail="Excel file must contain a 'Query' column"
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing Excel file: {str(e)}"
        )

    async def stream_generator():
        for _, row in df.iterrows():
            try:
                print(f"Testing Query #{_}")
                query, actual_intent = row["Query"], row.get("Intent")

                if not query or not isinstance(query, str):
                    continue

                start_time = time()
                navigation: schema.Navigation = agent.get_navigation_response(
                    query=query
                )
                end_time = time()

                elapsed_time = end_time - start_time
                elapsed_time = round(elapsed_time, 3)
                print(f"Time taken: {elapsed_time:.4f} seconds")

                chroma_id = navigation.id

                predicted_intent = db.get_intent_name_by_chroma_id_db(
                    chroma_id=chroma_id, session=session
                )

                result = schema.NavigationTestResult(
                    query=query,
                    actual_intent=actual_intent,
                    predicted_intent=predicted_intent,
                    response_time=elapsed_time,
                )

                print(f"Result: {result}")
                yield f"data: {result.model_dump_json()}\n\n"
            except Exception as e:
                error_result = {
                    "error": f"Failed to process row: {e}",
                    "query": query,
                }
                print(error_result)
                yield f"data: {json.dumps(error_result)}\n\n"

    return StreamingResponse(stream_generator(), media_type="text/event-stream")
