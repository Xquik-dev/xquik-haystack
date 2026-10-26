# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from inspect import Signature, signature

import httpx
import pytest
from haystack import Document
from haystack.core.serialization import component_from_dict, component_to_dict
from haystack.utils import Secret

from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
from haystack_integrations.components.websearch.xquik.xquik_websearch import JsonValue

MODULE = "haystack_integrations.components.websearch.xquik.xquik_websearch"

TWEETS_RESPONSE: JsonValue = {
    "tweets": [
        {
            "id": "123",
            "text": "Haystack indexed this tweet as a Document.",
            "createdAt": "2026-05-15T07:00:00Z",
            "url": "https://x.com/example/status/123",
            "lang": "en",
            "likeCount": 7,
            "retweetCount": 2,
            "replyCount": 1,
            "quoteCount": 0,
            "viewCount": 120,
            "bookmarkCount": 3,
            "author": {
                "id": "42",
                "username": "xquikcom",
                "name": "Xquik",
                "verified": True,
            },
        }
    ],
    "has_next_page": True,
    "next_cursor": "cursor-1",
}


def _tweet_document(endpoint: str) -> Document:
    meta: dict[str, JsonValue] = {
        "endpoint": endpoint,
        "id": "123",
        "url": "https://x.com/example/status/123",
        "created_at": "2026-05-15T07:00:00Z",
        "lang": "en",
        "like_count": 7,
        "retweet_count": 2,
        "reply_count": 1,
        "quote_count": 0,
        "view_count": 120,
        "bookmark_count": 3,
        "author": {"id": "42", "username": "xquikcom", "name": "Xquik", "verified": True},
    }
    return Document(content="Haystack indexed this tweet as a Document.", meta=meta)


@dataclass
class FakeXquik:
    payload: JsonValue
    status_code: int = 200
    calls: list[dict[str, object]] = field(default_factory=list)

    def request(self, **kwargs: object) -> httpx.Response:
        self.calls.append(kwargs)
        return httpx.Response(
            self.status_code, json=self.payload, request=httpx.Request("GET", "https://xquik.com/api/v1")
        )

    async def async_request(self, **kwargs: object) -> httpx.Response:
        return self.request(**kwargs)


def fake_xquik(monkeypatch: pytest.MonkeyPatch, payload: JsonValue, status_code: int = 200) -> FakeXquik:
    xquik = FakeXquik(payload, status_code)
    monkeypatch.setattr(f"{MODULE}.request_with_retry", xquik.request)
    monkeypatch.setattr(f"{MODULE}.async_request_with_retry", xquik.async_request)
    return xquik


def resolved(secret: Secret) -> object:
    resolve: Callable[[], object] = secret.resolve_value
    return resolve()


@pytest.mark.parametrize(
    ("target", "positional_parameters"),
    [
        (
            signature(XquikTweetSearch.__init__),
            ["self", "api_key", "top_k", "query_type", "base_url", "extra_params", "timeout", "max_retries"],
        ),
        (
            signature(XquikTweetSearch.run),
            ["self", "query", "top_k", "query_type", "cursor", "since_time", "until_time"],
        ),
        (
            signature(XquikTweetSearch.run_async),
            ["self", "query", "top_k", "query_type", "cursor", "since_time", "until_time"],
        ),
        (
            signature(XquikUserTweetsFetcher.__init__),
            ["self", "api_key", "include_replies", "include_parent_tweet", "base_url", "timeout", "max_retries"],
        ),
        (
            signature(XquikUserTweetsFetcher.run),
            ["self", "user_id", "cursor", "include_replies", "include_parent_tweet"],
        ),
        (
            signature(XquikUserTweetsFetcher.run_async),
            ["self", "user_id", "cursor", "include_replies", "include_parent_tweet"],
        ),
    ],
)
def test_component_public_options_remain_positional(
    target: Signature,
    positional_parameters: list[str],
) -> None:
    actual = [
        name
        for name, parameter in target.parameters.items()
        if parameter.kind in {parameter.POSITIONAL_ONLY, parameter.POSITIONAL_OR_KEYWORD}
    ]

    assert actual == positional_parameters


