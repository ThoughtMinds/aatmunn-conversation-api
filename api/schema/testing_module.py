from pydantic import BaseModel


class ScoreResponse(BaseModel):
    analysis: str
    score: int
