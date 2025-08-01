from fastapi import APIRouter, Depends
from api import db, schema
from typing import Annotated, List
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/get_summary/", response_model=schema.SummaryResponse)
def get_summary(session: SessionDep, data: schema.SummaryRequest) -> schema.SummaryResponse:
    query = data.query
    # get summary (make api call, db fetch and summarize with LLM)
    summary = "This is a summary"
    # apply content moderation on summary
    response = schema.SummaryResponse(summary=summary, content_moderated=False)
    # Support single, multiple API call operation (flag?)
    return response