from pydantic import BaseModel


class SummaryRequest(BaseModel):
    query: str
    
class SummaryResponse(BaseModel):
    summary: str
    content_moderated: bool
