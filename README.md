# Haystack Twitter Search & User Timeline Components

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

Add Twitter search and public user timelines to Haystack RAG pipelines.
Xquik returns each post as a Haystack `Document`.

[Read the Xquik Haystack guide](https://docs.xquik.com/guides/haystack).

## Choose a Component

| Task | Haystack Component | Xquik Route | Output |
| --- | --- | --- | --- |
| Search tweets for RAG | `XquikTweetSearch` | `GET /x/tweets/search` | Matching posts as `Document` objects |
| Retrieve a user's timeline | `XquikUserTweetsFetcher` | `GET /x/users/{id}/tweets` | Recent user posts as `Document` objects |

Import both read-only components from the Haystack integration namespace.

```python
from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
```

Each component:

- Reads `XQUIK_API_KEY` by default.
- Accepts `haystack.utils.Secret` for explicit keys.
- Sends `x-api-key` and `xquik-api-contract: 2026-04-29`.
- Accepts a custom `base_url` for controlled deployments.
- Returns `documents`, `links`, `has_more`, and `next_cursor`.

Use an [Xquik SDK](https://docs.xquik.com/sdks) for follower exports or posting.

## Install

```bash
pip install xquik-haystack
```

## Build Haystack RAG With Twitter Search

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

Each tweet becomes a Haystack `Document` with this mapping.

- `Document.content`: tweet text, or an empty string when text is missing
- `Document.meta["endpoint"]`: Xquik endpoint family used by the component
- `Document.meta["id"]`: tweet ID when present
- `Document.meta["url"]`: tweet URL when present
- `Document.meta["created_at"]`: creation time when present
- `Document.meta["author"]`: available author identity and verification data
- `Document.meta`: available like, repost, reply, quote, view & bookmark counts

## Development

This project uses [Hatch](https://hatch.pypa.io/) for build and environment management.

```bash
pip install hatch==1.18.0
hatch run fmt-check
hatch run test:unit
hatch build
```

Unit tests mock all Xquik HTTP calls.

## Support & Project Policies

- [Organization support policy](https://github.com/Xquik-dev/.github/blob/main/SUPPORT.md)
- [Organization security policy](https://github.com/Xquik-dev/.github/blob/main/SECURITY.md)
- [Contribution guide](https://github.com/Xquik-dev/.github/blob/main/CONTRIBUTING.md)

## License

`xquik-haystack` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
