# Retrieve X/Twitter Context with Haystack

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

Retrieve public X/Twitter context through Xquik.

[Read the Xquik Haystack guide](https://docs.xquik.com/guides/haystack).

Import both read-only components from the Haystack integration namespace:

```python
from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
```

## Available Components

- `XquikTweetSearch`: calls `GET /x/tweets/search` and returns matching posts as Haystack `Document` objects.
- `XquikUserTweetsFetcher`: calls `GET /x/users/{id}/tweets` and returns recent public posts for a user as Haystack `Document` objects.

Both components:

- Read `XQUIK_API_KEY` by default.
- Accept `haystack.utils.Secret` for explicit keys.
- Send `x-api-key` and `xquik-api-contract: 2026-04-29`.
- Allow a custom `base_url` for controlled deployments.
- Return `documents`, `links`, `has_more`, and `next_cursor`.

## Install

Install from PyPI:

```bash
pip install xquik-haystack
```

## Search Public X Data

### Search Posts

```python
from haystack import Pipeline
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikTweetSearch

search = XquikTweetSearch(api_key=Secret.from_env_var("XQUIK_API_KEY"), top_k=10)

pipeline = Pipeline()
pipeline.add_component("x_search", search)

result = pipeline.run({"x_search": {"query": "haystack ai"}})
documents = result["x_search"]["documents"]
```

### Fetch User Posts

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikUserTweetsFetcher

fetcher = XquikUserTweetsFetcher(api_key=Secret.from_env_var("XQUIK_API_KEY"))

result = fetcher.run(user_id="example_user", include_replies=False)
documents = result["documents"]
```

## Document Mapping

Each tweet becomes a Haystack `Document`.

- `Document.content`: tweet text, or an empty string when text is missing
- `Document.meta["endpoint"]`: Xquik endpoint family used by the component
- `Document.meta["id"]`: tweet ID when present
- `Document.meta["url"]`: tweet URL when present
- `Document.meta["created_at"]`: tweet creation time when present
- `Document.meta["author"]`: author ID, username, display name, and verification status when present
- `Document.meta` also includes available public metrics such as like, repost, reply, quote, view, and bookmark counts

## Development

This project uses [Hatch](https://hatch.pypa.io/) for build and environment management.

```bash
pip install hatch
hatch run fmt-check
hatch run test:unit
hatch build
```

Unit tests mock all Xquik HTTP calls.

## License

`xquik-haystack` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
