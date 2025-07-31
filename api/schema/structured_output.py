from pydantic import BaseModel, field_validator
from typing import Union


class Navigation(BaseModel):
    """
    Pydantic model for the structured output of the navigation model.

    Attributes:
        id (Union[str, int]): The ID of the predicted intent.
        reasoning (str): The reasoning behind the prediction.
    """
    id: Union[str, int]
    reasoning: str


class NavigationResponse(BaseModel):
    """
    Pydantic model for the navigation response API endpoint.

    Attributes:
        id (str): The Chroma ID of the predicted intent.
        reasoning (str): The reasoning behind the prediction.
        intent_name (str): The name of the predicted intent.
    """
    id: str
    reasoning: str
    intent_name: str
