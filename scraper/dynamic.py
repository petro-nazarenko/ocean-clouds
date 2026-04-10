"""
Playwright scrapers for JavaScript-rendered maritime job sites.

Install: pip install playwright && playwright install chromium

Each scraper returns list[Vacancy]. Selectors may need updates if sites redesign.
"""
import logging
from typing import Optional

from .models import Vacancy
from .sites import _extract_vessel_type, _extract_region, _extract_salary, _extract_duration

log = logging.getLogger(__name__)


def _playwright_available() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except ImportError:
        return False


def scrape_safety4sea() -> list[Vacancy]:
    """Safety4Sea jobs board — JS-rendered."""
    if not _playwright_available():
        log.warning("Playwright not installed. Run: pip install playwright && playwright install chromium")
        return []

    from playwright.sync_api import sync_playwright

    vacancies = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://jobs.safety4sea.com/search-jobs/", timeout=30000)
            page.wait_for_selector(".job-listing, .search-result, article", timeout=15000)

            cards = page.query_selector_all(".job-listing, .search-result, article.job")
            for card in cards:
                try:
                    title_el = card.query_selector("h2, h3, .job-title")
                    company_el = card.query_selector(".company, .employer")
                    link_el = card.query_selector("a")
                    text = card.inner_text()

                    title = title_el.inner_text().strip() if title_el else "—"
                    company = company_el.inner_text().strip() if company_el else "—"
                    url = link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = "https://jobs.safety4sea.com" + url

                    vacancies.append(Vacancy(
                        title=title,
                        company=company,
                        rank=title,
                        vessel_type=_extract_vessel_type(text),
                        region=_extract_region(text),
                        salary=_extract_salary(text),
                        duration=_extract_duration(text),
                        joining_date="—",
                        source="safety4sea.com",
                        url=url,
                        description=text[:200],
                        posted_at="",
                        is_urgent="urgent" in text.lower(),
                    ))
                except Exception as e:
                    log.debug("Safety4Sea card error: %s", e)
        except Exception as e:
            log.warning("Safety4Sea scrape failed: %s", e)
        finally:
            browser.close()
    return vacancies


def scrape_viking_crew() -> list[Vacancy]:
    """Viking Crew vacancies — JS-rendered."""
    if not _playwright_available():
        log.warning("Playwright not installed.")
        return []

    from playwright.sync_api import sync_playwright

    vacancies = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto("https://www.vikingcrewing.com/crew/vacancies", timeout=30000)
            # Wait for vacancy list to load
            page.wait_for_selector(".vacancy, .job-item, table tr", timeout=15000)

            cards = page.query_selector_all(".vacancy-item, .job-row, table tbody tr")
            for card in cards:
                try:
                    cells = card.query_selector_all("td")
                    text = card.inner_text()
                    link_el = card.query_selector("a")
                    url = link_el.get_attribute("href") if link_el else ""
                    if url and not url.startswith("http"):
                        url = "https://www.vikingcrewing.com" + url

                    # Viking typically shows: Rank | Vessel | Salary | Date
                    rank = cells[0].inner_text().strip() if len(cells) > 0 else _extract_rank_from_text(text)
                    vessel = cells[1].inner_text().strip() if len(cells) > 1 else _extract_vessel_type(text)
                    salary = cells[2].inner_text().strip() if len(cells) > 2 else _extract_salary(text)

                    vacancies.append(Vacancy(
                        title=rank,
                        company="Viking Crew",
                        rank=rank,
                        vessel_type=vessel if vessel else _extract_vessel_type(text),
                        region=_extract_region(text),
                        salary=salary,
                        duration=_extract_duration(text),
                        joining_date="—",
                        source="vikingcrewing.com",
                        url=url,
                        description=text[:200],
                        posted_at="",
                        is_urgent="urgent" in text.lower(),
                    ))
                except Exception as e:
                    log.debug("Viking Crew row error: %s", e)
        except Exception as e:
            log.warning("Viking Crew scrape failed: %s", e)
        finally:
            browser.close()
    return vacancies


def _extract_rank_from_text(text: str) -> str:
    from .config import RANK_KEYWORDS
    text_lower = text.lower()
    for rank, keywords in RANK_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return rank
    return "—"


# ---------------------------------------------------------------------------
# Registry: all Playwright scrapers
# ---------------------------------------------------------------------------
PLAYWRIGHT_SCRAPERS = {
    "Safety4Sea Jobs": scrape_safety4sea,
    "Viking Crew":     scrape_viking_crew,
}
