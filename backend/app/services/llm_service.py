"""Sends a conversation to the LLM, trying each configured key in order until one
succeeds, with the response cache checked first. Returns every field the API
contract requires in `metadata`.

ponytail: folded the key-failover loop in here instead of a separate
failover_service.py -- it's one function, used from exactly one place.
"""
import logging
import time

import litellm

from app.config import settings
from app.services import cache_service

logger = logging.getLogger("win_ai.llm")


class AllProvidersUnavailable(Exception):
    pass


def _key_ids() -> list[str]:
    return [f"key_{i + 1}" for i in range(len(settings.api_key_list))]


def send_message(messages: list[dict], simulate: dict[str, int] | None = None) -> dict:
    simulate = simulate or {}
    model = settings.llm_model
    start = time.perf_counter()

    cached = cache_service.get_cached(model, messages)
    if cached is not None:
        return {
            "reply": cached["content"],
            "resolution_source": "LLM_CACHE",
            "model": model,
            "latency_ms": round((time.perf_counter() - start) * 1000),
            "input_tokens": cached["input_tokens"],
            "output_tokens": cached["output_tokens"],
            "key_id": None,
            "fallback_attempts": 0,
        }

    fallback_attempts = 0
    for key, key_id in zip(settings.api_key_list, _key_ids()):
        forced_status = simulate.get("*", simulate.get(key_id))
        try:
            if forced_status is not None:
                raise RuntimeError(f"simulated failure status={forced_status}")
            response = litellm.completion(model=model, messages=messages, api_key=key)
            result = {
                "content": response.choices[0].message.content,
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
            cache_service.store_cached(model, messages, result)
            return {
                "reply": result["content"],
                "resolution_source": "LIVE_INFERENCE",
                "model": model,
                "latency_ms": round((time.perf_counter() - start) * 1000),
                "input_tokens": result["input_tokens"],
                "output_tokens": result["output_tokens"],
                "key_id": key_id,
                "fallback_attempts": fallback_attempts,
            }
        except Exception as exc:
            logger.warning("key %s failed: %s", key_id, exc)
            fallback_attempts += 1

    raise AllProvidersUnavailable
