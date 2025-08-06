from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from sqlmodel import Session, select
from sqlalchemy.sql import func, extract
from datetime import date, time
from api import db
from pydantic import BaseModel
from sqlalchemy import inspect
from langchain_core.tools import tool


# Make your logic (with tool calls)
# List table, Get table schema, Get query, Run Query, Summarize/Error
def get_db_schema(session) -> Dict:
    """
    Generate a JSON-compatible schema description of the database tables.

    Args:
        session: The database session for inspecting the database.

    Returns:
        Dict: A dictionary containing the schema description of all tables, including fields,
              data types, constraints, and relationships.

    Raises:
        Exception: If there is an error accessing the database metadata.
    """
    schema = {"tables": {}}

    # Define the table models
    table_models = {
        "Department": db.Department,
        "Employee": db.Employee,
        "Role": db.Role,
        "Shift": db.Shift,
        "EmployeeShift": db.EmployeeShift,
        "Project": db.Project,
        "EmployeeProject": db.EmployeeProject,
        "Skill": db.Skill,
        "EmployeeSkill": db.EmployeeSkill,
        "PerformanceReview": db.PerformanceReview,
    }

    # Get the SQLAlchemy inspector from the session
    inspector = inspect(session.get_bind())

    for table_name, model in table_models.items():
        table_schema = {
            "fields": [],
            "primary_key": [],
            "foreign_keys": [],
            "unique_constraints": [],
            "indexes": [],
        }

        # Get fields from SQLModel
        for field_name, field in model.__fields__.items():
            field_info = {
                "name": field_name,
                "type": str(field.outer_type_)
                .replace("typing.", "")
                .replace("NoneType", "Optional"),
                "nullable": field.allow_none,
                "default": str(field.default) if field.default is not None else None,
            }
            table_schema["fields"].append(field_info)

        # Primary keys
        table_schema["primary_key"] = inspector.get_pk_constraint(table_name.lower())[
            "constrained_columns"
        ]

        # Foreign keys
        for fk in inspector.get_foreign_keys(table_name.lower()):
            table_schema["foreign_keys"].append(
                {
                    "columns": fk["constrained_columns"],
                    "referenced_table": fk["referred_table"],
                    "referenced_columns": fk["referred_columns"],
                }
            )

        # Unique constraints
        for unique in inspector.get_unique_constraints(table_name.lower()):
            table_schema["unique_constraints"].append(unique["column_names"])

        # Indexes
        for index in inspector.get_indexes(table_name.lower()):
            table_schema["indexes"].append(
                {
                    "name": index["name"],
                    "columns": index["column_names"],
                    "unique": index["unique"],
                }
            )

        schema["tables"][table_name] = table_schema

    return schema


class SummarizationRequest(BaseModel):
    """
    Pydantic model for requesting a data summarization or fetch.

    Attributes:
        table (str): The primary table to query (e.g., 'Employee', 'Department').
        group_by (Optional[str]): The field to group by (e.g., 'department_id').
        filters (Optional[Dict[str, str]]): Key-value pairs for filtering data.
        metrics (Optional[List[str]]): Metrics to compute (e.g., ['count', 'avg_rating']).
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.
    """

    table: str
    group_by: Optional[str] = None
    filters: Optional[Dict[str, str]] = None
    metrics: Optional[List[str]] = None
    limit: Optional[int] = None
    offset: Optional[int] = 0


class SummarizationResponse(BaseModel):
    """
    Pydantic model for summarization results.

    Attributes:
        results (List[Dict]): List of summarized or fetched data.
        total (int): Total number of records or groups.
    """

    results: List[Dict]
    total: int


