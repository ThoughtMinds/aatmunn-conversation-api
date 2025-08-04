from sqlmodel import Field, SQLModel
from typing import Optional
from datetime import date, time

class Department(SQLModel, table=True):
    """
    Represents a department in the organization.
    """
    department_id: Optional[int] = Field(default=None, primary_key=True)
    department_name: str = Field(index=True, unique=True)
    location: Optional[str] = Field(default=None)
    manager_id: Optional[int] = Field(default=None, foreign_key="employee.employee_id")

class Employee(SQLModel, table=True):
    """
    Represents an employee in the organization.
    """
    employee_id: Optional[int] = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str = Field(unique=True)
    hire_date: date
    department_id: int = Field(foreign_key="department.department_id")
    role_id: int = Field(foreign_key="role.role_id")
    status: str = Field(default="active")  # active, inactive, terminated

    class Config:
        table_args = {"sqlite_autoincrement": True}

class Role(SQLModel, table=True):
    """
    Represents a job role in the organization.
    """
    role_id: Optional[int] = Field(default=None, primary_key=True)
    role_name: str = Field(index=True, unique=True)
    description: Optional[str] = Field(default=None)
    salary_grade: str

    class Config:
        table_args = {"sqlite_autoincrement": True}

class Shift(SQLModel, table=True):
    """
    Represents a work shift schedule.
    """
    shift_id: Optional[int] = Field(default=None, primary_key=True)
    shift_name: str = Field(index=True)
    start_time: time
    end_time: time
    department_id: int = Field(foreign_key="department.department_id")

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["department_id", "shift_name"]},
        )

class EmployeeShift(SQLModel, table=True):
    """
    Represents the assignment of employees to shifts.
    """
    employee_shift_id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.employee_id")
    shift_id: int = Field(foreign_key="shift.shift_id")
    start_date: date
    end_date: Optional[date] = Field(default=None)

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["employee_id", "shift_id", "start_date"]},
        )

class Project(SQLModel, table=True):
    """
    Represents a project in the organization.
    """
    project_id: Optional[int] = Field(default=None, primary_key=True)
    project_name: str = Field(index=True, unique=True)
    department_id: int = Field(foreign_key="department.department_id")
    start_date: date
    end_date: Optional[date] = Field(default=None)
    status: str = Field(default="active")  # active, completed, cancelled

    class Config:
        table_args = {"sqlite_autoincrement": True}

class EmployeeProject(SQLModel, table=True):
    """
    Represents the assignment of employees to projects.
    """
    employee_project_id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.employee_id")
    project_id: int = Field(foreign_key="project.project_id")
    role_in_project: str
    assignment_date: date

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["employee_id", "project_id"]},
        )

class Skill(SQLModel, table=True):
    """
    Represents a skill that employees can have.
    """
    skill_id: Optional[int] = Field(default=None, primary_key=True)
    skill_name: str = Field(index=True, unique=True)
    category: str

    class Config:
        table_args = {"sqlite_autoincrement": True}

class EmployeeSkill(SQLModel, table=True):
    """
    Represents the skills possessed by an employee.
    """
    employee_skill_id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.employee_id")
    skill_id: int = Field(foreign_key="skill.skill_id")
    proficiency_level: str  # beginner, intermediate, expert
    acquired_date: date

    class Config:
        table_args = (
            {"sqlite_autoincrement": True},
            {"unique": ["employee_id", "skill_id"]},
        )

class PerformanceReview(SQLModel, table=True):
    """
    Represents an employee's performance review.
    """
    review_id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employee.employee_id")
    reviewer_id: int = Field(foreign_key="employee.employee_id")
    review_date: date
    rating: int  # 1-5 scale
    comments: Optional[str] = Field(default=None)

    class Config:
        table_args = {"sqlite_autoincrement": True}