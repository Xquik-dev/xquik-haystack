# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

import logging as stdlib_logging
import sys
from collections.abc import Callable
from types import ModuleType
from typing import NoReturn, TypeVar

import atheris

MAX_INPUT_LENGTH = 4096
NETWORK_ERROR = "Network request blocked. Test response conversion only."

_Decorated = TypeVar("_Decorated")


class _Document:
    def __init__(self, content: str, meta: dict[str, object]) -> None:
        self.content = content
        self.meta = meta


class _Component:
    def __call__(self, value: _Decorated) -> _Decorated:
        return value

    @staticmethod
    def output_types(**_types: object) -> Callable[[_Decorated], _Decorated]:
        return lambda value: value


class _Secret:
    def __init__(self, value: str = "") -> None:
        self.value = value

    @classmethod
    def from_env_var(cls, _name: str) -> _Secret:
        return cls()

    def resolve_value(self) -> str:
        return self.value


def _unused_request(*_args: object, **_kwargs: object) -> NoReturn:
    raise RuntimeError(NETWORK_ERROR)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


class _Haystack(ModuleType):
    Document = _Document
    component = _Component()
    logging = stdlib_logging


class _HaystackUtils(ModuleType):
    Secret = _Secret


class _RequestsUtils(ModuleType):
    async_request_with_retry = staticmethod(_unused_request)
    request_with_retry = staticmethod(_unused_request)


haystack = _Haystack("haystack")
haystack.__path__ = []
haystack_utils = _HaystackUtils("haystack.utils")
haystack_utils.__path__ = []

sys.modules["haystack"] = haystack
sys.modules["haystack.utils"] = haystack_utils
sys.modules["haystack.utils.requests_utils"] = _RequestsUtils("haystack.utils.requests_utils")

with atheris.instrument_imports():
    from haystack_integrations.components.websearch.xquik.xquik_websearch import (
        JsonValue,
        _as_list,
        _as_optional_string,
        _compact,
        _get,
        _parse_tweets_response,
        _tweet_content,
        _tweet_meta,
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

    tweet: dict[str, JsonValue] = {
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
    tweet_collection: JsonValue = [tweet, text, None] if selector & 1 else {"unexpected": text}
    response: JsonValue = {
        "tweets" if selector & 8 else "data": tweet_collection,
        "has_next_page" if selector & 16 else "hasMore": bool(selector & 32),
        "next_cursor" if selector & 64 else "nextCursor": text if selector & 128 else None,
    }

    result = _parse_tweets_response(response, endpoint=text)
    expected_documents = 1 if isinstance(tweet_collection, list) else 0

    _require(set(result) == {"documents", "links", "has_more", "next_cursor"}, "Response keys changed. Restore them.")
    _require(len(result["documents"]) == expected_documents, "Document count changed. Check conversion.")
    _require(
        all(result["links"]),
        "Response link is invalid. Check parsing.",
    )
    _require(isinstance(result["has_more"], bool), "has_more is invalid. Return a boolean.")
    _require(
        result["next_cursor"] is None or isinstance(result["next_cursor"], str),
        "next_cursor is invalid. Return a string or None.",
    )

    meta = _tweet_meta(tweet, endpoint=text)
    author = meta.get("author")
    _require(isinstance(_tweet_content(tweet), str), "Document content is invalid. Return a string.")
    _require(meta["endpoint"] == text, "Document endpoint changed. Preserve its value.")
    _require(isinstance(author, dict) and "ignored" not in author, "Author data leaked. Filter unknown fields.")

    _require(_get(tweet, "missing", text_key, default=None) == text, "Alias lookup failed. Check fallback keys.")
    expected_list = tweet_collection if isinstance(tweet_collection, list) else []
    _require(_as_list(tweet_collection) == expected_list, "List conversion failed. Check input handling.")
    _require(_as_optional_string(None) is None, "None conversion failed. Preserve None.")
    _require(_as_optional_string(selector) == str(selector), "Integer conversion failed. Return a string.")
    _require(_compact({"text": text, "missing": None}) == {"text": text}, "Compaction failed. Remove None values.")


atheris.Setup(sys.argv, fuzz_response_helpers)
atheris.Fuzz()
