# Xquik Haystack

Haystack web search components for retrieving public X/Twitter context through the Xquik REST API.

This package is maintained by Xquik as a standalone Haystack integration. It follows the `haystack_integrations` namespace convention and exposes read-only components under:

```python
from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
```

## Components

- `XquikTweetSearch`: calls `GET /x/tweets/search` and returns matching posts as Haystack `Document` objects.
- `XquikUserTweetsFetcher`: calls `GET /x/users/{id}/tweets` and returns recent public posts for a user as Haystack `Document` objects.

Both components:

- read the API key from `XQUIK_API_KEY` by default
- accept `haystack.utils.Secret` for explicit API key injection
- send the `x-api-key` and `xquik-api-contract: 2026-04-29` headers
- keep `base_url` configurable for tests and controlled deployments
- return `documents`, `links`, `has_more`, and `next_cursor`

## Installation

Install the current repository build:

```bash
pip install git+https://github.com/Xquik-dev/xquik-haystack.git
```

After the first PyPI release:

```bash
pip install xquik-haystack
```

## Usage

### Tweet Search

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

### User Tweets

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikUserTweetsFetcher

fetcher = XquikUserTweetsFetcher(api_key=Secret.from_env_var("XQUIK_API_KEY"))

result = fetcher.run(user_id="xquikcom", include_replies=False)
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

Unit tests mock all Xquik HTTP calls. Integration tests can be added later behind an `XQUIK_API_KEY` check.

## Publishing

The release workflow publishes to PyPI when a version tag is pushed and the repository has a `PYPI_API_TOKEN` Actions secret.

```bash
git tag v0.1.0
git push origin v0.1.0
```

After a first PyPI version is published, submit a listing PR to [`deepset-ai/haystack-integrations`](https://github.com/deepset-ai/haystack-integrations) as requested by the Haystack maintainers.

## License

`xquik-haystack` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.
