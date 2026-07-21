from __future__ import annotations

import logging
import sys
from collections.abc import Callable, Sequence
from contextlib import AbstractContextManager
from importlib import import_module
from types import ModuleType
from typing import Any, NoReturn, cast

MAX_INPUT_LENGTH = 4096
NETWORK_ERROR = "network requests are outside this fuzz target"


class _Document:
    def __init__(self, content: str, meta: dict[str, Any]) -> None:
        self.content = content
        self.meta = meta


class _Component:
    def __call__(self, value: Any) -> Any:
        return value

    @staticmethod
    def output_types(**_types: Any) -> Callable[[Any], Any]:
        return lambda value: value


class _Secret:
    def __init__(self, value: str = "") -> None:
        self.value = value

    @classmethod
    def from_env_var(cls, _name: str) -> _Secret:
        return cls()

    def resolve_value(self) -> str:
        return self.value


def _unused_request(*_args: Any, **_kwargs: Any) -> NoReturn:
    raise RuntimeError(NETWORK_ERROR)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


haystack = ModuleType("haystack")
haystack.__path__ = []
haystack.Document = _Document
haystack.component = _Component()
haystack.logging = logging

haystack_utils = ModuleType("haystack.utils")
haystack_utils.__path__ = []
haystack_utils.Secret = _Secret

requests_utils = ModuleType("haystack.utils.requests_utils")
requests_utils.async_request_with_retry = _unused_request
requests_utils.request_with_retry = _unused_request

sys.modules["haystack"] = haystack
sys.modules["haystack.utils"] = haystack_utils
sys.modules["haystack.utils.requests_utils"] = requests_utils

atheris = import_module("atheris")
instrument_imports = cast(Callable[[], AbstractContextManager[None]], atheris.instrument_imports)
setup = cast(Callable[[Sequence[str], Callable[[bytes], None]], None], atheris.Setup)
fuzz = cast(Callable[[], NoReturn], atheris.Fuzz)

with instrument_imports():
    from haystack_integrations.components.websearch.xquik.xquik_websearch import (
        _as_list,
        _as_optional_string,
        _compact,
        _get,
        _parse_tweets_response,
        _tweet_to_document,
    )


def fuzz_response_helpers(data: bytes) -> None:
    """Exercise response conversion with bounded generated values."""
    if len(data) > MAX_INPUT_LENGTH:
        return

    text = data.decode("utf-8", errors="replace")
    selector = data[0] if data else 0
    text_key = ("text", "full_text", "content")[selector % 3]
    created_key = ("created_at", "createdAt")[selector % 2]
    author_key = ("author", "user")[selector % 2]
    username_key = ("username", "screen_name")[selector % 2]

    tweet: dict[str, Any] = {
        "id": str(selector),
        text_key: text,
        created_key: text,
        "url": text if selector & 2 else "",
        author_key: {
            "id": selector,
            username_key: text,
            "name": text,
            "verified": bool(selector & 4),
            "ignored": None,
        },
    }
    tweet_collection: Any = [tweet, text, None] if selector & 1 else {"unexpected": text}
    response = {
        "tweets" if selector & 8 else "data": tweet_collection,
        "has_next_page" if selector & 16 else "hasMore": bool(selector & 32),
        "next_cursor" if selector & 64 else "nextCursor": text if selector & 128 else None,
    }

    result = _parse_tweets_response(response, endpoint=text)
    expected_documents = 1 if isinstance(tweet_collection, list) else 0

    _require(set(result) == {"documents", "links", "has_more", "next_cursor"}, "unexpected response keys")
    _require(len(result["documents"]) == expected_documents, "unexpected document count")
    _require(all(isinstance(link, str) and link for link in result["links"]), "invalid response link")
    _require(isinstance(result["has_more"], bool), "has_more must be a boolean")
    _require(
        result["next_cursor"] is None or isinstance(result["next_cursor"], str),
        "next_cursor must be an optional string",
    )

    document = _tweet_to_document(tweet, endpoint=text)
    _require(isinstance(document.content, str), "document content must be a string")
    _require(document.meta["endpoint"] == text, "document endpoint changed")
    _require("ignored" not in document.meta.get("author", {}), "unexpected author field")

    _require(_get(tweet, "missing", text_key, default=None) == text, "alias lookup failed")
    expected_list = tweet_collection if isinstance(tweet_collection, list) else []
    _require(_as_list(tweet_collection) == expected_list, "list coercion failed")
    _require(_as_optional_string(None) is None, "None string coercion failed")
    _require(_as_optional_string(selector) == str(selector), "integer string coercion failed")
    _require(_compact({"text": text, "missing": None}) == {"text": text}, "mapping compaction failed")


setup(sys.argv, fuzz_response_helpers)
fuzz()
