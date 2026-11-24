# WIN-AI Chatbot

Multi-turn chatbot with LLM key failover, LiteLLM response caching, per-request
token tracking, and SQLite-backed conversation history.

## API

- `GET /health` -> `{"status": "ok", "keys_configured": N, "cache_enabled": bool}`
- `POST /chat` -> `{session_id, message, system_prompt?}` in, `{session_id, reply, metadata}` out
- `GET /sessions/{session_id}/messages` -> chronological history, 404 if unknown

Failover test hook: send `X-Simulate-Failure: key_1=429` (or `*=429`) on `POST /chat`
while `ENABLE_FAILURE_SIMULATION=true` to force a key to fail for that one request.

## Status

Backend is implemented and tested against the exact contract above. Frontend is
still the Prompt 1 placeholder shell.

## Run locally (no Docker)

    cd backend
    pip install -r requirements.txt
    cp ../.env.example ../.env
    uvicorn app.main:app --reload

## Run with Docker

    cp .env.example .env
    make up

Backend: http://localhost:8000, frontend: http://localhost:3000.

## Test

    make backend-test

## Design decisions

- **Key fallback:** keys are tried in the order listed in `LLM_API_KEYS`
  (`key_1`, `key_2`, ...); any exception from that key counts as a failed attempt
  and moves to the next one. All keys failing returns `503`.
- **Caching:** the LiteLLM response cache is checked explicitly (model + full
  message list) before the key loop runs, so a hit never touches a key, is never
  counted as a fallback attempt, and is fast by construction (no network call).
- **SQLite session storage:** one `messages` table, `session_id` as a plain
  string column (no separate sessions table -- an unknown id just starts a new
  history). Assistant metadata is stored as a JSON string per row.

## Config (.env)

- `LLM_API_KEYS` -- comma-separated keys, mapped in order to `key_1`, `key_2`, ...
- `LLM_MODEL` -- LiteLLM model name shared by every key
- `DATABASE_URL` -- SQLAlchemy URL; use `sqlite:////data/app.db` under Docker
- `ALLOWED_ORIGINS` -- comma-separated CORS origins
- `ENABLE_FAILURE_SIMULATION` -- `true` to honor the `X-Simulate-Failure` header
