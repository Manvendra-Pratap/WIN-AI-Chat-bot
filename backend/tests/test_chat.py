import app.services.llm_service as llm_service
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_live_inference_happy_path(monkeypatch, make_llm_response):
    monkeypatch.setattr(
        llm_service.litellm, "completion", lambda **kwargs: make_llm_response("Paris is the capital of France.")
    )

    response = client.post(
        "/chat", json={"session_id": "s-chat-1", "message": "What is the capital of France?"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["reply"] == "Paris is the capital of France."
    meta = body["metadata"]
    assert meta["resolution_source"] == "LIVE_INFERENCE"
    assert meta["key_id"] == "key_1"
    assert meta["fallback_attempts"] == 0
    assert meta["input_tokens"] == 10
    assert meta["output_tokens"] == 5


def test_multi_turn_history_persists(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("ok"))

    session_id = "s-chat-multi"
    client.post("/chat", json={"session_id": session_id, "message": "first"})
    client.post("/chat", json={"session_id": session_id, "message": "second"})

    history = client.get(f"/sessions/{session_id}/messages").json()
    roles = [m["role"] for m in history["messages"]]
    assert roles == ["user", "assistant", "user", "assistant"]
    assert history["messages"][0]["content"] == "first"
    assert history["messages"][2]["content"] == "second"


def test_two_sessions_are_independent(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("ok"))

    client.post("/chat", json={"session_id": "s-a", "message": "hello a"})
    client.post("/chat", json={"session_id": "s-b", "message": "hello b"})

    history_a = client.get("/sessions/s-a/messages").json()
    history_b = client.get("/sessions/s-b/messages").json()
    assert history_a["messages"][0]["content"] == "hello a"
    assert history_b["messages"][0]["content"] == "hello b"


def test_cache_hit_on_identical_first_message(monkeypatch, make_llm_response):
    calls = {"count": 0}

    def fake_completion(**kwargs):
        calls["count"] += 1
        return make_llm_response("cached answer", prompt_tokens=7, completion_tokens=3)

    monkeypatch.setattr(llm_service.litellm, "completion", fake_completion)

    first = client.post("/chat", json={"session_id": "s-cache-1", "message": "same question"})
    second = client.post("/chat", json={"session_id": "s-cache-2", "message": "same question"})

    assert calls["count"] == 1  # second request served from cache, provider not called again
    assert first.json()["reply"] == second.json()["reply"]

    meta2 = second.json()["metadata"]
    assert meta2["resolution_source"] == "LLM_CACHE"
    assert meta2["key_id"] is None
    assert meta2["fallback_attempts"] == 0
    assert meta2["input_tokens"] == 7
    assert meta2["output_tokens"] == 3


def test_different_message_is_not_a_cache_hit(monkeypatch, make_llm_response):
    calls = {"count": 0}

    def fake_completion(**kwargs):
        calls["count"] += 1
        return make_llm_response(f"answer {calls['count']}")

    monkeypatch.setattr(llm_service.litellm, "completion", fake_completion)

    client.post("/chat", json={"session_id": "s-cache-3", "message": "question A"})
    second = client.post("/chat", json={"session_id": "s-cache-4", "message": "question B"})

    assert calls["count"] == 2
    assert second.json()["metadata"]["resolution_source"] == "LIVE_INFERENCE"


def test_cache_response_consistency_across_repeated_hits(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("consistent answer"))

    first = client.post("/chat", json={"session_id": "s-consist-1", "message": "consistency check"})
    second = client.post("/chat", json={"session_id": "s-consist-2", "message": "consistency check"})
    third = client.post("/chat", json={"session_id": "s-consist-3", "message": "consistency check"})

    assert {first.json()["reply"], second.json()["reply"], third.json()["reply"]} == {"consistent answer"}
    assert second.json()["metadata"]["resolution_source"] == "LLM_CACHE"
    assert third.json()["metadata"]["resolution_source"] == "LLM_CACHE"


def test_token_usage_is_per_request_not_cumulative(monkeypatch, make_llm_response):
    call_tokens = iter([(10, 4), (55, 20)])

    def fake_completion(**kwargs):
        prompt_tokens, completion_tokens = next(call_tokens)
        return make_llm_response("turn reply", prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)

    monkeypatch.setattr(llm_service.litellm, "completion", fake_completion)

    session_id = "s-tokens-1"
    first = client.post("/chat", json={"session_id": session_id, "message": "turn one"})
    second = client.post("/chat", json={"session_id": session_id, "message": "turn two"})

    assert first.json()["metadata"]["input_tokens"] == 10
    assert first.json()["metadata"]["output_tokens"] == 4
    assert second.json()["metadata"]["input_tokens"] == 55
    assert second.json()["metadata"]["output_tokens"] == 20
