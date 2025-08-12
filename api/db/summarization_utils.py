from typing import Dict, Any, Optional, List
from fastapi import HTTPException
from sqlmodel import Session, select
from datetime import date, time
from langchain_core.tools import tool
from api import db, schema
from sqlalchemy.sql import func, extract
from pydantic import EmailStr


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
def add_employee_db(employee_data: Dict[str, Any], session: Any) -> Dict[str, Any]:
    """
    Add a new employee to the database, ensuring department and role exist.

    Args:
        employee_data (Dict[str, Any]): Dictionary containing employee details (first_name, last_name, email, hire_date, department_id, role_id, status).
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Details of the newly created employee.

    Raises:
        HTTPException: If department or role doesn't exist (400), or if email is already in use (400), or other database errors (400).
    """
    try:
        employee_input = schema.EmployeeCreate(**employee_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid input data: {str(e)}")

    # Check if department exists
    department = session.get(db.Department, employee_input.department_id)
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    # Check if role exists
    role = session.get(db.Role, employee_input.role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    # Check if email is unique
    existing_employee = session.exec(
        select(db.Employee).where(db.Employee.email == employee_input.email)
    ).first()
    if existing_employee:
        raise HTTPException(status_code=400, detail="Email already in use")

    # Create new employee
    new_employee = db.Employee(
        first_name=employee_input.first_name,
        last_name=employee_input.last_name,
        email=employee_input.email,
        hire_date=employee_input.hire_date,
        department_id=employee_input.department_id,
        role_id=employee_input.role_id,
        status=employee_input.status,
    )

    session.add(new_employee)
    try:
        session.commit()
        session.refresh(new_employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error adding employee: {str(e)}")

    return {
        "employee_id": new_employee.employee_id,
        "name": f"{new_employee.first_name} {new_employee.last_name}",
        "email": new_employee.email,
        "hire_date": str(new_employee.hire_date),
        "department": department.department_name,
        "role": role.role_name,
        "status": new_employee.status,
    }


@tool
def update_employee_first_name_db(
    employee_id: int, first_name: str, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's first name in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        first_name (str): The new first name.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee doesn't exist (404), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not first_name or not first_name.strip():
        raise HTTPException(status_code=400, detail="First name cannot be empty")

    employee.first_name = first_name.strip()

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error updating first name: {str(e)}"
        )

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_last_name_db(
    employee_id: int, last_name: str, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's last name in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        last_name (str): The new last name.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee doesn't exist (404), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if not last_name or not last_name.strip():
        raise HTTPException(status_code=400, detail="Last name cannot be empty")

    employee.last_name = last_name.strip()

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error updating last name: {str(e)}"
        )

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_email_db(
    employee_id: int, email: str, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's email in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        email (str): The new email address.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee doesn't exist (404), email is already in use (400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        validated_email = EmailStr(email)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid email format")

    if validated_email != employee.email:
        existing_employee = session.exec(
            select(db.Employee).where(db.Employee.email == validated_email)
        ).first()
        if existing_employee:
            raise HTTPException(status_code=400, detail="Email already in use")

    employee.email = validated_email

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating email: {str(e)}")

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_hire_date_db(
    employee_id: int, hire_date: str, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's hire date in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        hire_date (str): The new hire date in ISO format (YYYY-MM-DD).
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee doesn't exist (404), invalid date format (400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    try:
        validated_date = date.fromisoformat(hire_date)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid date format. Use YYYY-MM-DD"
        )

    if validated_date.year < 1900 or validated_date.year > 2025:
        raise HTTPException(
            status_code=400, detail="Hire date must be between 1900 and 2025"
        )

    employee.hire_date = validated_date

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error updating hire date: {str(e)}"
        )

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_department_db(
    employee_id: int, department_id: int, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's department in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        department_id (int): The new department ID.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee or department doesn't exist (404 or 400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    department = session.get(db.Department, department_id)
    if not department:
        raise HTTPException(status_code=400, detail="Department not found")

    employee.department_id = department_id

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error updating department: {str(e)}"
        )

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_role_db(
    employee_id: int, role_id: int, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's role in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        role_id (int): The new role ID.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee or role doesn't exist (404 or 400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    role = session.get(db.Role, role_id)
    if not role:
        raise HTTPException(status_code=400, detail="Role not found")

    employee.role_id = role_id

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating role: {str(e)}")

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def update_employee_status_db(
    employee_id: int, status: str, session: Any
) -> Dict[str, Any]:
    """
    Update an employee's status in the database.

    Args:
        employee_id (int): The ID of the employee to update.
        status (str): The new status (e.g., 'active', 'inactive').
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, Any]: Updated employee details.

    Raises:
        HTTPException: If employee doesn't exist (404), invalid status (400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    valid_statuses = ["active", "inactive"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400, detail=f"Invalid status. Must be one of {valid_statuses}"
        )

    employee.status = status

    try:
        session.commit()
        session.refresh(employee)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating status: {str(e)}")

    department = session.get(db.Department, employee.department_id)
    role = session.get(db.Role, employee.role_id)

    return {
        "employee_id": employee.employee_id,
        "name": f"{employee.first_name} {employee.last_name}",
        "email": employee.email,
        "hire_date": str(employee.hire_date),
        "department": department.department_name if department else None,
        "role": role.role_name if role else None,
        "status": employee.status,
    }


@tool
def delete_employee_db(employee_id: int, session: Any) -> Dict[str, str]:
    """
    Delete an employee from the database, checking for dependent records.

    Args:
        employee_id (int): The ID of the employee to delete.
        session (Session): The database session for executing queries.

    Returns:
        Dict[str, str]: Confirmation message of deletion.

    Raises:
        HTTPException: If employee doesn't exist (404), or if dependent records exist (400), or other database errors (400).
    """
    employee_id = int(employee_id)
    employee = session.get(db.Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    # Check for dependent records
    dependent_tables = [
        (db.EmployeeShift, db.EmployeeShift.employee_id),
        (db.EmployeeProject, db.EmployeeProject.employee_id),
        (db.EmployeeSkill, db.EmployeeSkill.employee_id),
        (db.PerformanceReview, db.PerformanceReview.employee_id),
    ]

    for table, column in dependent_tables:
        count = session.exec(
            select(func.count()).select_from(table).where(column == employee_id)
        ).one()
        if count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot delete employee due to dependent records in {table.__tablename__}",
            )

    session.delete(employee)
    try:
        session.commit()
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=400, detail=f"Error deleting employee: {str(e)}"
        )

    return {"message": f"Employee {employee_id} deleted successfully"}


@tool
def fetch_employee_by_id_db(session: Any, employee_id: int) -> Dict[str, Any]:
    """
    Fetch an employee by ID, including related department and role data.
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


@tool
def list_employees_by_skill_level_db(
    skill_level: str,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees with a specific skill proficiency level, including their department.

    Args:
        skill_level (str): The proficiency level to filter by (e.g., 'expert', 'intermediate').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees with the specified skill level.

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

    return formatted_results


@tool
def list_employees_by_performance_rating_db(
    rating: int,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees with a specific performance rating, including their department and role.

    Args:
        rating (int): The performance rating to filter by (1-5).
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees with the specified rating.

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

    return formatted_results


@tool
def list_employees_by_skill_db(
    skill_name: str,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees with a specific skill, including their department and skill proficiency.

    Args:
        skill_name (str): The skill name to filter by (e.g., 'Python').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees with the specified skill.

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

    return formatted_results


@tool
def list_employees_by_department_db(
    department_name: str,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees in a specific department, including their roles.

    Args:
        department_name (str): The department name to filter by (e.g., 'Engineering').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees in the specified department.

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

    return formatted_results


@tool
def list_employees_by_project_db(
    project_name: str,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees assigned to a specific project, including their role in the project and department.

    Args:
        project_name (str): The project name to filter by (e.g., 'Product Launch').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees assigned to the project.

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

    return formatted_results


@tool
def list_employees_by_shift_db(
    shift_name: str,
    session: Any,
    limit: Optional[int] = None,
) -> List[Dict]:
    """
    List employees assigned to a specific shift, including their department.

    Args:
        shift_name (str): The shift name to filter by (e.g., 'Morning').
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees assigned to the shift.

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

    return formatted_results


@tool
def list_employees_by_hire_year_db(
    year: int, session: Any, limit: Optional[int] = None
) -> List[Dict]:
    """
    List employees hired in a specific year, including their department and role.

    Args:
        year (int): The hire year to filter by (e.g., 2023).
        session (Session): The database session for executing queries.
        limit (Optional[int]): Maximum number of results to return.

    Returns:
        List[Dict]: List of employees hired in the specified year.

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

    return formatted_results
