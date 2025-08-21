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
