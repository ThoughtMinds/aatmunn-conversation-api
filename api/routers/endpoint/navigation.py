from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from api import agent, db, schema
import pandas as pd
from typing import Annotated, List
from sqlmodel import Session
from time import time


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/get_navigation/", response_model=schema.NavigationResponse)
def get_navigation(
    intent: schema.NavigationQuery, session: SessionDep
) -> schema.Navigation:
    """
    Get navigation information for a given query.

    This endpoint takes a user's query, invokes the agent graph to determine the
    appropriate navigation, and enriches the response with the intent name from the database.

    Args:
        intent (schema.NavigationQuery): The user's query for navigation.
        session (SessionDep): The database session dependency.

    Returns:
        schema.NavigationResponse: The navigation response, including the predicted intent.
    """
    query = intent.query
    print(f"Request: {query}")
    response = agent.navigation_graph.invoke({"query": query})
    print(f"Response: {response}")
    navigation: schema.Navigation = response["navigation"]

    predicted_intent = db.get_intent_name_by_chroma_id_db(
        chroma_id=navigation.id, session=session
    )
    navigation_response = schema.NavigationResponse(
        id=navigation.id, reasoning=navigation.reasoning, intent_name=predicted_intent
    )
    return navigation_response


@router.post("/test_navigation/", response_model=List[schema.NavigationTestResult])
async def upload_navigation_excel(
    session: SessionDep,
    file: UploadFile = File(...),
) -> List[schema.NavigationTestResult]:
    """
    Test navigation intents by uploading an Excel file.

    This endpoint allows for batch testing of navigation intents. It accepts an
    Excel file containing 'Query' and 'Intent' columns. It processes each query,
    runs it through the navigation agent, and compares the predicted intent with
    the actual intent.

    Args:
        session (SessionDep): The database session dependency.
        file (UploadFile): The Excel file containing test data.

    Returns:
        List[schema.NavigationTestResult]: A list of test results, including the query,
                                           actual intent, predicted intent, and response time.

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

        navigation_results = []

        for _, row in df.iterrows():
            try:
                print(f"Testing Query #{_}")
                query, actual_intent = row["Query"], row["Intent"]

                if not query or not isinstance(query, str):
                    continue

                start_time = time()
                response = agent.navigation_graph.invoke({"query": query})
                end_time = time()

                elapsed_time = end_time - start_time
                elapsed_time = round(elapsed_time, 3)
                print(f"Time taken: {elapsed_time:.4f} seconds")

                navigation: schema.Navigation = response["navigation"]
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
                navigation_results.append(result)
                # Measure accuracy, add score
            except Exception as e:
                print(f"Failed to process test due to: {e}")

        if not navigation_results:
            raise HTTPException(
                status_code=400, detail="No valid queries found in the Excel file"
            )

        return navigation_results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing Excel file: {str(e)}"
        )
