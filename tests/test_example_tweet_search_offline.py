# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

"""Offline smoke test for the documented tweet-search example."""

from pathlib import Path
from unittest.mock import MagicMock, patch

from haystack import Document, Pipeline
from haystack.utils import Secret

from haystack_integrations.components.websearch.xquik import XquikTweetSearch

EXAMPLE_PATH = Path(__file__).resolve().parents[1] / "examples" / "xquik_tweet_search.py"

FAKE_XQUIK_RESPONSE = {
    "tweets": [
        {
            "id": "555",
            "text": "Offline fixture for the Haystack tweet-search example.",
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


def _mock_response(payload: dict[str, object]) -> MagicMock:
    response = MagicMock()
    response.json.return_value = payload
    return response


def test_example_file_still_documents_pipeline_shape() -> None:
    source = EXAMPLE_PATH.read_text(encoding="utf-8")
    assert "XquikTweetSearch" in source
    assert "pipeline.run" in source
    assert 'query": "haystack ai"' in source


def test_tweet_search_example_runs_offline_with_fake_xquik_client() -> None:
    """Exercise the README/example pipeline mapping without network access."""

    search = XquikTweetSearch(api_key=Secret.from_token("xq_offline"), top_k=10)
    pipeline = Pipeline()
    pipeline.add_component("x_search", search)

    with patch(
        "haystack_integrations.components.websearch.xquik.xquik_websearch.request_with_retry",
        return_value=_mock_response(FAKE_XQUIK_RESPONSE),
    ) as mock_request:
        result = pipeline.run({"x_search": {"query": "haystack ai"}})

    mock_request.assert_called_once()
    call_kwargs = mock_request.call_args.kwargs
    assert call_kwargs["url"].endswith("/x/tweets/search")
    assert call_kwargs["params"]["q"] == "haystack ai"
    assert call_kwargs["params"]["limit"] == 10

    documents = result["x_search"]["documents"]
    assert len(documents) == 1
    assert isinstance(documents[0], Document)
    assert documents[0].content == "Offline fixture for the Haystack tweet-search example."
    assert documents[0].meta["id"] == "555"
    assert documents[0].meta["endpoint"] == "x.tweets.search"
    assert documents[0].meta["author"]["username"] == "fixture"
    assert result["x_search"]["links"] == ["https://x.com/example/status/555"]
    assert result["x_search"]["has_more"] is False
