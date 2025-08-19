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
