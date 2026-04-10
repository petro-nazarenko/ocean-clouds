"""
Aggregator — fetch all sources, extract via LLM, cache results.
"""
import hashlib
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import anthropic
from dotenv import load_dotenv

from .config import JOB_SITES, CACHE_DIR, CACHE_TTL_HOURS
from .models import Vacancy, save_cache, load_cache
from .fetch import fetch_all_sites
from .llm import extract_vacancies_from_text, extract_from_telegram_messages

load_dotenv()
log = logging.getLogger(__name__)

CACHE_FILE = f"{CACHE_DIR}/last_results.json"


def _make_client() -> Optional[anthropic.Anthropic]:
    import os
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        log.error("ANTHROPIC_API_KEY not set — add to .env")
        return None
    return anthropic.Anthropic(api_key=key)


def _vacancy_hash(v: Vacancy) -> str:
    key = f"{v.title.lower()}|{v.salary}|{v.source}"
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
    """Fetch + LLM-extract all sources. Returns filtered vacancies."""
    if use_cache and _cache_fresh():
        log.info("Using cached results")
        vacancies = load_cache(CACHE_FILE)
    else:
        vacancies = _fetch_and_extract(include_telegram, tg_limit, tg_since)
        save_cache(vacancies, CACHE_FILE)
        log.info("Done — %d vacancies cached", len(vacancies))

    if any([rank, vessel, region]):
        before = len(vacancies)
        vacancies = [v for v in vacancies if v.matches(rank=rank, vessel=vessel, region=region)]
        log.info("Filter: %d → %d", before, len(vacancies))

    return vacancies


def _fetch_and_extract(
    include_telegram: bool,
    tg_limit: int,
    tg_since: int,
) -> list[Vacancy]:
    client = _make_client()
    if not client:
        return []

    all_vacancies: list[Vacancy] = []
    seen: set[str] = set()

    # ── Job sites ──────────────────────────────────────────────────────────
    pages = fetch_all_sites(JOB_SITES)
    for page in pages:
        log.info("LLM extracting: %s", page["name"])
        results = extract_vacancies_from_text(
            text=page["text"],
            source=page["name"],
            url=page["url"],
            client=client,
        )
        _add_unique(results, all_vacancies, seen)
        log.info("%s → %d vacancies", page["name"], len(results))

    # ── Telegram ───────────────────────────────────────────────────────────
    if include_telegram:
        log.info("Fetching Telegram sources...")
        try:
            from .telegram import fetch as tg_fetch
            tg_vacancies = tg_fetch(limit=tg_limit, since_hours=tg_since)
            _add_unique(tg_vacancies, all_vacancies, seen)
            log.info("Telegram → %d vacancies", len(tg_vacancies))
        except RuntimeError as e:
            log.warning("Telegram skipped: %s", e)
        except Exception as e:
            log.warning("Telegram error: %s", e)

    return all_vacancies


def _add_unique(new: list[Vacancy], existing: list[Vacancy], seen: set[str]) -> None:
    for v in new:
        h = _vacancy_hash(v)
        if h not in seen:
            seen.add(h)
            existing.append(v)
