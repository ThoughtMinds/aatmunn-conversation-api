from pydantic import BaseModel
from typing import Literal


class OrchestrationQuery(BaseModel):
    query: str
    
class OrchestrationResponse(BaseModel):
    category: Literal["navigation", "summarization", "task_execution"]