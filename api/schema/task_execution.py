from pydantic import BaseModel, EmailStr
from datetime import date

class TaskRequest(BaseModel):
    query: str
    chained: bool = False
    
class TaskResponse(BaseModel):
    response: str
    status: bool

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