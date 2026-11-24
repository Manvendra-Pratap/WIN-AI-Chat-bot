import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Message
from app.schemas import ChatRequest, ChatResponse
from app.services.llm_service import AllProvidersUnavailable, send_message

router = APIRouter(tags=["chat"])

DEFAULT_SYSTEM_PROMPT = "You are a helpful assistant."


def _parse_simulate_header(value: str | None) -> dict[str, int]:
    if not value:
        return {}
    pairs: dict[str, int] = {}
    for part in value.split(","):
        key, _, status = part.partition("=")
        key, status = key.strip(), status.strip()
        if key and status.isdigit():
            pairs[key] = int(status)
    return pairs


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@router.post("/chat", response_model=ChatResponse)
def chat(body: ChatRequest, request: Request, db: Session = Depends(get_db)):
    history = (
        db.query(Message)
        .filter(Message.session_id == body.session_id)
        .order_by(Message.created_at, Message.id)
        .all()
    )

    system_prompt = body.system_prompt or DEFAULT_SYSTEM_PROMPT
    messages = [{"role": "system", "content": system_prompt}]
    messages += [{"role": m.role, "content": m.content} for m in history]
    messages.append({"role": "user", "content": body.message})

    simulate: dict[str, int] = {}
    if settings.enable_failure_simulation:
        simulate = _parse_simulate_header(request.headers.get("x-simulate-failure"))

    try:
        result = send_message(messages, simulate=simulate)
    except AllProvidersUnavailable:
        raise HTTPException(503, "all providers unavailable")

    metadata = {
        "resolution_source": result["resolution_source"],
        "model": result["model"],
        "latency_ms": result["latency_ms"],
        "input_tokens": result["input_tokens"],
        "output_tokens": result["output_tokens"],
        "key_id": result["key_id"],
        "fallback_attempts": result["fallback_attempts"],
    }

    now = _now_iso()
    db.add(Message(session_id=body.session_id, role="user", content=body.message, created_at=now))
    db.add(
        Message(
            session_id=body.session_id,
            role="assistant",
            content=result["reply"],
            metadata_json=json.dumps(metadata),
            created_at=now,
        )
    )
    db.commit()

    return {"session_id": body.session_id, "reply": result["reply"], "metadata": metadata}
