from fastapi import APIRouter, Depends
from api import db, schema, agent
from typing import Annotated
from sqlmodel import Session
from langchain_core.messages import HumanMessage
from api.core.logging_config import logger


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

# Support single, multiple API call operation (flag?)

@router.post("/execute_task/", response_model=schema.TaskResponse)
def execute_task(session: SessionDep, data: schema.TaskRequest) -> schema.TaskResponse:
    query = data.query
    logger.info(f"Task Execution Query: {query}")
    
    content = agent.execute_task(messages=[HumanMessage(content=query)])
    response = schema.TaskResponse(response=content, status=True)
    return response