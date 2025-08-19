from fastapi import APIRouter, Depends
from api import db, schema, agent
from typing import Annotated
from sqlmodel import Session
from api.core.logging_config import logger


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

# Support single, multiple API call operation (flag?)


@router.post("/execute_task/", response_model=schema.TaskResponse)
def execute_task(
    session: SessionDep, data: schema.TaskRequest
) -> schema.TaskResponse:
    query, chained = data.query, data.chained
    logger.info(f"Task Execution Query: {query}")

    content = agent.get_task_execution_response(query=query, chained=chained)
    response = schema.TaskResponse(response=content, status=True)
    return response
