from fastapi import APIRouter, Depends
from api import agent, db, schema
from typing import Annotated, Optional
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/identify_intent/", response_model=schema.OrchestrationResponse)
def identify_intent(
    session: SessionDep, data: schema.OrchestrationQuery
) -> schema.OrchestrationResponse:
    """
    Identify the intent of a user's query.

    This endpoint takes a user's query and uses the orchestrator agent to
    categorize it as 'navigation', 'summarization', or 'task_execution'.

    Args:
        session (SessionDep): The database session dependency.
        data (schema.OrchestrationQuery): The user's query.

    Returns:
        schema.OrchestrationResponse: The identified category of the query.
    """
    query = data.query
    response = agent.get_orchestrator_response(query=query)
    return response


@router.post("/invoke_agent")
def invoke_agent(session: SessionDep, data: schema.InvokeAgentRequest) -> Optional[str]:
    agent_name = data.agent
    query = data.query
    match agent_name:
        case "navigation":
            agent_to_use = agent.get_navigation_response
        case "summarization":
            agent_to_use = agent.get_summarized_response
        case "task_execution":
            agent_to_use = agent.get_task_execution_response
