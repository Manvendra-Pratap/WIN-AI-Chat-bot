"""Proves history is actually durable in the SQLite file -- reads it back with
plain sqlite3, bypassing the app's own ORM session entirely.
"""
import sqlite3

import app.services.llm_service as llm_service
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_message_is_durable_in_the_sqlite_file(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("durable answer"))

    session_id = "s-durable-1"
    client.post("/chat", json={"session_id": session_id, "message": "will this persist?"})

    db_path = settings.database_url.replace("sqlite:///", "", 1)
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE session_id = ? ORDER BY id", (session_id,)
        ).fetchall()
    finally:
        conn.close()

    assert rows == [("user", "will this persist?"), ("assistant", "durable answer")]
