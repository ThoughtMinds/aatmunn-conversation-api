from sqlmodel import Field, SQLModel, Session, select
from datetime import datetime
from typing import Optional, List


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    intent_type: str = Field(index=True)
    request_data: str
    response_data: str
    status: str = Field(index=True)
    processing_time: Optional[float] = Field(default=None)


def create_log_entry(
    session: Session,
    intent_type: str,
    request_data: str,
    response_data: str,
    status: str,
    processing_time: float,
):
    log_entry = Log(
        intent_type=intent_type,
        request_data=request_data,
        response_data=response_data,
        status=status,
        processing_time=processing_time,
    )
    session.add(log_entry)
    session.commit()
    return log_entry


def get_logs(
    session: Session,
    offset: int = 0,
    limit: int = 10,
    intent_type: Optional[str] = None,
) -> List[Log]:
    query = select(Log).order_by(Log.id.desc()).offset(offset).limit(limit)
    if intent_type and intent_type != "all":
        if intent_type == "task":
            intent_type = "task_execution"
        query = query.where(Log.intent_type == intent_type)
    logs = session.exec(query).all()
    return logs


def count_logs(session: Session, intent_type: Optional[str] = None) -> int:
    query = select(Log)
    if intent_type and intent_type != "all":
        if intent_type == "task":
            intent_type = "task_execution"
        query = query.where(Log.intent_type == intent_type)

    results = session.exec(query).all()
    return len(results)
