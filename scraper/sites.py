"""
BeautifulSoup scrapers for static maritime job sites.

Each scraper function returns a list[Vacancy].
If selectors break due to site redesign, inspect the live HTML and update
the CSS selectors in the corresponding scraper function.
"""
import time
import logging
from typing import Optional
import requests
from bs4 import BeautifulSoup

from .models import Vacancy
from .config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, USER_AGENT

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
    for attempt in range(MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except requests.RequestException as e:
            log.warning("Attempt %d/%d failed for %s: %s", attempt + 1, MAX_RETRIES + 1, url, e)
            if attempt < MAX_RETRIES:
                time.sleep(REQUEST_DELAY * 2)
    return None


# ---------------------------------------------------------------------------
# AllCrewing  (allcrewing.com/vacancies)
# ---------------------------------------------------------------------------
def scrape_allcrewing() -> list[Vacancy]:
    session = _session()
    soup = _get(session, "https://allcrewing.com/vacancies")
    if not soup:
        return []

    vacancies = []
    # Inspect: vacancy cards are typically <div class="vacancy-item"> or similar
    # Update selectors based on live HTML if needed
    for card in soup.select(".vacancy-item, .job-card, article.vacancy"):
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

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://allcrewing.com" + url

            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "AllCrewing",
                rank=rank.get_text(strip=True) if rank else title.get_text(strip=True) if title else "—",
                vessel_type=vessel.get_text(strip=True) if vessel else "—",
                region=region.get_text(strip=True) if region else "—",
                salary=salary.get_text(strip=True) if salary else "—",
                duration=duration.get_text(strip=True) if duration else "—",
                joining_date=joining.get_text(strip=True) if joining else "—",
                source="allcrewing.com",
                url=url,
                description="",
                posted_at="",
                is_urgent="urgent" in card.get_text().lower(),
            ))
        except Exception as e:
            log.debug("AllCrewing card parse error: %s", e)
        time.sleep(REQUEST_DELAY)
    return vacancies


# ---------------------------------------------------------------------------
# Maritime Connector  (maritime-connector.com/seafarer-jobs/)
# ---------------------------------------------------------------------------
def scrape_maritime_connector() -> list[Vacancy]:
    session = _session()
    soup = _get(session, "https://maritime-connector.com/seafarer-jobs/")
    if not soup:
        return []

    vacancies = []
    for card in soup.select(".job-listing, .job-item, .vacancy-row"):
        try:
            title = card.select_one(".job-title, h3, h2")
            company = card.select_one(".company, .employer-name")
            details = card.get_text(" | ", strip=True)
            link_tag = card.select_one("a[href]")

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://maritime-connector.com" + url

            # Maritime Connector often puts rank in the title
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
                url=url,
                description=details[:200],
                posted_at="",
                is_urgent="urgent" in details.lower(),
            ))
        except Exception as e:
            log.debug("Maritime Connector parse error: %s", e)
    return vacancies


# ---------------------------------------------------------------------------
# SeafarerJobs  (seafarerjobs.com/jobs)
# ---------------------------------------------------------------------------
def scrape_seafarerjobs() -> list[Vacancy]:
    session = _session()
    base = "https://www.seafarerjobs.com"
    soup = _get(session, f"{base}/jobs")
    if not soup:
        return []

    vacancies = []
    for card in soup.select(".job-listing, .vacancy, .search-result-item"):
        try:
            title = card.select_one("h2, h3, .position-title")
            company = card.select_one(".company-name, .employer")
            salary = card.select_one(".salary")
            vessel = card.select_one(".vessel-type")
            region = card.select_one(".location, .region")
            link_tag = card.select_one("a[href]")

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = base + url

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
                url=url,
                description="",
                posted_at="",
                is_urgent="urgent" in card.get_text().lower(),
            ))
        except Exception as e:
            log.debug("SeafarerJobs parse error: %s", e)
    return vacancies


