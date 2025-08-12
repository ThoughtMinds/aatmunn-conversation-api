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
    query = data.query
    logger.info(f"Summarization Query: {query}")
    content = agent.get_summarized_response(query=query)

    response = schema.SummaryResponse(summary=content, content_moderated=False)
    return response
