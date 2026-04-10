"""
Aggregator — runs all scrapers in parallel, deduplicates, and caches results.
"""
import hashlib
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from .config import (
    JOB_SITES, CACHE_DIR, CACHE_TTL_HOURS,
)
from .models import Vacancy, save_cache, load_cache
from .sites import BS4_SCRAPERS
from .dynamic import PLAYWRIGHT_SCRAPERS

log = logging.getLogger(__name__)

CACHE_FILE = f"{CACHE_DIR}/last_results.json"


def _vacancy_hash(v: Vacancy) -> str:
    """Deduplicate by title + company + source."""
    key = f"{v.title.lower()}|{v.company.lower()}|{v.source}"
    return hashlib.md5(key.encode()).hexdigest()


def _cache_fresh() -> bool:
    p = Path(CACHE_FILE)
    if not p.exists():
        return False
    data = json.loads(p.read_text())
    fetched_at = datetime.fromisoformat(data.get("fetched_at", "2000-01-01T00:00:00"))
    if fetched_at.tzinfo is None:
        fetched_at = fetched_at.replace(tzinfo=timezone.utc)
    age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    return age_hours < CACHE_TTL_HOURS


def run_all(
    rank: Optional[str] = None,
    vessel: Optional[str] = None,
    region: Optional[str] = None,
    use_cache: bool = True,
    include_telegram: bool = True,
    tg_limit: int = 50,
    tg_since: int = 24,
) -> list[Vacancy]:
    """
    Fetch vacancies from all enabled sources.
    Returns deduplicated, optionally filtered list.
    """
    if use_cache and _cache_fresh():
        log.info("Using cached results from %s", CACHE_FILE)
        vacancies = load_cache(CACHE_FILE)
    else:
        vacancies = _fetch_from_all_sources(include_telegram, tg_limit, tg_since)
        save_cache(vacancies, CACHE_FILE)
        log.info("Fetched %d vacancies total, saved to cache", len(vacancies))

    # Apply filters
    if any([rank, vessel, region]):
        before = len(vacancies)
        vacancies = [v for v in vacancies if v.matches(rank=rank, vessel=vessel, region=region)]
        log.info("Filtered %d → %d results", before, len(vacancies))

    return vacancies


def _fetch_from_all_sources(
    include_telegram: bool,
    tg_limit: int,
    tg_since: int,
) -> list[Vacancy]:
    """Run all scrapers, collect results, deduplicate."""
    all_vacancies: list[Vacancy] = []
    seen: set[str] = set()

    enabled_sites = {s["name"] for s in JOB_SITES if s.get("enabled", True)}

    # Run BS4 scrapers in parallel (thread-safe: each has its own requests session)
    bs4_tasks = {k: v for k, v in BS4_SCRAPERS.items() if k in enabled_sites}
    pw_tasks = {k: v for k, v in PLAYWRIGHT_SCRAPERS.items() if k in enabled_sites}

    log.info("Running %d BS4 scrapers in parallel...", len(bs4_tasks))
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(fn): name for name, fn in bs4_tasks.items()}
        for future in as_completed(futures):
            name = futures[future]
            try:
                results = future.result(timeout=30)
                added = _deduplicate_add(results, all_vacancies, seen)
                log.info("%-30s → %d new vacancies", name, added)
            except Exception as e:
                log.warning("%-30s → FAILED: %s", name, e)

    # Run Playwright scrapers sequentially (Playwright isn't thread-safe)
    log.info("Running %d Playwright scrapers...", len(pw_tasks))
    for name, fn in pw_tasks.items():
        if name not in enabled_sites:
            continue
        try:
            results = fn()
            added = _deduplicate_add(results, all_vacancies, seen)
            log.info("%-30s → %d new vacancies", name, added)
        except Exception as e:
            log.warning("%-30s → FAILED: %s", name, e)

    # Telegram
    if include_telegram:
        log.info("Fetching Telegram sources...")
        try:
            from .telegram import fetch as tg_fetch
            tg_results = tg_fetch(limit=tg_limit, since_hours=tg_since)
            added = _deduplicate_add(tg_results, all_vacancies, seen)
            log.info("Telegram → %d new posts", added)
        except RuntimeError as e:
            log.warning("Telegram skipped: %s", e)
        except Exception as e:
            log.warning("Telegram fetch failed: %s", e)

    return all_vacancies


def _deduplicate_add(
    new_items: list[Vacancy],
    existing: list[Vacancy],
    seen: set[str],
) -> int:
    added = 0
    for v in new_items:
        h = _vacancy_hash(v)
        if h not in seen:
            seen.add(h)
            existing.append(v)
            added += 1
    return added


def list_sources() -> dict:
    """Return source status dict for the /ocean-clouds:sources skill."""
    return {
        "job_sites": JOB_SITES,
        "telegram": [],  # populated by telegram module at runtime
        "cache": {
            "file": CACHE_FILE,
            "fresh": _cache_fresh(),
        },
    }
