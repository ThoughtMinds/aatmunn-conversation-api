from fastapi import APIRouter, Depends
from api import db, agent, schema
from typing import Annotated
from sqlmodel import Session
from api.core.logging_config import logger
from time import time


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/get_summary/", response_model=schema.SummaryResponse)
async def get_summary(
    session: SessionDep, data: schema.SummaryRequest
) -> schema.SummaryResponse:
    """
    Get a summary for a given query.

    This endpoint takes a user's query and uses the summarization agent to
    generate a summary. It supports both single and chained tool calls.

    Args:
        session (SessionDep): The database session dependency.
        data (schema.SummaryRequest): The user's query and chaining preference.

    Returns:
        schema.SummaryResponse: The generated summary and content moderation status.
    """
    query, chained = data.query, data.chained
    logger.info(f"Summarization Query: {query}")

    start_time = time()
    try:
        summary, moderated = await agent.get_summarized_response(query=query, chained=chained)
    except Exception as e:
        logger.error(f"Failed to generate summary due to: {e}")
        summary = "Failed to generate summary. Please rephrase or retry"
        moderated = False
    finally:
        end_time = time()
        elapsed_time = end_time - start_time
        elapsed_time = round(elapsed_time, 3)
        print(f"Time taken: {elapsed_time:.4f} seconds")

        response = schema.SummaryResponse(
            summary=summary, content_moderated=moderated, processing_time=elapsed_time
        )
        return response
