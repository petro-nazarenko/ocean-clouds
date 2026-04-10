"""
Ocean Clouds CLI — entry point for Claude Code plugin skills.

Usage:
  python -m scraper.cli search [--rank RANK] [--vessel VESSEL] [--region REGION]
  python -m scraper.cli filter [--rank] [--vessel] [--region] [--salary] [--urgent]
  python -m scraper.cli sources [--list] [--test-all]
"""
import argparse
import json
import logging
import os
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s  %(message)s",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Formatters
# ---------------------------------------------------------------------------

def _truncate(s: str, n: int) -> str:
    return s[:n - 1] + "…" if len(s) > n else s


def print_table(vacancies: list) -> None:
    if not vacancies:
        print("No vacancies found.")
        return

    cols = [
        ("Rank",        "rank",         22),
        ("Vessel",       "vessel_type",  16),
        ("Company",      "company",      20),
        ("Salary",       "salary",       14),
        ("Duration",     "duration",     10),
        ("Source",       "source",       22),
    ]

    # Header
    header = "  ".join(h.ljust(w) for h, _, w in cols) + "  URL"
    sep = "  ".join("-" * w for _, _, w in cols)
    print(header)
    print(sep)

    for v in vacancies:
        urgent_marker = " !" if v.is_urgent else "  "
        row = "  ".join(
            _truncate(getattr(v, field) or "—", width).ljust(width)
            for _, field, width in cols
        )
        print(f"{urgent_marker}{row}  {v.url}")

    print(f"\n{'='*80}")
    print(f"  {len(vacancies)} vacancies  |  ! = urgent/immediate")


def print_json(vacancies: list) -> None:
    print(json.dumps([v.to_dict() for v in vacancies], ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_search(args: argparse.Namespace) -> None:
    from .aggregator import run_all

    print(f"\nSearching all sources...")
    if args.rank:
        print(f"  Rank filter:   {args.rank}")
    if args.vessel:
        print(f"  Vessel filter: {args.vessel}")
    if args.region:
        print(f"  Region filter: {args.region}")
    print()

    vacancies = run_all(
        rank=args.rank,
        vessel=args.vessel,
        region=args.region,
        use_cache=not args.fresh,
        include_telegram=not args.no_telegram,
        tg_limit=args.tg_limit,
        tg_since=args.tg_since,
    )

    if args.format == "json":
        print_json(vacancies)
    else:
        print_table(vacancies)

    print(f"\nFound {len(vacancies)} vacancies across all sources.\n")


def cmd_filter(args: argparse.Namespace) -> None:
    from .models import load_cache

    cache_file = ".cache/last_results.json"
    if not Path(cache_file).exists():
        print("No cached results found. Run `/ocean-clouds:search` first.")
        sys.exit(1)

    all_vacancies = load_cache(cache_file)
    filtered = [
        v for v in all_vacancies
        if v.matches(
            rank=args.rank,
            vessel=args.vessel,
            region=args.region,
            min_salary=args.salary,
            max_duration=args.duration,
            source_filter=args.source,
            urgent_only=args.urgent,
        )
    ]

    if args.format == "json":
        print_json(filtered)
    else:
        print_table(filtered)

    print(f"\nShowing {len(filtered)} of {len(all_vacancies)} results after filters.\n")


def cmd_sources(args: argparse.Namespace) -> None:
    from .config import JOB_SITES, TELEGRAM_SOURCES
    import requests

    if args.test_all:
        print("Testing all sources...\n")
        for site in JOB_SITES:
            if not site.get("enabled"):
                print(f"  DISABLED  {site['name']}")
                continue
            try:
                r = requests.get(site["url"], timeout=10, headers={"User-Agent": "Mozilla/5.0"})
                status = r.status_code
                icon = "OK  " if status == 200 else "WARN"
                print(f"  {icon}  {status}  {site['name']:30s} {site['url']}")
            except Exception as e:
                print(f"  FAIL  ---  {site['name']:30s} {e}")
        return

    # Default: list all
    print("\n=== Job Boards & Portals ===\n")
    print(f"  {'Name':30s} {'Type':12s} {'Status':10s} URL")
    print(f"  {'-'*30} {'-'*12} {'-'*10} {'-'*40}")
    for s in JOB_SITES:
        status = "enabled" if s.get("enabled", True) else "disabled"
        print(f"  {s['name']:30s} {s['type']:12s} {status:10s} {s['url']}")

    print(f"\n=== Telegram Channels & Groups ===\n")
    print(f"  {'Name':30s} {'Handle':25s} {'Type':10s} Status")
    print(f"  {'-'*30} {'-'*25} {'-'*10} {'-'*10}")
    for s in TELEGRAM_SOURCES:
        status = "enabled" if s.get("enabled", True) else "disabled"
        handle = f"@{s.get('username', s.get('id', ''))}"
        print(f"  {s['name']:30s} {handle:25s} {s['type']:10s} {status}")

    print()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="python -m scraper.cli",
        description="Ocean Clouds — maritime job aggregator",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # search
    p_search = sub.add_parser("search", help="Fetch vacancies from all sources")
    p_search.add_argument("--rank", type=str, default=None)
    p_search.add_argument("--vessel", type=str, default=None)
    p_search.add_argument("--region", type=str, default=None)
    p_search.add_argument("--fresh", action="store_true", help="Bypass cache")
    p_search.add_argument("--no-telegram", action="store_true")
    p_search.add_argument("--tg-limit", type=int, default=50)
    p_search.add_argument("--tg-since", type=int, default=24, help="Hours")
    p_search.add_argument("--format", choices=["table", "json"], default="table")

    # filter
    p_filter = sub.add_parser("filter", help="Filter cached results")
    p_filter.add_argument("--rank", type=str, default=None)
    p_filter.add_argument("--vessel", type=str, default=None)
    p_filter.add_argument("--region", type=str, default=None)
    p_filter.add_argument("--salary", type=int, default=None, help="Minimum salary (USD)")
    p_filter.add_argument("--duration", type=int, default=None, help="Max contract months")
    p_filter.add_argument("--source", type=str, default=None)
    p_filter.add_argument("--urgent", action="store_true")
    p_filter.add_argument("--format", choices=["table", "json"], default="table")

    # sources
    p_sources = sub.add_parser("sources", help="List and test all sources")
    p_sources.add_argument("--list", action="store_true", default=True)
    p_sources.add_argument("--test-all", action="store_true")

    args = parser.parse_args()

    dispatch = {
        "search":  cmd_search,
        "filter":  cmd_filter,
        "sources": cmd_sources,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
