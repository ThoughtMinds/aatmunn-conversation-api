from fastapi import APIRouter, Depends
from api import db, agent, schema
from typing import Annotated
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]

# Support single, multiple API   call operation (flag?)

@router.post("/get_summary/", response_model=schema.SummaryResponse)
def get_summary(session: SessionDep, data: schema.SummaryRequest) -> schema.SummaryResponse:
    query = data.query
    # get summary (make api call, db fetch and summarize with LLM)

    ####
    initial_state = {
        "messages": [],
        "query": query,
        "table_names": "",
        "schema": "",
        "checked_query": "",
        "query_result": "",
        "summary": ""
    }
    
    result = agent.summarization_graph.invoke(initial_state)
    
    if "summary" in result:
        content = result["summary"]
    else:
        content = ""
  
    response = schema.SummaryResponse(summary=content, content_moderated=False)
    return response