class TestXquikTweetSearch:
    def test_init_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XQUIK_API_KEY", "xq_test")
        search = XquikTweetSearch()

        assert search.top_k == 20
        assert search.query_type == "Latest"
        assert search.base_url == "https://xquik.com/api/v1"
        assert search.timeout == 10
        assert search.max_retries == 3
        assert resolved(search.api_key) == "xq_test"

    def test_init_with_params(self) -> None:
        search = XquikTweetSearch(
            api_key=Secret.from_token("xq_custom"),
            top_k=5,
            query_type="Top",
            base_url="https://example.com/api/v1/",
            extra_params={"safe": "true"},
            timeout=20,
            max_retries=1,
        )

        assert search.top_k == 5
        assert search.query_type == "Top"
        assert search.base_url == "https://example.com/api/v1"
        assert search.extra_params == {"safe": "true"}
        assert search.timeout == 20
        assert search.max_retries == 1

    def test_to_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XQUIK_API_KEY", "xq_custom")
        search = XquikTweetSearch(top_k=5, query_type="Top")

        data: Mapping[str, object] = component_to_dict(search, "XquikTweetSearch")

        assert data == {
            "type": "haystack_integrations.components.websearch.xquik.xquik_websearch.XquikTweetSearch",
            "init_parameters": {
                "api_key": {"type": "env_var", "env_vars": ["XQUIK_API_KEY"], "strict": True},
                "top_k": 5,
                "query_type": "Top",
                "base_url": "https://xquik.com/api/v1",
                "extra_params": None,
                "timeout": 10,
                "max_retries": 3,
            },
        }

    def test_from_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XQUIK_API_KEY", "xq_custom")
        data: dict[str, JsonValue] = {
            "type": "haystack_integrations.components.websearch.xquik.xquik_websearch.XquikTweetSearch",
            "init_parameters": {
                "api_key": {"env_vars": ["XQUIK_API_KEY"], "strict": True, "type": "env_var"},
                "top_k": 3,
                "query_type": "Latest",
                "base_url": "https://example.com/api/v1",
                "extra_params": {"safe": "true"},
                "timeout": 15,
                "max_retries": 2,
            },
        }
        restore: Callable[[type[XquikTweetSearch], dict[str, JsonValue], str], object] = component_from_dict

        search = restore(XquikTweetSearch, data, "XquikTweetSearch")

        assert isinstance(search, XquikTweetSearch)
        assert resolved(search.api_key) == "xq_custom"
        assert search.top_k == 3
        assert search.base_url == "https://example.com/api/v1"
        assert search.extra_params == {"safe": "true"}

    def test_run_returns_documents_links_and_pagination(self, monkeypatch: pytest.MonkeyPatch) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"), top_k=5)
        fake_xquik(monkeypatch, TWEETS_RESPONSE)

        result = search.run(query="haystack ai")

        assert result == {
            "documents": [_tweet_document("x.tweets.search")],
            "links": ["https://x.com/example/status/123"],
            "has_more": True,
            "next_cursor": "cursor-1",
        }

    def test_run_passes_headers_and_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        search = XquikTweetSearch(
            api_key=Secret.from_token("xq_test"),
            top_k=5,
            query_type="Top",
            extra_params={"foo": "bar"},
        )
        xquik = fake_xquik(monkeypatch, {"tweets": []})

        search.run(
            query="haystack ai",
            top_k=3,
            query_type="Latest",
            cursor="cursor-0",
            since_time="2026-05-01T00:00:00Z",
            until_time="2026-05-15T00:00:00Z",
        )

        assert xquik.calls == [
            {
                "attempts": 3,
                "method": "GET",
                "url": "https://xquik.com/api/v1/x/tweets/search",
                "params": {
                    "q": "haystack ai",
                    "queryType": "Latest",
                    "limit": 3,
                    "cursor": "cursor-0",
                    "sinceTime": "2026-05-01T00:00:00Z",
                    "untilTime": "2026-05-15T00:00:00Z",
                    "foo": "bar",
                },
                "headers": {
                    "Accept": "application/json",
                    "x-api-key": "xq_test",
                    "xquik-api-contract": "2026-04-29",
                },
                "timeout": 10,
            }
        ]

    @pytest.mark.asyncio
    async def test_run_async(self, monkeypatch: pytest.MonkeyPatch) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"), top_k=5)
        fake_xquik(monkeypatch, TWEETS_RESPONSE)

        result = await search.run_async(query="haystack ai")

        assert result["documents"] == [_tweet_document("x.tweets.search")]
        assert result["links"] == ["https://x.com/example/status/123"]
        assert result["has_more"] is True

    def test_run_handles_empty_and_missing_optional_fields(self, monkeypatch: pytest.MonkeyPatch) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"))
        fake_xquik(monkeypatch, {"tweets": [{"id": "123"}], "has_more": False})
        meta: dict[str, JsonValue] = {"endpoint": "x.tweets.search", "id": "123"}

        result = search.run(query="missing text")

        assert result == {
            "documents": [Document(content="", meta=meta)],
            "links": [],
            "has_more": False,
            "next_cursor": None,
        }

    @pytest.mark.parametrize("tweets", [{"unexpected": True}, [None]])
    def test_run_ignores_invalid_tweet_collections(self, monkeypatch: pytest.MonkeyPatch, tweets: JsonValue) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"), top_k=None)
        xquik = fake_xquik(monkeypatch, {"tweets": tweets})

        result = search.run(query="haystack")

        assert [call["params"] for call in xquik.calls] == [{"q": "haystack", "queryType": "Latest"}]
        assert result["documents"] == []
        assert result["links"] == []

    def test_run_propagates_response_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"))
        fake_xquik(monkeypatch, {}, status_code=401)

        with pytest.raises(httpx.HTTPStatusError, match="401 Unauthorized"):
            search.run(query="haystack")


class TestXquikUserTweetsFetcher:
    def test_run_passes_path_and_params(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fetcher = XquikUserTweetsFetcher(api_key=Secret.from_token("xq_test"), include_replies=True)
        xquik = fake_xquik(monkeypatch, TWEETS_RESPONSE)

        result = fetcher.run(user_id="xquik/com", cursor="cursor-0", include_parent_tweet=True)

        assert [(call["url"], call["params"]) for call in xquik.calls] == [
            (
                "https://xquik.com/api/v1/x/users/xquik%2Fcom/tweets",
                {"includeReplies": True, "includeParentTweet": True, "cursor": "cursor-0"},
            )
        ]
        assert result["documents"] == [_tweet_document("x.users.tweets")]
        assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_run_async(self, monkeypatch: pytest.MonkeyPatch) -> None:
        fetcher = XquikUserTweetsFetcher(api_key=Secret.from_token("xq_test"))
        fake_xquik(monkeypatch, TWEETS_RESPONSE)

        result = await fetcher.run_async(user_id="xquikcom")

        assert len(result["documents"]) == 1
        assert result["links"] == ["https://x.com/example/status/123"]
