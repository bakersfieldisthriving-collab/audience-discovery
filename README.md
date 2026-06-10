# Audience Discovery

Audience Discovery is an MVP Python tool for finding and organizing public sponsorship-ready audience prospects for paid promotion research.

The current implementation is intentionally conservative. It only works with public URLs and public sponsor, advertise, media-kit, business inquiry, contact page, or explicitly published email information. It does not auto-send outreach.

## Compliance Limitations

- Do not scrape private communities, private Discord servers, logins, paywalls, or hidden data.
- Do not bypass platform restrictions.
- Only collect public business, sponsor, advertise, media-kit, or contact information.
- Respect `robots.txt` where page fetching is implemented.
- Every exported lead includes source URLs.
- Missing fields are set to `unknown`; the tool should not invent facts.
- Leads require manual review before any outreach.
- Review queue exports are a triage aid, not an approval to contact.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

## Environment Variables

- `OPENAI_API_KEY`: optional. If missing, deterministic local classification and scoring are used.
- `OPENAI_MODEL`: optional. Defaults to `gpt-4.1-mini` when OpenAI classification is used.
- `SERPAPI_API_KEY`: required for real Google search through SerpAPI.
- `YOUTUBE_API_KEY`: optional. The MVP includes a non-scraping YouTube provider skeleton; API search is not implemented yet.

## Example Commands

```powershell
python -m audience_discovery.main --dry-run --limit 10
python -m audience_discovery.main --category longevity_communities --limit 25
python -m audience_discovery.main --provider serpapi --category biohacking_newsletters --limit 100
python -m audience_discovery.main --export-only
```

By default, the CLI uses deterministic mock search results. With `--provider serpapi`, it searches Google through SerpAPI using the configured category seed queries, deduplicates results by URL and domain, then feeds results into the existing fetch, classify, score, SQLite, and CSV export workflow.

Without `--dry-run`, the CLI attempts to fetch public result URLs, checks `robots.txt`, rate limits requests, and extracts public page text, links, sponsor signals, and contact signals.

## Outputs

CSV exports are written to `outputs/`:

- `leads_raw.csv`: all stored leads.
- `leads_scored.csv`: all stored leads sorted by score.
- `leads_review_queue.csv`: leads with `fit_score >= 60`, `sponsorship_probability >= 50`, `compliance_risk != high`, `sponsor_signal != none`, and non-directory/non-article lead types. The review queue is sorted by `sponsorship_probability` descending.

SQLite storage is written to `outputs/leads.sqlite` by default.

## CSV Fields

- `entity_name`
- `category`
- `platform`
- `url`
- `domain`
- `audience_type`
- `audience_description`
- `audience_size_estimate`
- `lead_type`
- `sponsor_signal`
- `contact_method`
- `public_contact`
- `fit_score`
- `sponsorship_probability`
- `compliance_risk`
- `fit_reason`
- `outreach_angle`
- `source_urls`
- `status`
- `created_at`
- `updated_at`

## What Is Mocked

- `MockSearchProvider` returns deterministic public-looking mock results for dry runs and tests.
- OpenAI classification falls back to deterministic local rules when `OPENAI_API_KEY` is missing or the OpenAI package is unavailable.
- `YouTubeProvider` reads `YOUTUBE_API_KEY`, but real YouTube Data API search is not implemented in this MVP. It does not scrape YouTube HTML.
- SerpAPI tests use mocked HTTP responses. Live SerpAPI search requires `SERPAPI_API_KEY`.

## Tests

```powershell
pytest
```

All tests are designed to pass without external API keys or network access.

## Category System

Each lead has two category fields:

Audience Type:

- `Biohacking`
- `Longevity`
- `Men's Health`
- `Fitness Science`
- `Nootropics`
- `Lab/Research`

Lead Type:

- `Newsletter`
- `Creator`
- `Podcast`
- `Community`
- `Media Kit`
- `Sponsor Page`

## Lead Quality

The local scorer penalizes directories, listicles, aggregators, and generic articles. It boosts media kits, sponsor pages, newsletter operators, creator websites, and podcast sponsorship pages.

The `sponsorship_probability` score is a 0-100 estimate based on public signals such as media-kit pages, advertise pages, sponsor pages, business inquiry pages, prior sponsor mentions, newsletter ownership, creator ownership, and contactability.
