"""Wires LiteLLM's built-in response cache. Cache identity is model + the full
message list (system prompt + history + new message), per the API contract --
checked explicitly here (rather than via completion(caching=True)) so a hit never
touches the key loop: no key_id, no fallback attempt, and it's fast by construction.

max_messages=None disables litellm's default cap: Cache() otherwise silently
stops caching once a conversation passes 4 messages, which would break caching
for any real multi-turn session.
"""
import litellm
from litellm.caching.caching import Cache

_cache: Cache | None = None


def init_cache() -> None:
    global _cache
    _cache = Cache(type="local", max_messages=None)
    litellm.cache = _cache


def is_enabled() -> bool:
    return _cache is not None


def get_cached(model: str, messages: list[dict]) -> dict | None:
    if _cache is None:
        return None
    return _cache.get_cache(model=model, messages=messages)


def store_cached(model: str, messages: list[dict], result: dict) -> None:
    if _cache is not None:
        _cache.add_cache(result, model=model, messages=messages)
