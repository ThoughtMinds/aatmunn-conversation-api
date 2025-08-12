from fastapi import APIRouter, Depends
from api import db, agent, schema
from typing import Annotated
from sqlmodel import Session
from langchain_core.messages import HumanMessage

router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

# Support single, multiple API   call operation (flag?)


@router.post("/get_summary/", response_model=schema.SummaryResponse)
def get_summary(
    session: SessionDep, data: schema.SummaryRequest
) -> schema.SummaryResponse:
    query = data.query

    content = agent.get_summarized_response(messages=[HumanMessage(content=query)])

    response = schema.SummaryResponse(summary=content, content_moderated=False)
    return response
