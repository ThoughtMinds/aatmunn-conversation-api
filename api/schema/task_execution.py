from pydantic import BaseModel, EmailStr
from datetime import date


class TaskRequest(BaseModel):
    """
    Pydantic model for a task execution request.

    Attributes:
        query (str): The user's query for task execution.
        chained (bool): Whether to use chained tool calls.
    """

    query: str
    chained: bool = False


class TaskResponse(BaseModel):
    """
    Pydantic model for a task execution response.

    Attributes:
        response (str): The response from the task execution.
        status (bool): The status of the task execution.
    """

    response: str
    status: bool
    processing_time: float


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
