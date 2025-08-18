from pydantic import BaseModel


class ChainedToolCall(BaseModel):
    name: str
    parameters: dict
