from fastapi import APIRouter

from app.api.v1.routes import analyses, chat, health

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(analyses.router)
api_router.include_router(chat.router)
