from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Dict, List, Literal, Optional


class ApprovalRequest(BaseModel):
    thread_id: str
    approved: bool


class TaskRequest(BaseModel):
    query: str
    chained: bool = False
    thread_id: Optional[str] = None
    resume_action: Optional[Literal["approve", "reject"]] = None


class TaskResponse(BaseModel):
    response: str
    status: bool
    processing_time: float
    thread_id: Optional[str] = None
    requires_approval: bool = False
    actions_to_review: Optional[List[Dict]] = None


class ActionReviewItem(BaseModel):
    tool: str
    parameters: Dict
    description: str


class ApprovalDialogData(BaseModel):
    question: str
    actions: List[ActionReviewItem]
    query: str
    thread_id: str


class EmployeeCreate(BaseModel):
    """
    Pydantic model for creating a new employee record.

    Attributes:
        first_name (str): Employee's first name.
        last_name (str): Employee's last name.
        email (EmailStr): Employee's email address.
        hire_date (date): Employee's hire date.
        department_id (int): ID of the employee's department.
        role_id (int): ID of the employee's role.
        status (str): Employee status (default: 'active').
    """

    first_name: str
    last_name: str
    email: EmailStr
    hire_date: date
    department_id: int
    role_id: int
    status: str = "active"
