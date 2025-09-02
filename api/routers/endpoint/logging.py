from fastapi import APIRouter, Depends, Query
from api import db, schema
from typing import Annotated, List, Optional
from sqlmodel import Session
from api.db.log import get_logs, count_logs


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.get("/get_audit_log/", response_model=List[schema.AuditLog])
async def get_audit_log(
    session: SessionDep,
    offset: int = 0,
    limit: int = 10,
    intent_type: Optional[str] = Query(None, alias="intentType"),
) -> List[schema.AuditLog]:
    """
    Retrieve the audit log.

    This endpoint fetches the audit log from the database, which contains
    information about past requests and their outcomes.

    Args:
        session (SessionDep): The database session dependency.

    Returns:
        List[schema.AuditLog]: A list of audit log entries.
    """
    logs = get_logs(session=session, offset=offset, limit=limit, intent_type=intent_type)

    audit_logs = [
        schema.AuditLog(
            id=log.id,
            timestamp=log.timestamp,
            intent_type=log.intent_type,
            data=schema.RequestData(input=log.request_data, output=log.response_data),
            status=log.status,
        )
        for log in logs
    ]
    return audit_logs


@router.get("/get_audit_log_count/")
async def get_audit_log_count(
    session: SessionDep,
    intent_type: Optional[str] = Query(None, alias="intentType"),
) -> dict:
    count = count_logs(session=session, intent_type=intent_type)
    return {"total": count}
