from fastapi import APIRouter, Depends
from api import db, schema
from typing import Annotated, List
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/execute_task/", response_model=schema.TaskResponse)
def execute_task(session: SessionDep, data: schema.TaskRequest) -> schema.TaskResponse:
    query = data.query
    # Execute task, ask for follow up information
    response = "This is a response"
    # apply content moderation on summary
    response = schema.TaskResponse(response=response, status=True)
    # Support single, multiple API call operation (flag?)
    return response