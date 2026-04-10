"""
Simple page fetcher — no parsing, no selectors.
Just GET the URL and return clean text for LLM extraction.
"""
import logging
import time
import requests
from bs4 import BeautifulSoup

from .config import REQUEST_TIMEOUT, REQUEST_DELAY, MAX_RETRIES, USER_AGENT

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept-Language": "en-US,en;q=0.9,uk;q=0.8",
    "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
}


def fetch_text(url: str) -> str:
    """Fetch a URL and return readable text (HTML stripped). Empty string on failure."""
    session = requests.Session()
    session.headers.update(HEADERS)

    for attempt in range(MAX_RETRIES + 1):
        try:
            r = session.get(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "head", "noscript", "svg", "img"]):
                tag.decompose()
            text = soup.get_text(separator="\n", strip=True)
            # Collapse blank lines
            lines = [l for l in text.splitlines() if l.strip()]
            return "\n".join(lines)
        except requests.exceptions.HTTPError as e:
            log.warning("HTTP %s for %s — not retrying", e.response.status_code, url)
            return ""
        except requests.RequestException as e:
            log.warning("Fetch attempt %d/%d failed for %s: %s", attempt + 1, MAX_RETRIES + 1, url, e)
            if attempt < MAX_RETRIES:
                time.sleep(REQUEST_DELAY * 2)

    log.error("All attempts failed for %s", url)
    return ""


def fetch_all_sites(sites: list[dict]) -> list[dict]:
    """
    Fetch text from all enabled sites.
    Returns list of {"name": ..., "url": ..., "text": ...}
    """
    results = []
    for site in sites:
        if not site.get("enabled", True):
            continue
        name = site["name"]
        url  = site["url"]
        log.info("Fetching %s", name)
        text = fetch_text(url)
        if text:
            log.info("%s — got %d chars", name, len(text))
            results.append({"name": name, "url": url, "text": text})
        else:
            log.warning("%s — empty response, skipping", name)
        time.sleep(REQUEST_DELAY)
    return results