def populate_db_from_json(json_data: Dict, session: Session) -> Dict[str, int]:
    """
    Populate the database with mock data from JSON, respecting foreign key dependencies,
    only if the target table is empty.

    Args:
        json_data (Dict): The JSON data containing table entries.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, int]: A dictionary with table names and the number of records inserted
                       (0 if the table was not empty).

    Raises:
        HTTPException: If there is a database error (e.g., constraint violation).
    """
    table_map = {
        "Department": db.Department,
        "Role": db.Role,
        "Skill": db.Skill,
        "Employee": db.Employee,
        "Shift": db.Shift,
        "Project": db.Project,
        "EmployeeShift": db.EmployeeShift,
        "EmployeeProject": db.EmployeeProject,
        "EmployeeSkill": db.EmployeeSkill,
        "PerformanceReview": db.PerformanceReview,
    }

    # Define insertion order to respect foreign key constraints
    insertion_order = [
        "Department",
        "Role",
        "Skill",
        "Employee",
        "Shift",
        "Project",
        "EmployeeShift",
        "EmployeeProject",
        "EmployeeSkill",
        "PerformanceReview",
    ]

    inserted_counts = {}

    for table_name in insertion_order:
        if table_name not in json_data:
            inserted_counts[table_name] = 0
            continue

        model = table_map[table_name]
        # Check if the table is empty
        count_query = select(func.count()).select_from(model)
        existing_records = session.exec(count_query).one()

        if existing_records > 0:
            # inserted_counts[table_name] = 0
            continue

        records = json_data[table_name]
        count = 0

        for record in records:
            # Convert date and time strings to appropriate types
            for key, value in record.items():
                if isinstance(value, str) and key.endswith("_date"):
                    record[key] = date.fromisoformat(value)
                if isinstance(value, str) and (
                    key == "start_time" or key == "end_time"
                ):
                    record[key] = time.fromisoformat(value)

            db_record = model(**record)
            session.add(db_record)
            count += 1

        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise HTTPException(
                status_code=400, detail=f"Error populating {table_name}: {str(e)}"
            )

        inserted_counts[table_name] = count

    return inserted_counts


@tool
def fetch_employee_by_id_db(session: Any, employee_id: int) -> Dict[str, Any]:
    """
    Fetch an employee by ID, including related department and role data.

    Args:
        employee_id (int): The ID of the employee to fetch.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Employee details with department and role information.

    Raises:
        HTTPException: If the employee is not found (404).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "status": employee.status,
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
    }


def list_employees_by_skill_level_db(
    skill_level: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees with a specific skill proficiency level, including their department.

    Args:
        skill_level (str): The proficiency level to filter by (e.g., 'expert', 'intermediate').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees with the specified skill level and total count.

    Raises:
        HTTPException: If no employees are found (404) or invalid skill level (400).
    """
    valid_levels = ["beginner", "intermediate", "expert"]
    if skill_level not in valid_levels:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid skill level. Must be one of {valid_levels}",
        )

    query = (
        select(db.Employee, db.Department.department_name)
        .join(db.EmployeeSkill, db.EmployeeSkill.employee_id == db.Employee.employee_id)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .where(db.EmployeeSkill.proficiency_level == skill_level)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found with the specified skill level"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "skill_level": skill_level,
        }
        for employee, department_name in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.EmployeeSkill)
        .where(db.EmployeeSkill.proficiency_level == skill_level)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_performance_rating_db(
    rating: int,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees with a specific performance rating, including their department and role.

    Args:
        rating (int): The performance rating to filter by (1-5).
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees with the specified rating and total count.

    Raises:
        HTTPException: If no employees are found (404) or invalid rating (400).
    """
    if not 1 <= rating <= 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")

    query = (
        select(db.Employee, db.Department.department_name, db.Role.role_name)
        .join(
            db.PerformanceReview,
            db.PerformanceReview.employee_id == db.Employee.employee_id,
        )
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .join(db.Role, db.Role.role_id == db.Employee.role_id)
        .where(db.PerformanceReview.rating == rating)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found with the specified rating"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "role": role_name,
            "rating": rating,
        }
        for employee, department_name, role_name in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.PerformanceReview)
        .where(db.PerformanceReview.rating == rating)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_skill_db(
    skill_name: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees with a specific skill, including their department and skill proficiency.

    Args:
        skill_name (str): The skill name to filter by (e.g., 'Python').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees with the specified skill and total count.

    Raises:
        HTTPException: If no employees are found (404).
    """
    query = (
        select(
            db.Employee,
            db.Department.department_name,
            db.EmployeeSkill.proficiency_level,
        )
        .join(db.EmployeeSkill, db.EmployeeSkill.employee_id == db.Employee.employee_id)
        .join(db.Skill, db.Skill.skill_id == db.EmployeeSkill.skill_id)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .where(db.Skill.skill_name == skill_name)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found with the specified skill"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "skill_name": skill_name,
            "proficiency_level": proficiency_level,
        }
        for employee, department_name, proficiency_level in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.EmployeeSkill)
        .join(db.Skill)
        .where(db.Skill.skill_name == skill_name)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_department_db(
    department_name: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees in a specific department, including their roles.

    Args:
        department_name (str): The department name to filter by (e.g., 'Engineering').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees in the specified department and total count.

    Raises:
        HTTPException: If no employees are found (404).
    """
    query = (
        select(db.Employee, db.Department.department_name, db.Role.role_name)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .join(db.Role, db.Role.role_id == db.Employee.role_id)
        .where(db.Department.department_name == department_name)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found in the specified department"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "role": role_name,
        }
        for employee, department_name, role_name in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.Department)
        .where(db.Department.department_name == department_name)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_project_db(
    project_name: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees assigned to a specific project, including their role in the project and department.

    Args:
        project_name (str): The project name to filter by (e.g., 'Product Launch').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees assigned to the project and total count.

    Raises:
        HTTPException: If no employees are found (404).
    """
    query = (
        select(
            db.Employee,
            db.Department.department_name,
            db.EmployeeProject.role_in_project,
        )
        .join(
            db.EmployeeProject,
            db.EmployeeProject.employee_id == db.Employee.employee_id,
        )
        .join(db.Project, db.Project.project_id == db.EmployeeProject.project_id)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .where(db.Project.project_name == project_name)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found for the specified project"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "project_name": project_name,
            "role_in_project": role_in_project,
        }
        for employee, department_name, role_in_project in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.EmployeeProject)
        .join(db.Project)
        .where(db.Project.project_name == project_name)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_shift_db(
    shift_name: str,
    session: Session,
    limit: Optional[int] = None,
    offset: Optional[int] = 0,
) -> SummarizationResponse:
    """
    List employees assigned to a specific shift, including their department.

    Args:
        shift_name (str): The shift name to filter by (e.g., 'Morning').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees assigned to the shift and total count.

    Raises:
        HTTPException: If no employees are found (404).
    """
    query = (
        select(db.Employee, db.Department.department_name, db.Shift.shift_name)
        .join(db.EmployeeShift, db.EmployeeShift.employee_id == db.Employee.employee_id)
        .join(db.Shift, db.Shift.shift_id == db.EmployeeShift.shift_id)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .where(db.Shift.shift_name == shift_name)
        .where(db.EmployeeShift.end_date.is_(None))
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found for the specified shift"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "shift_name": shift_name,
        }
        for employee, department_name, shift_name in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .join(db.EmployeeShift)
        .join(db.Shift)
        .where(db.Shift.shift_name == shift_name)
        .where(db.EmployeeShift.end_date.is_(None))
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)


