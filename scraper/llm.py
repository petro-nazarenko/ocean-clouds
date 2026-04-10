"""
LLM-based vacancy extraction using Claude API.

Instead of fragile CSS selectors, we send raw page text to Claude
and ask it to extract structured vacancy data as JSON.

Requires: ANTHROPIC_API_KEY in .env
Model: claude-haiku-4-5 (fast + cheap for extraction tasks)
"""
import json
import logging
import os
from typing import Optional

import anthropic
from dotenv import load_dotenv

from .models import Vacancy

load_dotenv()
log = logging.getLogger(__name__)

# Haiku is fast and cheap — ideal for extraction
MODEL = "claude-haiku-4-5-20251001"
# Max chars to send per chunk (keeps tokens manageable)
CHUNK_SIZE = 12_000


EXTRACTION_PROMPT = """\
You are extracting maritime job vacancies from text scraped from a job website or Telegram channel.

Source: {source}
URL: {url}

--- TEXT START ---
{text}
--- TEXT END ---

Extract ALL job vacancies visible in the text above.
Return a JSON array. Each object must have these exact fields:
{{
  "title": "full job title as shown",
  "company": "company or crewing agency name, or blank if unknown",
  "rank": "standardized rank (Master, Chief Officer, 2nd Officer, AB, Cook, etc.)",
  "vessel_type": "vessel type (Container, Bulk Carrier, Tanker, LNG, Offshore, etc.) or blank",
  "region": "trading area or region or blank",
  "salary": "salary as shown (e.g. '$5000/month', '4000-5500 $') or blank",
  "duration": "contract duration (e.g. '4 months', '3+1 months') or blank",
  "joining_date": "joining date or 'immediate' or blank",
  "url": "direct URL to this vacancy if found in the text, else blank",
  "is_urgent": false
}}

Rules:
- Return ONLY a valid JSON array, no markdown, no explanation
- If no vacancies found, return []
- is_urgent = true if the text says urgent, immediate, ASAP, срочно, негайно
- Normalize rank names to English standard titles
- Include every vacancy you see, even if some fields are missing
"""


def _chunk_text(text: str, size: int = CHUNK_SIZE) -> list[str]:
    """Split text into overlapping chunks so vacancies spanning a boundary aren't lost."""
    if len(text) <= size:
        return [text]
    chunks = []
    step = size - 500  # 500-char overlap
    for i in range(0, len(text), step):
        chunks.append(text[i:i + size])
    return chunks


def extract_vacancies_from_text(
    text: str,
    source: str,
    url: str,
    client: Optional[anthropic.Anthropic] = None,
) -> list[Vacancy]:
    """Send text to Claude, parse the JSON response into Vacancy objects."""
    if not text.strip():
        return []

    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            log.error("ANTHROPIC_API_KEY not set — add it to .env")
            return []
        client = anthropic.Anthropic(api_key=api_key)

    vacancies: list[Vacancy] = []
    chunks = _chunk_text(text)

    for i, chunk in enumerate(chunks):
        if len(chunks) > 1:
            log.info("%s — sending chunk %d/%d to LLM", source, i + 1, len(chunks))
        else:
            log.info("%s — sending to LLM (%d chars)", source, len(chunk))

        prompt = EXTRACTION_PROMPT.format(source=source, url=url, text=chunk)

        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            block = response.content[0]
            raw = (block.text if hasattr(block, "text") else "").strip()

            # Strip markdown code fences if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            raw = raw.strip()

            items = json.loads(raw)
            if not isinstance(items, list):
                log.warning("%s — LLM returned non-list JSON", source)
                continue

            for item in items:
                try:
                    v = Vacancy(
                        title=item.get("title", "—") or "—",
                        company=item.get("company", "") or source,
                        rank=item.get("rank", "—") or "—",
                        vessel_type=item.get("vessel_type", "—") or "—",
                        region=item.get("region", "—") or "—",
                        salary=item.get("salary", "—") or "—",
                        duration=item.get("duration", "—") or "—",
                        joining_date=item.get("joining_date", "—") or "—",
                        source=source,
                        url=item.get("url", "") or url,
                        description="",
                        posted_at="",
                        is_urgent=bool(item.get("is_urgent", False)),
                    )
                    vacancies.append(v)
                except Exception as e:
                    log.warning("%s — failed to build Vacancy from item: %s — %s", source, item, e)

            log.info("%s — extracted %d vacancies from chunk %d", source, len(items), i + 1)

        except json.JSONDecodeError as e:
            log.warning("%s — LLM returned invalid JSON: %s\nRaw: %s", source, e, raw[:300])
        except anthropic.APIError as e:
            log.error("%s — Claude API error: %s", source, e)
        except Exception as e:
            log.error("%s — unexpected error during LLM extraction: %s", source, e)

    # Deduplicate within the same source (same title+salary)
    seen: set[str] = set()
    unique: list[Vacancy] = []
    for v in vacancies:
        key = f"{v.title.lower()}|{v.salary}"
        if key not in seen:
            seen.add(key)
            unique.append(v)

    return unique


def extract_from_telegram_messages(
    messages: list[str],
    source: str,
    urls: list[str],
    client: Optional[anthropic.Anthropic] = None,
) -> list[Vacancy]:
    """
    Batch-extract vacancies from a list of Telegram message texts.
    Sends them all at once (or in chunks) to reduce API calls.
    """
    if not messages:
        return []

    numbered = "\n\n".join(
        f"[MSG {i+1}] {msg}" for i, msg in enumerate(messages)
    )
    return extract_vacancies_from_text(numbered, source=source, url=source, client=client)
