# X (Twitter) Dataset Components for Haystack RAG by Xquik

Use these Haystack components by Xquik to build an X (Twitter) dataset for RAG.
Each post becomes a Haystack `Document` with its text & metadata.

Xquik is the world's fastest and cheapest X (Twitter) scraper service with the most complete X (Twitter) data.
Most other Apify Actors charge before filtering or deduplication.
Xquik charges only for delivered, unique, filter-matching results and never pads rows.
Xquik is independent and not affiliated with X Corp.

<!-- trust:win:start -->

The Xquik REST API read 45 tweets per second on 2026-10-15. That cost $0.15 per 1,000. The fastest of 4 rival Actors read 12.5 per second. The cheapest cost $0.173 per 1,000. [Compare each run](https://xquik.com/benchmarks#benchmark-x-tweet-scraper).

<!-- trust:win:end -->

## Install the Haystack X (Twitter) components

The package needs Python 3.10 or newer.

```bash
pip install xquik-haystack
```

Copy a key from [your Xquik account](https://dashboard.xquik.com/en/account?tab=api-keys), then set it in your shell.

```bash
export XQUIK_API_KEY=xq_your_key
```

## Build an X (Twitter) dataset for RAG

Each `Document` in `dataset` is ready to embed & store.

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikTweetSearch

search = XquikTweetSearch(api_key=Secret.from_env_var("XQUIK_API_KEY"), top_k=10)

dataset = search.run(query="haystack ai")["documents"]
```

Next, read the [Xquik Haystack guide](https://docs.xquik.com/guides/haystack), the [component table](#components) or the [document mapping](#document-mapping).

<!-- trust:start -->

## Benchmarks & usage

[![xquik-haystack downloads on PyPI](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Fpypi-xquik-haystack.json)](https://pypistats.org/packages/xquik-haystack)
[![X (Twitter) API p99 server read time](https://img.shields.io/endpoint?url=https%3A%2F%2Fxquik.com%2Fbadges%2Frest-p99.json)](https://xquik.com/benchmarks#speed)
[![OpenSSF Best Practices](https://www.bestpractices.dev/projects/13741/badge)](https://www.bestpractices.dev/projects/13741)

- 1,000+ downloads of xquik-haystack on PyPI ([source](https://pypistats.org/packages/xquik-haystack)) <!-- trust:pypi-xquik-haystack 1076 -->
- 5.4 s p99 REST server read time over 7 days, failures included ([source](https://xquik.com/benchmarks#speed)) <!-- trust:rest-p99 5312 -->
- This repo meets the OpenSSF Best Practices passing criteria ([source](https://www.bestpractices.dev/projects/13741)) <!-- trust:openssf-xquik-haystack 1 -->

Checked on 2026-11-08. See each number with its date & source on [xquik.com/benchmarks](https://xquik.com/benchmarks) or as [JSON](https://xquik.com/trust.json).

<!-- trust:end -->

## Components

| Task | Haystack component | Xquik route | Output |
| --- | --- | --- | --- |
| Search tweets for RAG | `XquikTweetSearch` | `GET /x/tweets/search` | Matching posts as `Document` objects |
| Retrieve a user's timeline | `XquikUserTweetsFetcher` | `GET /x/users/{id}/tweets` | Recent user posts as `Document` objects |

Import both read-only components from the Haystack integration namespace.

```python
from haystack_integrations.components.websearch.xquik import XquikTweetSearch, XquikUserTweetsFetcher
```

Both components read `XQUIK_API_KEY` by default and accept a Haystack `Secret`.
They send `x-api-key` and `xquik-api-contract: 2026-04-29` headers.
Results include `documents`, `links`, `has_more` & `next_cursor`.

Use an [Xquik SDK](https://docs.xquik.com/sdks) for follower exports or posting.

## Search tweets in a Haystack pipeline

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

## Fetch user posts

```python
from haystack.utils import Secret
from haystack_integrations.components.websearch.xquik import XquikUserTweetsFetcher

fetcher = XquikUserTweetsFetcher(api_key=Secret.from_env_var("XQUIK_API_KEY"))

result = fetcher.run(user_id="example_user", include_replies=False)
documents = result["documents"]
```

## Document mapping

Each tweet becomes a Haystack `Document` with this mapping.

- `Document.content` holds the tweet text, or an empty string when text is missing.
- `Document.meta["endpoint"]` names the Xquik endpoint family the component used.
- `Document.meta` holds the available `id`, `url` & `created_at` source values.
- `Document.meta["author"]` holds the available author identity & verification data.
- `Document.meta` holds the available like, repost, reply, quote, view & bookmark counts.

## Questions

### Do I need an X (Twitter) developer account?

No. Public reads need only an Xquik API key.
Private reads & account actions need a connected X (Twitter) account.

### Is this the official X (Twitter) API?

No. Xquik runs its own REST API.
This package calls that API, not the official X (Twitter) API.

## More Xquik tools

- [X (Twitter) scraper API & MCP server](https://github.com/Xquik-dev/x-twitter-scraper) with REST, MCP & Skill setup.
- X (Twitter) API SDKs for [TypeScript](https://github.com/Xquik-dev/x-twitter-scraper-typescript), [Python](https://github.com/Xquik-dev/x-twitter-scraper-python), [Go](https://github.com/Xquik-dev/x-twitter-scraper-go), [Ruby](https://github.com/Xquik-dev/x-twitter-scraper-ruby), [Java](https://github.com/Xquik-dev/x-twitter-scraper-java), [Kotlin](https://github.com/Xquik-dev/x-twitter-scraper-kotlin), [C#](https://github.com/Xquik-dev/x-twitter-scraper-csharp) & [PHP](https://github.com/Xquik-dev/x-twitter-scraper-php).
- [X (Twitter) CLI](https://github.com/Xquik-dev/x-twitter-scraper-cli) for terminal workflows.
- The [X (Twitter) API alternative skill](https://github.com/Xquik-dev/x-api) & [X (Twitter) advanced search operators](https://github.com/Xquik-dev/x-twitter-advanced-search).
- X (Twitter) agent plugins for [OpenClaw](https://github.com/Xquik-dev/tweetclaw) & [Hermes Agent](https://github.com/Xquik-dev/hermes-tweet).
- The [X (Twitter) API documentation source](https://github.com/Xquik-dev/xquik-docs).
- X (Twitter) integrations for [n8n](https://github.com/Xquik-dev/n8n-nodes-xquik), [Prefect](https://github.com/Xquik-dev/prefect-xquik), [Paperclip](https://github.com/Xquik-dev/paperclip-plugin-xquik), [Terraform](https://github.com/Xquik-dev/terraform-provider-x-twitter-scraper), [Convex](https://github.com/Xquik-dev/xquik-convex), [Supabase](https://github.com/Xquik-dev/xquik-supabase) & [Strapi](https://github.com/Xquik-dev/strapi-plugin-xquik).
- X (Twitter) MCP for [AI agents](https://github.com/Xquik-dev/xquik-mcp), [VS Code](https://github.com/Xquik-dev/xquik-vscode) & [Raycast](https://github.com/Xquik-dev/xquik-raycast).
- [Xquik X (Twitter) API & scraper](https://xquik.com) and the [X (Twitter) API documentation](https://docs.xquik.com/api-reference/overview).

## Develop

Use [Hatch](https://hatch.pypa.io/) for builds and environment management.

```bash
pip install hatch==1.18.0
hatch run fmt-check
hatch run test:types
hatch run test:unit
hatch build
```

Unit tests mock all Xquik HTTP calls.
Run `bin/check-local` before you open a pull request.

## Help & contributing

- Ask usage questions through the [organization support policy](https://github.com/Xquik-dev/.github/blob/main/SUPPORT.md).
- Report vulnerabilities through the [organization security policy](https://github.com/Xquik-dev/.github/blob/main/SECURITY.md).
- Read the [contribution guide](https://github.com/Xquik-dev/.github/blob/main/CONTRIBUTING.md).

## License

`xquik-haystack` uses the [Apache-2.0](https://spdx.org/licenses/Apache-2.0.html) license.

Xquik is an independent third-party service. Not affiliated with X Corp. "Twitter" and "X" are trademarks of X Corp.
