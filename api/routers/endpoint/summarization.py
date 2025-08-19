from fastapi import APIRouter, Depends
from api import db, agent, schema
from typing import Annotated
from sqlmodel import Session
from api.core.logging_config import logger


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

# Support single, multiple API   call operation (flag?)


@router.post("/get_summary/", response_model=schema.SummaryResponse)
def get_summary(
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
    summary, moderated = agent.get_summarized_response(query=query, chained=chained)

    response = schema.SummaryResponse(summary=summary, content_moderated=moderated)
    return response
