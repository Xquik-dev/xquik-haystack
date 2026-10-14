# Twitter search & user timeline components for Haystack

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

Search Twitter and fetch public user timelines in Haystack RAG pipelines.
Each Xquik result becomes a Haystack `Document`.

Xquik is the world's fastest and cheapest X Twitter scraper service with the most complete X data.
Xquik charges only for delivered, unique, filter-matching results and never pads rows.

[Read the Xquik Haystack guide](https://docs.xquik.com/guides/haystack).

## Components

| Task | Haystack Component | Xquik Route | Output |
| --- | --- | --- | --- |
| Search tweets for RAG | `XquikTweetSearch` | `GET /x/tweets/search` | Matching posts as `Document` objects |
| Retrieve a user's timeline | `XquikUserTweetsFetcher` | `GET /x/users/{id}/tweets` | Recent user posts as `Document` objects |

Import both read-only components from the Haystack integration namespace.

```python
from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
```

Both components read `XQUIK_API_KEY` by default and accept a Haystack `Secret`.
They send `x-api-key` and `xquik-api-contract: 2026-04-29` headers.
Set `base_url` for another Xquik-compatible endpoint. Results include `documents`, `links`,
`has_more`, and `next_cursor`.

Use an [Xquik SDK](https://docs.xquik.com/sdks) for follower exports or posting.

## Install

```bash
pip install xquik-haystack
```

## Build a Haystack RAG pipeline with Twitter search

### Search posts

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

### Fetch user posts

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikUserTweetsFetcher

fetcher = XquikUserTweetsFetcher(api_key=Secret.from_env_var("XQUIK_API_KEY"))

result = fetcher.run(user_id="example_user", include_replies=False)
documents = result["documents"]
```

## Document mapping

Each tweet becomes a Haystack `Document` with this mapping.

- `Document.content` holds the tweet text, or an empty string when text is
  missing.
- `Document.meta["endpoint"]` names the Xquik endpoint family the component
  used.
- `Document.meta` holds the available `id`, `url`, and `created_at` source
  values.
- `Document.meta["author"]` holds the available author identity and
  verification data.
- `Document.meta` holds the available like, repost, reply, quote, view &
  bookmark counts.

## Development

Use [Hatch](https://hatch.pypa.io/) for builds and environment management.

```bash
pip install hatch==1.18.0
hatch run fmt-check
hatch run test:unit
hatch build
```

Unit tests mock all Xquik HTTP calls.

Run `bin/check-local` before you open a pull request. It runs the lint, license, test & CodeQL checks.

Maintainers release with `bin/release-local <version>` on a clean `main`. It runs the checks, builds, uploads to PyPI, tags the commit and creates the GitHub release. `bin/release-local --dry-run <version>` uploads, tags and releases nothing.

PyPI has no trusted publisher for `xquik-haystack`. A maintainer's PyPI token is the only way it publishes. `bin/release-local` reads it from the Keychain item that `PYPI_KEYCHAIN_SERVICE` names.

## Support & project policies

- [Organization support policy](https://github.com/Xquik-dev/.github/blob/main/SUPPORT.md)
- [Organization security policy](https://github.com/Xquik-dev/.github/blob/main/SECURITY.md)
- [Contribution guide](https://github.com/Xquik-dev/.github/blob/main/CONTRIBUTING.md)

## More Xquik tools

- [X (Twitter) scraper API & Twitter MCP server](https://github.com/Xquik-dev/x-twitter-scraper) with REST, MCP & Skill setup.
- Twitter API SDKs for [TypeScript](https://github.com/Xquik-dev/x-twitter-scraper-typescript), [Python](https://github.com/Xquik-dev/x-twitter-scraper-python), [Go](https://github.com/Xquik-dev/x-twitter-scraper-go), [Ruby](https://github.com/Xquik-dev/x-twitter-scraper-ruby), [Java](https://github.com/Xquik-dev/x-twitter-scraper-java), [Kotlin](https://github.com/Xquik-dev/x-twitter-scraper-kotlin), [C#](https://github.com/Xquik-dev/x-twitter-scraper-csharp) & [PHP](https://github.com/Xquik-dev/x-twitter-scraper-php).
- [Twitter CLI & X CLI](https://github.com/Xquik-dev/x-twitter-scraper-cli) for terminal workflows.
- [Twitter advanced search operators](https://github.com/Xquik-dev/x-twitter-advanced-search) with tested examples.
- [Xquik X API & Twitter scraper](https://xquik.com) and the [Twitter API documentation](https://docs.xquik.com/api-reference/overview).

## License

`xquik-haystack` is distributed under the terms of the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
