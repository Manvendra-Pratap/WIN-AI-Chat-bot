import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Message
from app.schemas import HistoryResponse

router = APIRouter(tags=["sessions"])


@router.get("/sessions/{session_id}/messages", response_model=HistoryResponse)
def get_history(session_id: str, db: Session = Depends(get_db)):
    rows = (
        db.query(Message)
        .filter(Message.session_id == session_id)
        .order_by(Message.created_at, Message.id)
        .all()
    )
    if not rows:
        raise HTTPException(404, "session not found")

    messages = []
    for row in rows:
        entry = {"role": row.role, "content": row.content}
        if row.role == "assistant" and row.metadata_json:
            meta = json.loads(row.metadata_json)
            entry["metadata"] = {
                "resolution_source": meta["resolution_source"],
                "input_tokens": meta["input_tokens"],
                "output_tokens": meta["output_tokens"],
            }
        messages.append(entry)

    return {"session_id": session_id, "messages": messages}
