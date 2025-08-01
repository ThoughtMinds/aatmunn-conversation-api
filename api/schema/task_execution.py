from pydantic import BaseModel


class TaskRequest(BaseModel):
    query: str
    
class TaskResponse(BaseModel):
    response: str
    status: bool
