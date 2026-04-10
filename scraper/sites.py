"""
BeautifulSoup scrapers for static maritime job sites.

Each scraper function returns list[Vacancy].
If selectors break due to site redesign, inspect the live HTML and update
the CSS selectors in the corresponding scraper function.
"""
import re
import time
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

from .models import Vacancy
from .config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, USER_AGENT, BASE_URLS

log = logging.getLogger(__name__)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT,
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def _get(session: requests.Session, url: str) -> Optional[BeautifulSoup]:
    """Fetch URL with retry logic. Returns parsed soup or None on failure."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            log.debug("GET %s (attempt %d/%d)", url, attempt + 1, MAX_RETRIES + 1)
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except requests.exceptions.Timeout:
            log.warning("Timeout on %s (attempt %d/%d)", url, attempt + 1, MAX_RETRIES + 1)
        except requests.exceptions.HTTPError as e:
            log.warning("HTTP %s for %s — skipping", e.response.status_code, url)
            return None  # don't retry on HTTP errors (4xx/5xx)
        except requests.RequestException as e:
            log.warning("Request failed for %s (attempt %d/%d): %s", url, attempt + 1, MAX_RETRIES + 1, e)
        if attempt < MAX_RETRIES:
            time.sleep(REQUEST_DELAY * 2)
    log.error("All %d attempts failed for %s", MAX_RETRIES + 1, url)
    return None


def _resolve_url(href: object, base: str) -> str:
    """Resolve a potentially relative URL against a base."""
    h = str(href) if href else ""
    if not h:
        return ""
    return h if h.startswith("http") else base + h


# ---------------------------------------------------------------------------
# AllCrewing  (allcrewing.com/vacancies)
# ---------------------------------------------------------------------------
def scrape_allcrewing() -> list[Vacancy]:
    base = BASE_URLS["AllCrewing"]
    url = next(s["url"] for s in __import__("scraper.config", fromlist=["JOB_SITES"]).JOB_SITES if s["name"] == "AllCrewing")
    log.info("Scraping AllCrewing: %s", url)
    session = _session()
    soup = _get(session, url)
    if not soup:
        log.warning("AllCrewing: no response, returning empty")
        return []

    vacancies: list[Vacancy] = []
    cards = soup.select(".vacancy-item, .job-card, article.vacancy")
    log.info("AllCrewing: found %d candidate cards", len(cards))

    for card in cards:
        try:
            title = card.select_one(".vacancy-title, .job-title, h2, h3")
            company = card.select_one(".company-name, .employer")
            rank = card.select_one(".rank, .position")
            vessel = card.select_one(".vessel-type, .ship-type")
            salary = card.select_one(".salary, .wage")
            duration = card.select_one(".duration, .contract")
            joining = card.select_one(".joining, .start-date")
            region = card.select_one(".region, .trading-area, .area")
            link_tag = card.select_one("a[href]")

            href = str(link_tag["href"]) if link_tag and link_tag.get("href") else ""
            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "AllCrewing",
                rank=rank.get_text(strip=True) if rank else (title.get_text(strip=True) if title else "—"),
                vessel_type=vessel.get_text(strip=True) if vessel else "—",
                region=region.get_text(strip=True) if region else "—",
                salary=salary.get_text(strip=True) if salary else "—",
                duration=duration.get_text(strip=True) if duration else "—",
                joining_date=joining.get_text(strip=True) if joining else "—",
                source="allcrewing.com",
                url=_resolve_url(href, base),
                description="",
                posted_at="",
                is_urgent="urgent" in card.get_text().lower(),
            ))
        except Exception as e:
            log.warning("AllCrewing: failed to parse card — %s", e)
        time.sleep(REQUEST_DELAY)

    log.info("AllCrewing: parsed %d vacancies", len(vacancies))
    return vacancies


# ---------------------------------------------------------------------------
# Maritime Connector  (maritime-connector.com/seafarer-jobs/)
# ---------------------------------------------------------------------------
def scrape_maritime_connector() -> list[Vacancy]:
    base = BASE_URLS["Maritime Connector"]
    url = base + "/seafarer-jobs/"
    log.info("Scraping Maritime Connector: %s", url)
    session = _session()
    soup = _get(session, url)
    if not soup:
        log.warning("Maritime Connector: no response, returning empty")
        return []

    vacancies: list[Vacancy] = []
    cards = soup.select(".job-listing, .job-item, .vacancy-row")
    log.info("Maritime Connector: found %d candidate cards", len(cards))

    for card in cards:
        try:
            title = card.select_one(".job-title, h3, h2")
            company = card.select_one(".company, .employer-name")
            details = card.get_text(" | ", strip=True)
            link_tag = card.select_one("a[href]")

            href = str(link_tag["href"]) if link_tag and link_tag.get("href") else ""
            rank = title.get_text(strip=True) if title else "—"

            vacancies.append(Vacancy(
                title=rank,
                company=company.get_text(strip=True) if company else "—",
                rank=rank,
                vessel_type=_extract_vessel_type(details),
                region=_extract_region(details),
                salary=_extract_salary(details),
                duration=_extract_duration(details),
                joining_date="—",
                source="maritime-connector.com",
                url=_resolve_url(href, base),
                description=details[:200],
                posted_at="",
                is_urgent="urgent" in details.lower(),
            ))
        except Exception as e:
            log.warning("Maritime Connector: failed to parse card — %s", e)

    log.info("Maritime Connector: parsed %d vacancies", len(vacancies))
    return vacancies


# ---------------------------------------------------------------------------
# SeafarerJobs  (seafarerjobs.com/jobs)
# ---------------------------------------------------------------------------
def scrape_seafarerjobs() -> list[Vacancy]:
    base = BASE_URLS["SeafarerJobs"]
    url = base + "/jobs"
    log.info("Scraping SeafarerJobs: %s", url)
    session = _session()
    soup = _get(session, url)
    if not soup:
        log.warning("SeafarerJobs: no response, returning empty")
        return []

    vacancies: list[Vacancy] = []
    cards = soup.select(".job-listing, .vacancy, .search-result-item")
    log.info("SeafarerJobs: found %d candidate cards", len(cards))

    for card in cards:
        try:
            title = card.select_one("h2, h3, .position-title")
            company = card.select_one(".company-name, .employer")
            salary = card.select_one(".salary")
            vessel = card.select_one(".vessel-type")
            region = card.select_one(".location, .region")
            link_tag = card.select_one("a[href]")

            href = str(link_tag["href"]) if link_tag and link_tag.get("href") else ""
            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "—",
                rank=title.get_text(strip=True) if title else "—",
                vessel_type=vessel.get_text(strip=True) if vessel else "—",
                region=region.get_text(strip=True) if region else "—",
                salary=salary.get_text(strip=True) if salary else "—",
                duration="—",
                joining_date="—",
                source="seafarerjobs.com",
                url=_resolve_url(href, base),
                description="",
                posted_at="",
                is_urgent="urgent" in card.get_text().lower(),
            ))
        except Exception as e:
            log.warning("SeafarerJobs: failed to parse card — %s", e)

    log.info("SeafarerJobs: parsed %d vacancies", len(vacancies))
    return vacancies


# ---------------------------------------------------------------------------
# UkrCrewingUA  (ukrcrewing.com.ua) — real maritime vacancies, clean HTML
# Structure: <tr> → <td class='wrap'> rank | vessel | duration+salary+date
#            <a class='var'> = vacancy link
# ---------------------------------------------------------------------------
def scrape_ukrcrewing() -> list[Vacancy]:
    base = "https://ukrcrewing.com.ua"
    url = base + "/ua/vacancy/?on_page=50&v_sort=0&v_sort_dir=0"
    log.info("Scraping UkrCrewingUA: %s", url)
    session = _session()
    soup = _get(session, url)
    if not soup:
        log.warning("UkrCrewingUA: no response, returning empty")
        return []

    vacancies: list[Vacancy] = []
    rows = soup.select("a.var")
    log.info("UkrCrewingUA: found %d vacancy links", len(rows))

    for a in rows:
        try:
            row = a.find_parent("tr")
            if not row:
                continue
            cells = row.select("td.wrap")
            if len(cells) < 3:
                continue

            rank        = cells[0].get_text(strip=True)  # e.g. "2nd Officer"
            vessel_type = cells[1].get_text(strip=True)  # e.g. "Bulk Carrier"
            details     = cells[2].get_text(" ", strip=True)  # "4 months 4000-5500 $ 11.04.26 17.02.26"

            # Parse details cell: duration salary currency joining_date posted_date
            parts = details.split()
            duration     = f"{parts[0]} {parts[1]}" if len(parts) >= 2 and parts[1] in ("months","month","weeks","week") else parts[0] if parts else "—"
            currency     = next((p for p in parts if p in ("$", "€", "USD", "EUR")), "")
            salary_num   = next((p for p in parts if any(c.isdigit() for c in p) and p not in duration.split()), "")
            salary       = f"{salary_num} {currency}".strip() if salary_num else "—"
            joining_date = parts[-2] if len(parts) >= 2 else "—"

            href = str(a.get("href", "") or "")
            vacancies.append(Vacancy(
                title=rank,
                company="UkrCrewingUA",
                rank=rank,
                vessel_type=vessel_type,
                region="Worldwide",
                salary=salary,
                duration=duration,
                joining_date=joining_date,
                source="ukrcrewing.com.ua",
                url=_resolve_url(href, base),
                description="",
                posted_at="",
                is_urgent=False,
            ))
        except Exception as e:
            log.warning("UkrCrewingUA: failed to parse row — %s", e)

    log.info("UkrCrewingUA: parsed %d vacancies", len(vacancies))
    return vacancies


# ---------------------------------------------------------------------------
# Crewtoo  (crewtoo.com/maritime-jobs)
# ---------------------------------------------------------------------------
def scrape_crewtoo() -> list[Vacancy]:
    base = BASE_URLS["Crewtoo"]
    url = base + "/maritime-jobs"
    log.info("Scraping Crewtoo: %s", url)
    session = _session()
    soup = _get(session, url)
    if not soup:
        log.warning("Crewtoo: no response, returning empty")
        return []

    vacancies: list[Vacancy] = []
    cards = soup.select(".job-card, .job-result, article")
    log.info("Crewtoo: found %d candidate cards", len(cards))

    for card in cards:
        try:
            title = card.select_one("h2, h3, .job-title")
            company = card.select_one(".company-name, .employer")
            link_tag = card.select_one("a[href]")
            text = card.get_text(" ", strip=True)

            href = str(link_tag["href"]) if link_tag and link_tag.get("href") else ""
            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "—",
                rank=title.get_text(strip=True) if title else "—",
                vessel_type=_extract_vessel_type(text),
                region=_extract_region(text),
                salary=_extract_salary(text),
                duration=_extract_duration(text),
                joining_date="—",
                source="crewtoo.com",
                url=_resolve_url(href, base),
                description=text[:200],
                posted_at="",
                is_urgent="urgent" in text.lower(),
            ))
        except Exception as e:
            log.warning("Crewtoo: failed to parse card — %s", e)

    log.info("Crewtoo: parsed %d vacancies", len(vacancies))
    return vacancies


# ---------------------------------------------------------------------------
# Helpers: extract structured fields from unstructured text
# ---------------------------------------------------------------------------

def _extract_salary(text: str) -> str:
    m = re.search(r"\$[\d,]+(?:\s*/\s*month)?", text, re.IGNORECASE)
    if m:
        return m.group()
    m2 = re.search(r"[\d,]+\s*(?:USD|EUR|GBP)\s*/?\s*(?:month|mo)?", text, re.IGNORECASE)
    return m2.group().strip() if m2 else "—"


def _extract_duration(text: str) -> str:
    m = re.search(r"(\d+)\s*(?:\+\s*\d+)?\s*(?:months?|mos?|weeks?)", text, re.IGNORECASE)
    return m.group().strip() if m else "—"


def _extract_vessel_type(text: str) -> str:
    from .config import VESSEL_TYPES
    text_lower = text.lower()
    for vt in VESSEL_TYPES:
        if vt.lower() in text_lower:
            return vt
    return "—"


def _extract_region(text: str) -> str:
    regions = [
        "North Sea", "Mediterranean", "Pacific", "Atlantic", "Gulf of Mexico",
        "Indian Ocean", "Red Sea", "Black Sea", "Baltic", "Arctic",
        "Far East", "Southeast Asia", "Middle East", "West Africa",
        "North America", "South America", "Europe", "Worldwide",
    ]
    text_lower = text.lower()
    for r in regions:
        if r.lower() in text_lower:
            return r
    return "—"


# ---------------------------------------------------------------------------
# Registry: all BS4 scrapers
# ---------------------------------------------------------------------------
BS4_SCRAPERS: dict[str, object] = {
    "AllCrewing":          scrape_allcrewing,
    "Maritime Connector":  scrape_maritime_connector,
    "SeafarerJobs":        scrape_seafarerjobs,
    "UkrCrewingUA":        scrape_ukrcrewing,     # verified working ✓
    "Crewtoo":             scrape_crewtoo,
}
