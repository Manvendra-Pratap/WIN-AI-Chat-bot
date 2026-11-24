from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.database import engine
from app.services import cache_service

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "keys_configured": len(settings.api_key_list),
        "cache_enabled": cache_service.is_enabled(),
    }
