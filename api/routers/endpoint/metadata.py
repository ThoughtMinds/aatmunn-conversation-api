from fastapi import APIRouter, Depends
from api import db, schema
from typing import Annotated, List
from sqlmodel import Session


router = APIRouter()
SessionDep = Annotated[Session, Depends(db.get_session)]


@router.get("/get_dashboard_stats/", response_model=schema.DashboardStats)
def get_dashboard_stats(session: SessionDep) -> schema.DashboardStats:
    """
    Retrieve dashboard statistics.

    This endpoint fetches statistics for the dashboard, such as the total
    number of intents, summaries, and tasks.

    Args:
        session (SessionDep): The database session dependency.

    Returns:
        schema.DashboardStats: The dashboard statistics.
    """
    # Fetch stats from db
    stats = schema.DashboardStats(total_intents=10, total_summaries=5, total_tasks=3)

    return stats
