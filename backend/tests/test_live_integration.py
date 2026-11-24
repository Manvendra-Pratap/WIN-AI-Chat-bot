"""Genuine provider call -- skipped unless real keys are explicitly opted in.
Run with: RUN_LIVE_LLM_TESTS=1 LLM_API_KEYS=<real keys> pytest tests/test_live_integration.py
"""
import os

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.skipif(
    not os.environ.get("RUN_LIVE_LLM_TESTS"),
    reason="set RUN_LIVE_LLM_TESTS=1 with real LLM_API_KEYS to exercise a genuine provider call",
)


def test_live_chat_roundtrip():
    from app.main import app  # imported here so the skip above also skips this import

    client = TestClient(app)
    response = client.post("/chat", json={"session_id": "s-live-1", "message": "Reply with only the word OK."})
    assert response.status_code == 200
    body = response.json()
    assert body["reply"]
    assert body["metadata"]["resolution_source"] in ("LIVE_INFERENCE", "LLM_CACHE")
    assert body["metadata"]["input_tokens"] > 0
    assert body["metadata"]["output_tokens"] > 0
