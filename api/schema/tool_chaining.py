from pydantic import BaseModel


class ChainedToolCall(BaseModel):
    """
    Pydantic model for a chained tool call.

    Attributes:
        name (str): The name of the tool to be called.
        parameters (dict): The parameters to be passed to the tool.
    """

    name: str
    parameters: dict
