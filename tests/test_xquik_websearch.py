# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from haystack import Document
from haystack.core.serialization import component_from_dict, component_to_dict
from haystack.utils import Secret

from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher

TWEETS_RESPONSE = {
    "tweets": [
        {
            "id": "123",
            "text": "Haystack pipelines can retrieve public X context.",
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


def _mock_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


class TestXquikTweetSearch:
    def test_init_default(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XQUIK_API_KEY", "xq_test")
        search = XquikTweetSearch()

        assert search.top_k == 20
        assert search.query_type == "Latest"
        assert search.base_url == "https://xquik.com/api/v1"
        assert search.timeout == 10
        assert search.max_retries == 3
        assert search.api_key.resolve_value() == "xq_test"

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

        data = component_to_dict(search, "XquikTweetSearch")

        assert data["type"] == ("haystack_integrations.components.websearch.xquik.xquik_websearch.XquikTweetSearch")
        assert data["init_parameters"]["top_k"] == 5
        assert data["init_parameters"]["query_type"] == "Top"
        assert data["init_parameters"]["timeout"] == 10

    def test_from_dict(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("XQUIK_API_KEY", "xq_custom")
        data = {
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

        search = component_from_dict(XquikTweetSearch, data, "XquikTweetSearch")

        assert search.api_key.resolve_value() == "xq_custom"
        assert search.top_k == 3
        assert search.base_url == "https://example.com/api/v1"
        assert search.extra_params == {"safe": "true"}

    def test_run_returns_documents_links_and_pagination(self) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"), top_k=5)

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
            return_value=_mock_response(TWEETS_RESPONSE),
        ):
            result = search.run(query="haystack ai")

        assert len(result["documents"]) == 1
        assert isinstance(result["documents"][0], Document)
        assert result["documents"][0].content == "Haystack pipelines can retrieve public X context."
        assert result["documents"][0].meta["id"] == "123"
        assert result["documents"][0].meta["endpoint"] == "x.tweets.search"
        assert result["documents"][0].meta["created_at"] == "2026-05-15T07:00:00Z"
        assert result["documents"][0].meta["like_count"] == 7
        assert result["documents"][0].meta["author"] == {
            "id": "42",
            "username": "xquikcom",
            "name": "Xquik",
            "verified": True,
        }
        assert result["links"] == ["https://x.com/example/status/123"]
        assert result["has_more"] is True
        assert result["next_cursor"] == "cursor-1"

    def test_run_passes_headers_and_params(self) -> None:
        search = XquikTweetSearch(
            api_key=Secret.from_token("xq_test"),
            top_k=5,
            query_type="Top",
            extra_params={"foo": "bar"},
        )

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
            return_value=_mock_response({"tweets": []}),
        ) as mock_request:
            search.run(
                query="haystack ai",
                top_k=3,
                query_type="Latest",
                cursor="cursor-0",
                since_time="2026-05-01T00:00:00Z",
                until_time="2026-05-15T00:00:00Z",
            )

        assert mock_request.call_args.kwargs["url"] == "https://xquik.com/api/v1/x/tweets/search"
        assert mock_request.call_args.kwargs["headers"] == {
            "Accept": "application/json",
            "x-api-key": "xq_test",
            "xquik-api-contract": "2026-04-29",
        }
        assert mock_request.call_args.kwargs["params"] == {
            "q": "haystack ai",
            "queryType": "Latest",
            "limit": 3,
            "cursor": "cursor-0",
            "sinceTime": "2026-05-01T00:00:00Z",
            "untilTime": "2026-05-15T00:00:00Z",
            "foo": "bar",
        }

    @pytest.mark.asyncio
    async def test_run_async(self) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"), top_k=5)

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.async_request_with_retry",
            new_callable=AsyncMock,
            return_value=_mock_response(TWEETS_RESPONSE),
        ):
            result = await search.run_async(query="haystack ai")

        assert len(result["documents"]) == 1
        assert result["links"] == ["https://x.com/example/status/123"]
        assert result["has_more"] is True

    def test_run_handles_empty_and_missing_optional_fields(self) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"))

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
            return_value=_mock_response({"tweets": [{"id": "123"}], "has_more": False}),
        ):
            result = search.run(query="missing text")

        assert result["documents"][0].content == ""
        assert result["documents"][0].meta == {"endpoint": "x.tweets.search", "id": "123"}
        assert result["links"] == []
        assert result["has_more"] is False
        assert result["next_cursor"] is None

    def test_run_raises_on_http_error(self) -> None:
        search = XquikTweetSearch(api_key=Secret.from_token("xq_test"))
        response = _mock_response({})
        response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401 Unauthorized",
            request=MagicMock(),
            response=MagicMock(),
        )

        with (
            patch(
                "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
                return_value=response,
            ),
            pytest.raises(httpx.HTTPStatusError),
        ):
            search.run(query="haystack")


class TestXquikUserTweetsFetcher:
    def test_run_passes_path_and_params(self) -> None:
        fetcher = XquikUserTweetsFetcher(api_key=Secret.from_token("xq_test"), include_replies=True)

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
            return_value=_mock_response(TWEETS_RESPONSE),
        ) as mock_request:
            result = fetcher.run(user_id="xquik/com", cursor="cursor-0", include_parent_tweet=True)

        assert mock_request.call_args.kwargs["url"] == "https://xquik.com/api/v1/x/users/xquik%2Fcom/tweets"
        assert mock_request.call_args.kwargs["params"] == {
            "includeReplies": True,
            "includeParentTweet": True,
            "cursor": "cursor-0",
        }
        assert result["documents"][0].meta["endpoint"] == "x.users.tweets"
        assert result["has_more"] is True

    @pytest.mark.asyncio
    async def test_run_async(self) -> None:
        fetcher = XquikUserTweetsFetcher(api_key=Secret.from_token("xq_test"))

        with patch(
            "haystack_integrations.components.websearch.xquik.xquik_websearch.async_request_with_retry",
            new_callable=AsyncMock,
            return_value=_mock_response(TWEETS_RESPONSE),
        ):
            result = await fetcher.run_async(user_id="xquikcom")

        assert len(result["documents"]) == 1
        assert result["links"] == ["https://x.com/example/status/123"]
