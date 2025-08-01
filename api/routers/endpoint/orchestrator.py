from fastapi import APIRouter, Depends
from api import agent, db, schema
from typing import Annotated
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.post("/identify_intent/")#, response_model=schema.OrchestrationResponse)
def identify_intent(session: SessionDep, data: schema.OrchestrationQuery) :#-> schema.OrchestrationResponse:
    query = data.query
    response = agent.orchestrator_graph.invoke({"query": query})
    category = response["category"]
    print(f"Category: {category}")
    # response = schema.OrchestrationResponse(category=intent)
    # return response
    return category
