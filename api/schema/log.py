from pydantic import BaseModel
from typing import Dict, Literal


class RequestData(BaseModel):
    """
    Pydantic model for the input and output data of a request.

    Attributes:
        input (str): The input data of the request.
        output (str): The output data of the request.
    """

    input: str
    output: str


class AuditLog(BaseModel):
    """
    Pydantic model for an audit log entry.

    Attributes:
        intent_type (Literal): The type of intent (navigation, summarization, or task-execution).
        data (RequestData): The input and output data of the request.
        status (Literal): The status of the request (success or error).
    """

    intent_type: Literal["navigation", "summarization", "task-execution"]
    data: RequestData
    status: Literal["success", "error"]
