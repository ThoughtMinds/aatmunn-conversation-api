from pydantic import BaseModel
from typing import Dict, List, Optional


class IntentCreate(BaseModel):
    """
    Pydantic model for creating a new intent.

    Attributes:
        chroma_id (Optional[str]): The Chroma ID of the intent (optional).
        intent (str): The name of the intent.
        description (str): A description of the intent.
        parameters (Dict[str, str]): A dictionary of parameters for the intent.
        required (List[str]): A list of required parameters.
        responses (Dict[str, str]): A dictionary of responses for the intent.
    """
    chroma_id: Optional[str] = None  # Not needed when creating intent
    intent: str
    description: str
    parameters: Dict[str, str]
    required: List[str]
    responses: Dict[str, str]


class IntentResponse(BaseModel):
    """
    Pydantic model for the response when an intent is retrieved.

    Attributes:
        intent_id (int): The ID of the intent.
        intent (str): The name of the intent.
        description (str): A description of the intent.
        parameters (Dict[str, str]): A dictionary of parameters for the intent.
        required (List[str]): A list of required parameters.
        responses (Dict[str, str]): A dictionary of responses for the intent.
    """
    intent_id: int
    intent: str
    description: str
    parameters: Dict[str, str]
    required: List[str]
    responses: Dict[str, str]


class NavigationQuery(BaseModel):
    """
    Pydantic model for a navigation query.

    Attributes:
        query (str): The user's query for navigation.
        source (Optional[str]): The source of the query (optional).
    """
    query: str
    source: Optional[str] = None


class NavigationTestResult(BaseModel):
    """
    Pydantic model for the result of a navigation test.

    Attributes:
        query (str): The query that was tested.
        actual_intent (str): The expected intent.
        predicted_intent (str): The intent predicted by the model.
        response_time (float): The time taken to get the response.
    """
    query: str
    actual_intent: str
    predicted_intent: str
    response_time: float
