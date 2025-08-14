from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from typing_extensions import TypedDict
from typing import Any

class SummarizationCreate(BaseModel):
    """
    Pydantic model for requesting a data summarization.

    Attributes:
        table (str): The primary table to summarize (e.g., 'Employee', 'Department', 'Project').
        group_by (Optional[str]): The field to group by (e.g., 'department_id', 'role_id').
        filters (Optional[Dict[str, str]]): Key-value pairs for filtering data (e.g., {'status': 'active'}).
        metrics (List[str]): List of metrics to compute (e.g., ['count', 'avg_rating']).
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.
    """
    table: str
    group_by: Optional[str] = None
    filters: Optional[Dict[str, str]] = None
    metrics: List[str]
    limit: Optional[int] = None
    offset: Optional[int] = 0
    
class SummaryRequest(BaseModel):
    query: str
    
class SummaryResponse(BaseModel):
    summary: Any#str
    content_moderated: bool


from typing import Any
class SummarizationState(TypedDict):
    messages: List[dict]
    session: Any #Session
    summary: str