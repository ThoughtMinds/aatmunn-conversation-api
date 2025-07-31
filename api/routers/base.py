from fastapi import APIRouter
from .endpoint import navigation, navigation_intents

api_router = APIRouter()

api_router.include_router(navigation_intents.router, prefix="/navigation_intents", tags=["navigation-intents"])
api_router.include_router(navigation.router, prefix="/navigation", tags=["navigation"])
