from __future__ import annotations

import argparse
from itertools import islice

from audience_discovery.ai.classify import LeadClassifier
from audience_discovery.config import load_app_config
from audience_discovery.crawl.fetcher import PageFetcher
from audience_discovery.export.csv_exporter import CSVExporter
from audience_discovery.models import PageContent, SearchResult
from audience_discovery.search.mock_provider import MockSearchProvider
from audience_discovery.search.serpapi_provider import SerpAPIProvider
from audience_discovery.search.youtube_provider import YouTubeProvider
from audience_discovery.storage.db import LeadStore


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compliant public audience discovery MVP")
    parser.add_argument("--category", help="Category key to run. Defaults to all categories.")
    parser.add_argument("--limit", type=int, default=10, help="Maximum search results to process.")
    parser.add_argument("--dry-run", action="store_true", help="Use deterministic mock results and avoid live fetching.")
    parser.add_argument("--export-only", action="store_true", help="Export existing SQLite leads without searching.")
    parser.add_argument("--db-path", default="outputs/leads.sqlite", help="SQLite database path.")
    parser.add_argument("--output-dir", default="outputs", help="CSV output directory.")
    parser.add_argument(
        "--provider",
        choices=["mock", "serpapi", "youtube"],
        default="mock",
        help="Search provider. SerpAPI uses Google search; YouTube is a non-scraping API skeleton.",
    )
    return parser


def _iter_search_results(provider, categories, limit: int):
    remaining = limit
    seen_urls: set[str] = set()
    seen_domains: set[str] = set()
    for category in categories:
        if remaining <= 0:
            break
        for query in category.seed_queries:
            if remaining <= 0:
                break
            for result in provider.search(query, category.key, remaining):
                normalized_url = result.url.rstrip("/")
                if normalized_url in seen_urls or result.domain in seen_domains:
                    continue
                seen_urls.add(normalized_url)
                seen_domains.add(result.domain)
                yield result
                remaining -= 1
                if remaining <= 0:
                    break


def _page_from_search_result(result: SearchResult) -> PageContent:
    return PageContent(
        url=result.url,
        title=result.title,
        meta_description=result.snippet,
        text=result.snippet,
        links=[],
    )


def run(args: argparse.Namespace) -> dict[str, int]:
    config = load_app_config()
    store = LeadStore(args.db_path)
    try:
        if not args.export_only:
            if args.category:
                if args.category not in config.categories:
                    raise SystemExit(f"Unknown category '{args.category}'. Available: {', '.join(config.categories)}")
                categories = [config.categories[args.category]]
            else:
                categories = list(config.categories.values())

            if args.provider == "youtube":
                provider = YouTubeProvider()
            elif args.provider == "serpapi":
                provider = SerpAPIProvider()
            else:
                provider = MockSearchProvider()
            fetcher = PageFetcher(rate_limit_seconds=1.0)
            classifier = LeadClassifier(config.scoring_weights)

            for result in islice(_iter_search_results(provider, categories, args.limit), args.limit):
                page = _page_from_search_result(result)
                if not args.dry_run:
                    fetched = fetcher.fetch(result.url)
                    if fetched.ok:
                        page = fetched.page
                lead = classifier.classify(result, page)
                store.upsert_lead(lead)

        leads = store.list_leads()
        counts = CSVExporter(args.output_dir).export_all(leads)
        counts["total_leads"] = len(leads)
        return counts
    finally:
        store.close()


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    counts = run(args)
    print(
        "Audience discovery complete: "
        f"{counts['total_leads']} stored, "
        f"{counts['raw']} raw exported, "
        f"{counts['scored']} scored exported, "
        f"{counts['review_queue']} in review queue."
    )


if __name__ == "__main__":
    main()
