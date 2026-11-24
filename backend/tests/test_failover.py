import app.services.llm_service as llm_service
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

client = TestClient(app)


def test_failover_to_second_key_on_exception(monkeypatch, make_llm_response):
    state = {"calls": 0}

    def fake_completion(**kwargs):
        state["calls"] += 1
        if state["calls"] == 1:
            raise RuntimeError("simulated provider failure")
        return make_llm_response("ok")

    monkeypatch.setattr(llm_service.litellm, "completion", fake_completion)

    response = client.post("/chat", json={"session_id": "s-fail-1", "message": "trigger failover"})
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert meta["key_id"] == "key_2"
    assert meta["fallback_attempts"] == 1


def test_all_keys_fail_returns_503_and_nothing_persisted(monkeypatch):
    def always_fail(**kwargs):
        raise RuntimeError("down")

    monkeypatch.setattr(llm_service.litellm, "completion", always_fail)

    response = client.post("/chat", json={"session_id": "s-fail-all", "message": "trigger 503"})
    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}

    history = client.get("/sessions/s-fail-all/messages")
    assert history.status_code == 404


def test_simulate_failure_header_forces_fallback(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("real answer"))

    response = client.post(
        "/chat",
        json={"session_id": "s-sim-1", "message": "simulate key_1 down"},
        headers={"X-Simulate-Failure": "key_1=429"},
    )
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert meta["key_id"] == "key_2"
    assert meta["fallback_attempts"] == 1


def test_simulate_failure_wildcard_returns_503(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("real answer"))

    response = client.post(
        "/chat",
        json={"session_id": "s-sim-2", "message": "simulate all down"},
        headers={"X-Simulate-Failure": "*=429"},
    )
    assert response.status_code == 503


def test_simulate_failure_status_500_also_forces_fallback(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("real answer"))

    response = client.post(
        "/chat",
        json={"session_id": "s-sim-3", "message": "simulate key_1 500"},
        headers={"X-Simulate-Failure": "key_1=500"},
    )
    assert response.status_code == 200
    assert response.json()["metadata"]["key_id"] == "key_2"


def test_simulate_failure_both_configured_keys_down_returns_503(monkeypatch, make_llm_response):
    # only 2 keys are configured in this test session (see conftest.py)
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("should not be reached"))

    response = client.post(
        "/chat",
        json={"session_id": "s-sim-4", "message": "simulate both keys down"},
        headers={"X-Simulate-Failure": "key_1=429,key_2=500"},
    )
    assert response.status_code == 503
    assert response.json() == {"detail": "all providers unavailable"}


def test_simulated_failure_does_not_persist_to_next_request(monkeypatch, make_llm_response):
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("ok"))

    client.post(
        "/chat",
        json={"session_id": "s-sim-temp-1", "message": "force key_1 down this once"},
        headers={"X-Simulate-Failure": "key_1=429"},
    )
    second = client.post("/chat", json={"session_id": "s-sim-temp-2", "message": "key_1 should work again"})
    assert second.json()["metadata"]["key_id"] == "key_1"


def test_simulate_failure_header_ignored_when_disabled(monkeypatch, make_llm_response):
    monkeypatch.setattr(settings, "enable_failure_simulation", False)
    monkeypatch.setattr(llm_service.litellm, "completion", lambda **kwargs: make_llm_response("real answer, header ignored"))

    response = client.post(
        "/chat",
        json={"session_id": "s-sim-off", "message": "header should be ignored"},
        headers={"X-Simulate-Failure": "*=429"},
    )
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert meta["key_id"] == "key_1"
    assert meta["fallback_attempts"] == 0


def test_multi_key_failover_third_key_succeeds(monkeypatch, make_llm_response):
    monkeypatch.setattr(settings, "llm_api_keys", "k1,k2,k3")
    state = {"calls": 0}

    def fake_completion(**kwargs):
        state["calls"] += 1
        if state["calls"] <= 2:
            raise RuntimeError("simulated provider failure")
        return make_llm_response("third key answer")

    monkeypatch.setattr(llm_service.litellm, "completion", fake_completion)

    response = client.post("/chat", json={"session_id": "s-multi-fail", "message": "needs third key"})
    assert response.status_code == 200
    meta = response.json()["metadata"]
    assert meta["key_id"] == "key_3"
    assert meta["fallback_attempts"] == 2
