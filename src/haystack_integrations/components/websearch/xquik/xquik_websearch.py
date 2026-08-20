# SPDX-FileCopyrightText: 2026-present Xquik <support@xquik.com>
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Literal
from urllib.parse import quote

from haystack import Document, component, logging
from haystack.utils import Secret
from haystack.utils.requests_utils import async_request_with_retry, request_with_retry

logger = logging.getLogger(__name__)

XQUIK_API_URL = "https://xquik.com/api/v1"
XQUIK_API_CONTRACT = "2026-04-29"

QueryType = Literal["Latest", "Top"]
JsonObject = Mapping[str, Any]


@component
class XquikTweetSearch:
    """
    Search public Twitter posts and return Haystack Documents.

    Calls `GET /x/tweets/search` with the current Xquik response contract.
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var("XQUIK_API_KEY"),
        top_k: int | None = 20,
        query_type: QueryType = "Latest",
        base_url: str = XQUIK_API_URL,
        extra_params: dict[str, Any] | None = None,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Create a tweet search component.

        :param api_key:
            Xquik API key. Defaults to `XQUIK_API_KEY`.
        :param top_k:
            Maximum tweets requested through the Xquik `limit` parameter.
        :param query_type:
            Search order. `Latest` sorts by time; `Top` sorts by engagement.
        :param base_url:
            Xquik API base URL.
        :param extra_params:
            Extra tweet search query parameters.
        :param timeout:
            Request timeout in seconds.
        :param max_retries:
            Retries for transient request failures.
        """
        self.api_key = api_key
        self.top_k = top_k
        self.query_type = query_type
        self.base_url = base_url.rstrip("/")
        self.extra_params = extra_params
        self.timeout = timeout
        self.max_retries = max_retries

    @component.output_types(documents=list[Document], links=list[str], has_more=bool, next_cursor=str | None)
    def run(
        self,
        query: str,
        top_k: int | None = None,
        query_type: QueryType | None = None,
        cursor: str | None = None,
        since_time: str | None = None,
        until_time: str | None = None,
    ) -> dict[str, Any]:
        """
        Search public tweets.

        :param query:
            Twitter search query, including supported operators.
        :param top_k:
            Maximum tweets for this run.
        :param query_type:
            Search order for this run.
        :param cursor:
            Pagination cursor from the previous response.
        :param since_time:
            ISO 8601 creation-time lower bound.
        :param until_time:
            ISO 8601 creation-time upper bound.
        :returns:
            Haystack Documents, links & pagination data.
        """
        params = self._build_params(
            query=query,
            top_k=top_k,
            query_type=query_type,
            cursor=cursor,
            since_time=since_time,
            until_time=until_time,
        )
        response = request_with_retry(
            attempts=self.max_retries,
            method="GET",
            url=f"{self.base_url}/x/tweets/search",
            params=params,
            headers=_build_headers(self.api_key),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_tweets_response(response.json(), endpoint="x.tweets.search")

    @component.output_types(documents=list[Document], links=list[str], has_more=bool, next_cursor=str | None)
    async def run_async(
        self,
        query: str,
        top_k: int | None = None,
        query_type: QueryType | None = None,
        cursor: str | None = None,
        since_time: str | None = None,
        until_time: str | None = None,
    ) -> dict[str, Any]:
        """
        Search public tweets asynchronously.

        :param query:
            Twitter search query, including supported operators.
        :param top_k:
            Maximum tweets for this run.
        :param query_type:
            Search order for this run.
        :param cursor:
            Pagination cursor from the previous response.
        :param since_time:
            ISO 8601 creation-time lower bound.
        :param until_time:
            ISO 8601 creation-time upper bound.
        :returns:
            Haystack Documents, links & pagination data.
        """
        params = self._build_params(
            query=query,
            top_k=top_k,
            query_type=query_type,
            cursor=cursor,
            since_time=since_time,
            until_time=until_time,
        )
        response = await async_request_with_retry(
            attempts=self.max_retries,
            method="GET",
            url=f"{self.base_url}/x/tweets/search",
            params=params,
            headers=_build_headers(self.api_key),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_tweets_response(response.json(), endpoint="x.tweets.search")

    def _build_params(
        self,
        query: str,
        *,
        top_k: int | None,
        query_type: QueryType | None,
        cursor: str | None,
        since_time: str | None,
        until_time: str | None,
    ) -> dict[str, Any]:
        effective_top_k = self.top_k if top_k is None else top_k
        effective_query_type = self.query_type if query_type is None else query_type
        params: dict[str, Any] = {"q": query, "queryType": effective_query_type}
        if effective_top_k is not None:
            params["limit"] = effective_top_k
        if cursor is not None:
            params["cursor"] = cursor
        if since_time is not None:
            params["sinceTime"] = since_time
        if until_time is not None:
            params["untilTime"] = until_time
        if self.extra_params:
            params.update(self.extra_params)
        return params


@component
class XquikUserTweetsFetcher:
    """
    Fetch a public Twitter user timeline as Haystack Documents.

    Calls `GET /x/users/{id}/tweets` with an X user ID or username.
    """

    def __init__(
        self,
        api_key: Secret = Secret.from_env_var("XQUIK_API_KEY"),
        include_replies: bool = False,
        include_parent_tweet: bool = False,
        base_url: str = XQUIK_API_URL,
        timeout: int = 10,
        max_retries: int = 3,
    ) -> None:
        """
        Create a user timeline fetcher.

        :param api_key:
            Xquik API key. Defaults to `XQUIK_API_KEY`.
        :param include_replies:
            Include replies in the timeline.
        :param include_parent_tweet:
            Include available parent tweet data.
        :param base_url:
            Xquik API base URL.
        :param timeout:
            Request timeout in seconds.
        :param max_retries:
            Retries for transient request failures.
        """
        self.api_key = api_key
        self.include_replies = include_replies
        self.include_parent_tweet = include_parent_tweet
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

    @component.output_types(documents=list[Document], links=list[str], has_more=bool, next_cursor=str | None)
    def run(
        self,
        user_id: str,
        cursor: str | None = None,
        include_replies: bool | None = None,
        include_parent_tweet: bool | None = None,
    ) -> dict[str, Any]:
        """
        Fetch recent public tweets from one user.

        :param user_id:
            X user ID or username.
        :param cursor:
            Pagination cursor from the previous response.
        :param include_replies:
            Include replies for this run.
        :param include_parent_tweet:
            Include parent tweet data for this run.
        :returns:
            Haystack Documents, links & pagination data.
        """
        params = self._build_params(
            cursor=cursor,
            include_replies=include_replies,
            include_parent_tweet=include_parent_tweet,
        )
        response = request_with_retry(
            attempts=self.max_retries,
            method="GET",
            url=f"{self.base_url}/x/users/{quote(user_id, safe='')}/tweets",
            params=params,
            headers=_build_headers(self.api_key),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_tweets_response(response.json(), endpoint="x.users.tweets")

    @component.output_types(documents=list[Document], links=list[str], has_more=bool, next_cursor=str | None)
    async def run_async(
        self,
        user_id: str,
        cursor: str | None = None,
        include_replies: bool | None = None,
        include_parent_tweet: bool | None = None,
    ) -> dict[str, Any]:
        """
        Fetch recent public tweets asynchronously.

        :param user_id:
            X user ID or username.
        :param cursor:
            Pagination cursor from the previous response.
        :param include_replies:
            Include replies for this run.
        :param include_parent_tweet:
            Include parent tweet data for this run.
        :returns:
            Haystack Documents, links & pagination data.
        """
        params = self._build_params(
            cursor=cursor,
            include_replies=include_replies,
            include_parent_tweet=include_parent_tweet,
        )
        response = await async_request_with_retry(
            attempts=self.max_retries,
            method="GET",
            url=f"{self.base_url}/x/users/{quote(user_id, safe='')}/tweets",
            params=params,
            headers=_build_headers(self.api_key),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return _parse_tweets_response(response.json(), endpoint="x.users.tweets")

    def _build_params(
        self,
        *,
        cursor: str | None,
        include_replies: bool | None,
        include_parent_tweet: bool | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {
            "includeReplies": self.include_replies if include_replies is None else include_replies,
            "includeParentTweet": self.include_parent_tweet if include_parent_tweet is None else include_parent_tweet,
        }
        if cursor is not None:
            params["cursor"] = cursor
        return params


def _build_headers(api_key: Secret) -> dict[str, str]:
    return {
        "Accept": "application/json",
        "x-api-key": api_key.resolve_value() or "",
        "xquik-api-contract": XQUIK_API_CONTRACT,
    }


def _parse_tweets_response(response: JsonObject, endpoint: str) -> dict[str, Any]:
    documents: list[Document] = []
    links: list[str] = []

    tweets = _as_list(_get(response, "tweets", "data", default=[]))
    for tweet in tweets:
        if not isinstance(tweet, Mapping):
            continue
        document = _tweet_to_document(tweet, endpoint=endpoint)
        documents.append(document)
        url = document.meta.get("url")
        if isinstance(url, str) and url:
            links.append(url)

    has_more = bool(_get(response, "has_more", "has_next_page", "hasMore", default=False))
    next_cursor = _as_optional_string(_get(response, "next_cursor", "nextCursor", default=None))
    return {"documents": documents, "links": links, "has_more": has_more, "next_cursor": next_cursor}


def _tweet_to_document(tweet: JsonObject, endpoint: str) -> Document:
    content = _as_optional_string(_get(tweet, "text", "full_text", "content", default="")) or ""
    meta: dict[str, Any] = {"endpoint": endpoint}
    for key, aliases in {
        "id": ("id",),
        "url": ("url",),
        "created_at": ("created_at", "createdAt"),
        "lang": ("lang",),
        "conversation_id": ("conversation_id", "conversationId"),
        "in_reply_to_id": ("in_reply_to_id", "inReplyToId"),
        "in_reply_to_user_id": ("in_reply_to_user_id", "inReplyToUserId"),
        "in_reply_to_username": ("in_reply_to_username", "inReplyToUsername"),
        "is_reply": ("is_reply", "isReply"),
        "is_quote_status": ("is_quote_status", "isQuoteStatus"),
        "like_count": ("like_count", "likeCount"),
        "retweet_count": ("retweet_count", "retweetCount"),
        "reply_count": ("reply_count", "replyCount"),
        "quote_count": ("quote_count", "quoteCount"),
        "view_count": ("view_count", "viewCount"),
        "bookmark_count": ("bookmark_count", "bookmarkCount"),
    }.items():
        value = _get(tweet, *aliases, default=None)
        if value is not None:
            meta[key] = value

    author = _get(tweet, "author", "user", default=None)
    if isinstance(author, Mapping):
        meta["author"] = _compact(
            {
                "id": _get(author, "id", default=None),
                "username": _get(author, "username", "screen_name", default=None),
                "name": _get(author, "name", default=None),
                "verified": _get(author, "verified", default=None),
            }
        )

    return Document(content=content, meta=meta)


def _get(data: JsonObject, *keys: str, default: Any) -> Any:
    for key in keys:
        if key in data:
            return data[key]
    return default


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    return []


def _as_optional_string(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def _compact(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value is not None}
