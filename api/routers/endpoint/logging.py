from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from api import agent, db, schema
import pandas as pd
from typing import Annotated, List
from sqlmodel import Session
from time import time


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.get("/get_audit_log/", response_model=schema.AuditLog)
def get_audit_log(session: SessionDep) -> List[schema.AuditLog]:

    # fetch audit log from db
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

    raise audit_logs