from fastapi import APIRouter, Depends
from api import agent, db, schema
from typing import Annotated
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/identify_intent/", response_model=schema.OrchestrationResponse)
def identify_intent(session: SessionDep, data: schema.OrchestrationQuery) -> schema.OrchestrationResponse:
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
    response = agent.orchestrator_graph.invoke({"query": query})
    category = response["category"]
    response = schema.OrchestrationResponse(category=category)
    return response
