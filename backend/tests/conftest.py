"""Test-only setup: points the DB at a throwaway file and, if the real litellm
package can't be imported in this environment, installs a minimal stand-in so the
app's import graph resolves. Production never loads this file.
"""
import json
import os
import sys
import tempfile
import types

import pytest

_tmpdir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmpdir}/test.db"
os.environ["LLM_API_KEYS"] = "test-key-1,test-key-2"
os.environ["ALLOWED_ORIGINS"] = "http://localhost:3000"
os.environ["ENABLE_FAILURE_SIMULATION"] = "true"


def _install_fake_litellm() -> None:
    try:
        import litellm  # noqa: F401

        return
    except ImportError:
        pass

    fake = types.ModuleType("litellm")
    fake.cache = None
    fake.completion = lambda **kwargs: (_ for _ in ()).throw(
        NotImplementedError("tests must monkeypatch litellm.completion")
    )

    caching_pkg = types.ModuleType("litellm.caching")
    caching_mod = types.ModuleType("litellm.caching.caching")

    class FakeCache:
        def __init__(self, *args, **kwargs) -> None:
            self._store: dict[str, dict] = {}

        @staticmethod
        def _key(model: str, messages: list[dict]) -> str:
            return model + "|" + json.dumps(messages, sort_keys=True)

        def get_cache(self, *, model: str, messages: list[dict], **kwargs):
            return self._store.get(self._key(model, messages))

        def add_cache(self, result, *, model: str, messages: list[dict], **kwargs):
            self._store[self._key(model, messages)] = result

    caching_mod.Cache = FakeCache
    caching_pkg.caching = caching_mod
    fake.caching = caching_pkg

    sys.modules["litellm"] = fake
    sys.modules["litellm.caching"] = caching_pkg
    sys.modules["litellm.caching.caching"] = caching_mod


_install_fake_litellm()


@pytest.fixture
def make_llm_response():
    def _make(content: str, prompt_tokens: int = 10, completion_tokens: int = 5):
        message = types.SimpleNamespace(content=content)
        choice = types.SimpleNamespace(message=message)
        usage = types.SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=completion_tokens)
        return types.SimpleNamespace(choices=[choice], usage=usage)

    return _make
