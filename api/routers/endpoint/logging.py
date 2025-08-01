from fastapi import APIRouter, Depends
from api import db, schema
from typing import Annotated, List
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.get("/get_audit_log/", response_model=schema.AuditLog)
def get_audit_log(session: SessionDep) -> List[schema.AuditLog]:

    # fetch audit log from db
    # Dynamic data field based on Intent type with their own metadata for UI
    audit_logs = [
        schema.AuditLog(
            intent_type="navigation",
            data=schema.RequestData(input="Home page", output="Home page screen"),
            status="success",
        ),
        schema.AuditLog(
            intent_type="summarization",
            data=schema.RequestData(input="Home page", output="Home page screen"),
            status="error",
        ),
        schema.AuditLog(
            intent_type="task-execution",
            data=schema.RequestData(input="Home page", output="Home page screen"),
            status="success",
        ),
        schema.AuditLog(
            intent_type="navigation",
            data=schema.RequestData(input="Home page", output="Home page screen"),
            status="error",
        ),
    ]

    return audit_logs
