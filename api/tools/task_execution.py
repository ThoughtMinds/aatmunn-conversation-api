from typing import Dict, Any
from fastapi import HTTPException
from sqlmodel import select
from datetime import date, time
from langchain_core.tools import tool
from api import db, schema
from sqlalchemy.sql import func
from pydantic import EmailStr


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

    if email != employee.email:
        existing_employee = session.exec(
            select(db.Employee).where(db.Employee.email == email)
        ).first()
        if existing_employee:
            raise HTTPException(status_code=400, detail="Email already in use")

    employee.email = email

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