# ---------------------------------------------------------------------------
# Jobs.ua Maritime  (Ukrainian)
# ---------------------------------------------------------------------------
def scrape_jobs_ua() -> list[Vacancy]:
    session = _session()
    soup = _get(session, "https://www.jobs.ua/ukr/vacancies-in-sphere-marine_vessels/")
    if not soup:
        return []

    vacancies = []
    for card in soup.select(".card-vacancy, .vacancy__item, .b-vacancy-item"):
        try:
            title = card.select_one(".card-vacancy-title, .vacancy__title, h2")
            company = card.select_one(".card-company-name, .vacancy__company")
            salary = card.select_one(".card-salary, .vacancy__salary")
            region = card.select_one(".card-city, .vacancy__city")
            link_tag = card.select_one("a[href]")

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://www.jobs.ua" + url

            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "—",
                rank=title.get_text(strip=True) if title else "—",
                vessel_type=_extract_vessel_type(card.get_text()),
                region=region.get_text(strip=True) if region else "Ukraine",
                salary=salary.get_text(strip=True) if salary else "—",
                duration="—",
                joining_date="—",
                source="jobs.ua",
                url=url,
                description="",
                posted_at="",
                is_urgent=False,
            ))
        except Exception as e:
            log.debug("Jobs.ua parse error: %s", e)
    return vacancies


# ---------------------------------------------------------------------------
# Work.ua Maritime  (Ukrainian)
# ---------------------------------------------------------------------------
def scrape_work_ua() -> list[Vacancy]:
    session = _session()
    soup = _get(session, "https://www.work.ua/jobs-sea/")
    if not soup:
        return []

    vacancies = []
    for card in soup.select(".job-link, .card.card-hover"):
        try:
            title = card.select_one("h2, .h2")
            company = card.select_one(".add-top-xs span")
            salary = card.select_one(".h5.pull-right, .salary")
            link_tag = card.select_one("a[href]")

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://www.work.ua" + url

            vacancies.append(Vacancy(
                title=title.get_text(strip=True) if title else "—",
                company=company.get_text(strip=True) if company else "—",
                rank=title.get_text(strip=True) if title else "—",
                vessel_type=_extract_vessel_type(card.get_text()),
                region="Ukraine",
                salary=salary.get_text(strip=True) if salary else "—",
                duration="—",
                joining_date="—",
                source="work.ua",
                url=url,
                description="",
                posted_at="",
                is_urgent=False,
            ))
        except Exception as e:
            log.debug("Work.ua parse error: %s", e)
    return vacancies


# ---------------------------------------------------------------------------
# Crewtoo  (crewtoo.com/maritime-jobs)
# ---------------------------------------------------------------------------
def scrape_crewtoo() -> list[Vacancy]:
    session = _session()
    soup = _get(session, "https://www.crewtoo.com/maritime-jobs")
    if not soup:
        return []

    vacancies = []
    for card in soup.select(".job-card, .job-result, article"):
        try:
            title = card.select_one("h2, h3, .job-title")
            company = card.select_one(".company-name, .employer")
            link_tag = card.select_one("a[href]")
            text = card.get_text(" ", strip=True)

            url = link_tag["href"] if link_tag else ""
            if url and not url.startswith("http"):
                url = "https://www.crewtoo.com" + url

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
                url=url,
                description=text[:200],
                posted_at="",
                is_urgent="urgent" in text.lower(),
            ))
        except Exception as e:
            log.debug("Crewtoo parse error: %s", e)
    return vacancies


# ---------------------------------------------------------------------------
# Helpers: extract structured fields from unstructured text
# ---------------------------------------------------------------------------
import re

def _extract_salary(text: str) -> str:
    pattern = r"\$[\d,]+(?:\s*/\s*month)?"
    m = re.search(pattern, text, re.IGNORECASE)
    if m:
        return m.group()
    pattern2 = r"[\d,]+\s*(?:USD|EUR|GBP)\s*/?\s*(?:month|mo)?"
    m2 = re.search(pattern2, text, re.IGNORECASE)
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
BS4_SCRAPERS = {
    "AllCrewing":          scrape_allcrewing,
    "Maritime Connector":  scrape_maritime_connector,
    "SeafarerJobs":        scrape_seafarerjobs,
    "Jobs.ua Maritime":    scrape_jobs_ua,
    "Work.ua Maritime":    scrape_work_ua,
    "Crewtoo":             scrape_crewtoo,
}
