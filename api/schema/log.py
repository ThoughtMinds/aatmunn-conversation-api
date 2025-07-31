from pydantic import BaseModel
from typing import Dict, Literal

class RequestData(BaseModel):
    input: str
    output: str

class AuditLog(BaseModel):
    intent_type: Literal["navigation", "summarization", "task-execution"]
    data: RequestData
    status: Literal["success", "error"]