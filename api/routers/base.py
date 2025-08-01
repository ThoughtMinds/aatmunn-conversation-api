from fastapi import APIRouter
from .endpoint import logging, metadata, navigation, navigation_intents, orchestrator, summarization, task_execution

api_router = APIRouter()


api_router.include_router(logging.router, prefix="/logging", tags=["logging"])
api_router.include_router(metadata.router, prefix="/metadata", tags=["metadata"])
api_router.include_router(navigation_intents.router, prefix="/navigation_intents", tags=["navigation_intents"])
api_router.include_router(navigation.router, prefix="/navigation", tags=["navigation"])
api_router.include_router(summarization.router, prefix="/summarization", tags=["summarization"])
api_router.include_router(task_execution.router, prefix="/task_execution", tags=["task_execution"])
api_router.include_router(orchestrator.router, prefix="/orchestrator", tags=["orchestrator"])


