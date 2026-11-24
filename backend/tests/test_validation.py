from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_missing_message_is_422():
    assert client.post("/chat", json={"session_id": "s1"}).status_code == 422


def test_empty_message_after_trim_is_422():
    assert client.post("/chat", json={"session_id": "s1", "message": "   "}).status_code == 422


def test_message_too_long_is_422():
    assert client.post("/chat", json={"session_id": "s1", "message": "x" * 4001}).status_code == 422


def test_missing_session_id_is_422():
    assert client.post("/chat", json={"message": "hi"}).status_code == 422


def test_unknown_session_history_is_404():
    response = client.get("/sessions/does-not-exist/messages")
    assert response.status_code == 404
    assert response.json() == {"detail": "session not found"}


def test_malformed_json_is_422():
    response = client.post(
        "/chat", content="{not valid json", headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 422
