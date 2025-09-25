from pydantic import BaseModel, Field
from typing import Dict


class ChainedToolCall(BaseModel):
    name: str = Field(default="", description="Name of the tool to be used")
    parameters: Dict = Field(default={}, description="Parameters for the tool")
