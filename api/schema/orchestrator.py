from pydantic import BaseModel
from typing import Literal


class OrchestrationQuery(BaseModel):
    """
    Pydantic model for an orchestration query.

    Attributes:
        query (str): The user's query to be categorized.
    """

    query: str


class OrchestrationResponse(BaseModel):
    """
    Pydantic model for an orchestration response.

    Attributes:
        category (Literal): The identified category of the query.
    """

    category: Literal["navigation", "summarization", "task_execution"]

class InvokeAgentRequest(BaseModel):
    """
    Pydantic model for an Agent Invocation Request.

    Attributes:
        agent (str): The identified agent
        query (str): The query for the agent
    """
    agent: Literal["navigation", "summarization", "task_execution"]
    query: str