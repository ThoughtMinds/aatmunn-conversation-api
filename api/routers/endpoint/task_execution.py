from fastapi import APIRouter, Depends
from api import db, schema, agent
from typing import Annotated
from sqlmodel import Session
from api.core.logging_config import logger
from time import time
from api.db.log import create_log_entry


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/execute_task/", response_model=schema.TaskResponse)
async def execute_task(
    session: SessionDep, data: schema.TaskRequest
) -> schema.TaskResponse:
    """
    Execute a task for a given query.

    This endpoint takes a user's query and uses the task execution agent to
    perform an action. It supports both single and chained tool calls.

    Args:
        session (SessionDep): The database session dependency.
        data (schema.TaskRequest): The user's query and chaining preference.

    Returns:
        schema.TaskResponse: The result of the task execution.
    """
    query, chained = data.query, data.chained
    logger.info(f"Task Execution Query: {query}")

    start_time = time()
    try:
        task_response = await agent.get_task_execution_response(
            query=query, chained=chained
        )
        task_status = True
        status = "success"
    except Exception as e:
        logger.error(f"Failed to execute task due to: {e}")
        task_response = "Failed to execute task. Please rephrase or retry"
        task_status = False
        status = "error"

    end_time = time()
    elapsed_time = end_time - start_time
    elapsed_time = round(elapsed_time, 3)
    print(f"Time taken: {elapsed_time:.4f} seconds")
    response = schema.TaskResponse(
        response=task_response, status=task_status, processing_time=elapsed_time
    )

    create_log_entry(
        session=session,
        intent_type="task_execution",
        request_data=query,
        response_data=response.model_dump_json(),
        status=status,
        processing_time=elapsed_time,
    )
    return response
