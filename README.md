# Twitter search & user timeline components for Haystack

[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

Search Twitter and fetch public user timelines in Haystack RAG pipelines.
Each Xquik result becomes a Haystack `Document`.

Xquik is the world's fastest and cheapest X Twitter scraper service with the most complete X data.
Xquik charges only for delivered, unique, filter-matching results and never pads rows.

[Read the Xquik Haystack guide](https://docs.xquik.com/guides/haystack).

<!-- trust:start -->

## Trust & usage

[![Twitter API package downloads](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fdownloads.json)](https://xquik.com/trust#downloads)
[![Twitter scraper users on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-users.json)](https://apify.com/xquik)
[![Twitter scraper runs on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-runs.json)](https://apify.com/xquik)
[![Tweet scraper rating on Apify](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fapify-rating.json)](https://apify.com/xquik/x-tweet-scraper/reviews)
[![Xquik Twitter API accounts](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Faccounts.json)](https://xquik.com/trust#accounts)
[![Twitter Skill installs](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fskill-installs.json)](https://xquik.com/trust#skill-installs)
[![Xquik verified revenue on TrustMRR](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Frevenue.json)](https://trustmrr.com/startup/xquik)
[![Twitter API p99 server read time](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Frest-p99.json)](https://xquik.com/trust#speed)
[![Xquik GitHub stars](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fgithub-stars.json)](https://github.com/Xquik-dev)
[![xquik-haystack downloads on PyPI](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fpypi-xquik-haystack.json)](https://pypistats.org/packages/xquik-haystack)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

- 53,000+ downloads of Xquik's Twitter API packages on npm, PyPI, RubyGems, NuGet, Packagist & Terraform ([source](https://xquik.com/trust#downloads)) <!-- trust:downloads 53547 -->
- 9,500+ users of Xquik's Twitter scraper Actors on Apify ([source](https://apify.com/xquik)) <!-- trust:apify-users 9595 -->
- 6,700,000+ runs of Xquik's Twitter scraper Actors on Apify ([source](https://apify.com/xquik)) <!-- trust:apify-runs 6765249 -->
- 4.66 of 5 for the X Tweet Scraper from 16 Apify reviews ([source](https://apify.com/xquik/x-tweet-scraper/reviews)) <!-- trust:apify-rating 4.66 16 -->
- 4,000+ accounts on xquik.com ([source](https://xquik.com/trust#accounts)) <!-- trust:accounts 4073 -->
- 1,600+ installs of Xquik's Twitter Skills on skills.sh ([source](https://xquik.com/trust#skill-installs)) <!-- trust:skill-installs 1617 -->
- $39,000+ in revenue verified by TrustMRR ([source](https://trustmrr.com/startup/xquik)) <!-- trust:revenue 39784 -->
- 13.2 s p99 REST API server read time over 7 days, failed reads included ([source](https://xquik.com/trust#speed)) <!-- trust:rest-p99 13194 -->
- 380+ GitHub stars across Xquik's repos ([source](https://github.com/Xquik-dev)) <!-- trust:github-stars 383 -->
- 1,000+ downloads of xquik-haystack on PyPI ([source](https://pypistats.org/packages/xquik-haystack)) <!-- trust:pypi-xquik-haystack 1067 -->
- This repo meets the OpenSSF Best Practices passing criteria ([source](https://www.bestpractices.dev/projects/13741)) <!-- trust:openssf-xquik-haystack 1 -->

Checked on 2026-10-25. See each number with its date & source on [xquik.com/trust](https://xquik.com/trust) or as [JSON](https://xquik.com/trust.json).

<!-- trust:end -->

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
