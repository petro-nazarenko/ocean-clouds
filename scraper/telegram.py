"""
Telegram channel/group scraper using Telethon.

Setup:
  1. Get API credentials at https://my.telegram.org/apps
  2. Add TG_API_ID and TG_API_HASH to your .env file
  3. Run: python -m scraper.telegram --setup   (first-time auth)

Usage:
  python -m scraper.telegram fetch [--limit 50] [--since 24] [--channel @name]
"""
import asyncio
import json
import logging
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .config import TELEGRAM_SOURCES, TG_CACHE_DIR, TG_CACHE_TTL_HOURS, RANK_KEYWORDS
from .models import Vacancy

log = logging.getLogger(__name__)

SESSION_FILE = ".tg_session"


def _telethon_available() -> bool:
    try:
        import telethon  # noqa: F401
        return True
    except ImportError:
        return False


def _load_env() -> tuple[str, str]:
    """Load TG_API_ID and TG_API_HASH from environment or .env file."""
    from dotenv import load_dotenv
    load_dotenv()
    api_id = os.getenv("TG_API_ID", "")
    api_hash = os.getenv("TG_API_HASH", "")
    return api_id, api_hash


def setup_credentials() -> None:
    """Interactive first-time setup: save API credentials and authenticate."""
    print("=== Ocean Clouds — Telegram Setup ===")
    print("Get your credentials at: https://my.telegram.org/apps\n")
    api_id = input("Enter TG_API_ID: ").strip()
    api_hash = input("Enter TG_API_HASH: ").strip()

    env_path = Path(".env")
    lines = []
    if env_path.exists():
        lines = env_path.read_text().splitlines()
        lines = [l for l in lines if not l.startswith("TG_API_ID") and not l.startswith("TG_API_HASH")]

    lines += [f"TG_API_ID={api_id}", f"TG_API_HASH={api_hash}"]
    env_path.write_text("\n".join(lines) + "\n")
    print(f"\nCredentials saved to {env_path}")
    print("Now running authentication (you'll receive a code via Telegram)...\n")

    asyncio.run(_authenticate(api_id, api_hash))


async def _authenticate(api_id: str, api_hash: str) -> None:
    from telethon import TelegramClient
    client = TelegramClient(SESSION_FILE, int(api_id), api_hash)
    await client.start()
    me = await client.get_me()
    print(f"\nAuthenticated as: {me.first_name} (@{me.username})")
    print(f"Session saved to: {SESSION_FILE}.session")
    await client.disconnect()


def _extract_vacancy_from_message(text: str, source: str, url: str, posted_at: str) -> Vacancy:
    """Best-effort extraction of structured vacancy data from a Telegram message."""
    text_lower = text.lower()

    # Detect rank
    rank = "—"
    for rank_name, keywords in RANK_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            rank = rank_name
            break

    # Extract salary
    salary = "—"
    m = re.search(r"\$[\d,]+(?:\s*/\s*month)?|[\d,]+\s*(?:USD|EUR)\s*/?\s*(?:month|mo)?", text, re.I)
    if m:
        salary = m.group().strip()

    # Extract duration
    duration = "—"
    m = re.search(r"(\d+)\s*(?:\+\s*\d+)?\s*(?:months?|mos?|weeks?)", text, re.I)
    if m:
        duration = m.group().strip()

    # Detect vessel type
    from .config import VESSEL_TYPES
    vessel = "—"
    for vt in VESSEL_TYPES:
        if vt.lower() in text_lower:
            vessel = vt
            break

    # Detect urgency
    urgent_words = ["urgent", "immediately", "asap", "срочно", "негайно", "immediate joining"]
    is_urgent = any(w in text_lower for w in urgent_words)

    # Title: first meaningful line
    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    title = lines[0][:80] if lines else "Job Vacancy"

    return Vacancy(
        title=title,
        company=source,
        rank=rank,
        vessel_type=vessel,
        region="—",
        salary=salary,
        duration=duration,
        joining_date="—",
        source=f"telegram:{source}",
        url=url,
        description=text[:300],
        posted_at=posted_at,
        is_urgent=is_urgent,
    )


