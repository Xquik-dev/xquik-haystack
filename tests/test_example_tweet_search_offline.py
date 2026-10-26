# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Mapping
from pathlib import Path

import httpx
import pytest
from haystack import Document, Pipeline
from haystack.utils import Secret

from haystack_integrations.components.websearch.xquik import XquikTweetSearch
from haystack_integrations.components.websearch.xquik.xquik_websearch import JsonValue

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "xquik_tweet_search.py"

FAKE_XQUIK_RESPONSE: JsonValue = {
    "tweets": [
        {
            "id": "555",
            "text": "Haystack mapped this offline tweet to a Document.",
            "createdAt": "2026-07-01T12:00:00Z",
            "url": "https://x.com/example/status/555",
            "lang": "en",
            "likeCount": 1,
            "retweetCount": 0,
            "replyCount": 0,
            "quoteCount": 0,
            "viewCount": 10,
            "bookmarkCount": 0,
            "author": {
                "id": "9",
                "username": "fixture",
                "name": "Fixture",
                "verified": False,
            },
        }
    ],
    "has_next_page": False,
    "next_cursor": None,
}


def test_example_file_still_documents_pipeline_shape() -> None:
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "XquikTweetSearch" in source
    assert "pipeline.run" in source
    assert 'query": "haystack ai"' in source


def test_tweet_search_example_runs_offline_with_fake_xquik_client(monkeypatch: pytest.MonkeyPatch) -> None:
    search = XquikTweetSearch(api_key=Secret.from_token("xq_offline"), top_k=10)
    pipeline = Pipeline()
    pipeline.add_component("x_search", search)
    calls: list[dict[str, object]] = []

    def fake_request(**kwargs: object) -> httpx.Response:
        calls.append(kwargs)
        return httpx.Response(200, json=FAKE_XQUIK_RESPONSE, request=httpx.Request("GET", "https://xquik.com/api/v1"))

    monkeypatch.setattr(
        "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry", fake_request
    )
    inputs: dict[str, dict[str, str]] = {"x_search": {"query": "haystack ai"}}

    result: Mapping[str, Mapping[str, object]] = pipeline.run(inputs)

    assert [(call["url"], call["params"]) for call in calls] == [
        ("https://xquik.com/api/v1/x/tweets/search", {"q": "haystack ai", "queryType": "Latest", "limit": 10})
    ]
    meta: dict[str, JsonValue] = {
        "endpoint": "x.tweets.search",
        "id": "555",
        "url": "https://x.com/example/status/555",
        "created_at": "2026-07-01T12:00:00Z",
        "lang": "en",
        "like_count": 1,
        "retweet_count": 0,
        "reply_count": 0,
        "quote_count": 0,
        "view_count": 10,
        "bookmark_count": 0,
        "author": {"id": "9", "username": "fixture", "name": "Fixture", "verified": False},
    }
    assert result["x_search"]["documents"] == [
        Document(content="Haystack mapped this offline tweet to a Document.", meta=meta)
    ]
    assert result["x_search"]["links"] == ["https://x.com/example/status/555"]
    assert result["x_search"]["has_more"] is False