def list_employees_by_hire_year_db(
    year: int, session: Session, limit: Optional[int] = None, offset: Optional[int] = 0
) -> SummarizationResponse:
    """
    List employees hired in a specific year, including their department and role.

    Args:
        year (int): The hire year to filter by (e.g., 2023).
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.
        offset (Optional[int]): Number of records to skip for pagination.

    Returns:
        SummarizationResponse: List of employees hired in the specified year and total count.

    Raises:
        HTTPException: If no employees are found (404) or invalid year (400).
    """
    if year < 1900 or year > 2025:
        raise HTTPException(
            status_code=400, detail="Invalid year. Must be between 1900 and 2025"
        )

    query = (
        select(db.Employee, db.Department.department_name, db.Role.role_name)
        .join(db.Department, db.Department.department_id == db.Employee.department_id)
        .join(db.Role, db.Role.role_id == db.Employee.role_id)
        .where(extract("year", db.Employee.hire_date) == year)
    )

    if limit:
        query = query.limit(limit)
    query = query.offset(offset)

    results = session.exec(query).all()
    if not results:
        raise HTTPException(
            status_code=404, detail="No employees found for the specified hire year"
        )

    formatted_results = [
        {
            "employee_id": employee.employee_id,
            "name": f"{employee.first_name} {employee.last_name}",
            "email": employee.email,
            "department": department_name,
            "role": role_name,
            "hire_year": year,
        }
        for employee, department_name, role_name in results
    ]

    total_query = select(func.count()).select_from(
        select(db.Employee.employee_id)
        .where(extract("year", db.Employee.hire_date) == year)
        .subquery()
    )
    total = session.exec(total_query).one()

    return SummarizationResponse(results=formatted_results, total=total)