def _is_job_message(text: str) -> bool:
    """Filter Telegram messages — only keep those that look like job postings."""
    text_lower = text.lower()
    job_signals = [
        "vacancy", "vacanci", "hiring", "required", "needed", "join", "joining",
        "position", "rank", "salary", "contract", "vessel", "ship", "offshore",
        "вакансия", "вакансії", "набір", "работа", "робота", "моряк", "экипаж",
        "captain", "engineer", "officer", "seaman", "seafarer", "crew",
    ]
    return any(signal in text_lower for signal in job_signals)


async def _fetch_channel(
    client,
    source: dict,
    limit: int,
    since_hours: int,
) -> list[Vacancy]:
    """Fetch messages from a single channel or group."""
    from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError

    vacancies = []
    cutoff = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    handle = source.get("username") or source.get("id")
    name = source["name"]

    try:
        entity = await client.get_entity(handle)
        async for msg in client.iter_messages(entity, limit=limit):
            if not msg.text:
                continue
            if msg.date.replace(tzinfo=timezone.utc) < cutoff:
                break
            if not _is_job_message(msg.text):
                continue

            # Build Telegram message URL
            channel_id = str(entity.id).lstrip("-100")
            msg_url = f"https://t.me/{source.get('username', channel_id)}/{msg.id}"

            vacancy = _extract_vacancy_from_message(
                text=msg.text,
                source=name,
                url=msg_url,
                posted_at=msg.date.strftime("%Y-%m-%d %H:%M UTC"),
            )
            vacancies.append(vacancy)

        log.info("Fetched %d job posts from %s", len(vacancies), name)
    except ChannelPrivateError:
        log.warning("Cannot access %s — private channel/group. Join first.", name)
    except UsernameNotOccupiedError:
        log.warning("Channel @%s not found or has been renamed.", handle)
    except Exception as e:
        log.warning("Error fetching %s: %s", name, e)

    return vacancies


async def _fetch_all(
    limit: int = 50,
    since_hours: int = 24,
    channel_filter: str = None,
) -> list[Vacancy]:
    api_id, api_hash = _load_env()
    if not api_id or not api_hash:
        raise RuntimeError(
            "Telegram credentials not configured.\n"
            "Run: python -m scraper.telegram --setup"
        )

    from telethon import TelegramClient
    client = TelegramClient(SESSION_FILE, int(api_id), api_hash)

    sources = TELEGRAM_SOURCES
    if channel_filter:
        sources = [s for s in sources if channel_filter.lstrip("@") in (s.get("username", "") or "")]

    all_vacancies = []
    async with client:
        for source in sources:
            if not source.get("enabled", True):
                continue
            results = await _fetch_channel(client, source, limit, since_hours)
            all_vacancies.extend(results)

    return all_vacancies


def fetch(limit: int = 50, since_hours: int = 24, channel_filter: str = None) -> list[Vacancy]:
    """Public sync entry point."""
    if not _telethon_available():
        log.error("Telethon not installed. Run: pip install telethon")
        return []
    return asyncio.run(_fetch_all(limit, since_hours, channel_filter))


def _cache_path(since_hours: int) -> str:
    return f"{TG_CACHE_DIR}/tg_{since_hours}h.json"


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Ocean Clouds — Telegram fetcher")
    parser.add_argument("--setup", action="store_true", help="First-time auth setup")
    parser.add_argument("fetch", nargs="?", help="Fetch job posts")
    parser.add_argument("--limit", type=int, default=50)
    parser.add_argument("--since", type=int, default=24)
    parser.add_argument("--channel", type=str, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")

    if args.setup:
        setup_credentials()
    else:
        results = fetch(limit=args.limit, since_hours=args.since, channel_filter=args.channel)
        for v in results:
            print(f"[{v.posted_at}] {v.rank} | {v.vessel_type} | {v.salary}")
            print(f"  {v.title[:80]}")
            print(f"  {v.url}\n")
