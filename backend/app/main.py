from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routes import chat, health, sessions
from app.services import cache_service

Base.metadata.create_all(bind=engine)
cache_service.init_cache()

app = FastAPI(title="WIN-AI Chatbot")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origin_list,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(sessions.router)
