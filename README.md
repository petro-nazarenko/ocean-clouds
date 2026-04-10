# ⚓ Ocean Clouds

**Maritime job search for all seafarer ranks** — aggregates vacancies from job boards, crewing agency portals, and Telegram channels.

- 🌐 **Landing page**: `docs/` → deploy on GitHub Pages
- 🔌 **Claude Code plugin**: 4 skills for power users
- 🐍 **Python scraper**: BS4 + Playwright + Telethon

---

## Quick start

```bash
git clone https://github.com/petro-nazarenko/ocean-clouds
cd ocean-clouds
pip install -r requirements.txt
playwright install chromium
cp .env.example .env
```

### CLI usage

```bash
# Search all sources
python -m scraper.cli search

# Filter by rank and vessel
python -m scraper.cli search --rank "Chief Officer" --vessel Tanker

# Filter cached results
python -m scraper.cli filter --salary 6000 --urgent

# List all sources
python -m scraper.cli sources

# Test source connectivity
python -m scraper.cli sources --test-all
```

---

## Claude Code plugin

```bash
# Install the plugin (from repo root)
# Claude Code auto-discovers .claude-plugin/plugin.json

/ocean-clouds:search Chief Officer Tanker North Sea
/ocean-clouds:tg --since 48
/ocean-clouds:filter --salary 7000 --urgent
/ocean-clouds:sources
```

Skills:

| Skill | Description |
|---|---|
| `/ocean-clouds:search` | Search all sources. Args: rank, vessel type, region |
| `/ocean-clouds:tg` | Fetch Telegram channels. Args: `--limit`, `--since`, `--channel` |
| `/ocean-clouds:filter` | Filter cached results. Args: `--rank`, `--vessel`, `--salary`, `--urgent` |
| `/ocean-clouds:sources` | List/test all configured sources |

---

## Telegram setup

1. Get API credentials at **https://my.telegram.org/apps**
2. Add to `.env`:
   ```
   TG_API_ID=12345678
   TG_API_HASH=abcdef1234567890abcdef1234567890
   ```
3. First-time auth (one time only):
   ```bash
   python -m scraper.telegram --setup
   ```
   You'll receive a confirmation code in Telegram.

> **Note:** The `.session` file contains your auth token. It is gitignored — never commit it.

---

## Adding sources

**New job board** — edit `scraper/config.py`:
```python
JOB_SITES.append({
    "name": "My Source",
    "url": "https://example.com/jobs",
    "type": "bs4",   # or "playwright" for JS-rendered sites
    "enabled": True,
})
```
Then add a scraper function in `scraper/sites.py` (or `dynamic.py`) and register it in `BS4_SCRAPERS` / `PLAYWRIGHT_SCRAPERS`.

**New Telegram channel**:
```python
TELEGRAM_SOURCES.append({
    "name": "My Channel",
    "username": "channel_handle",   # without @
    "type": "channel",              # or "group"
    "enabled": True,
})
```

---

## Landing page (GitHub Pages)

The `docs/` directory is a self-contained static site.

**Deploy:**
1. Push to GitHub
2. Settings → Pages → Source: `Deploy from branch` → `main` / `docs`
3. Page will be live at `https://petro-nazarenko.github.io/ocean-clouds`

**Email alerts:** Create a free form at [formspree.io](https://formspree.io), then replace `YOUR_FORM_ID` in `docs/index.html` line:
```html
action="https://formspree.io/f/YOUR_FORM_ID"
```

---

## Project structure

```
ocean-clouds/
  .claude-plugin/
    plugin.json          Claude Code plugin manifest
  skills/
    search.md            /ocean-clouds:search
    tg-fetch.md          /ocean-clouds:tg
    filter.md            /ocean-clouds:filter
    sources.md           /ocean-clouds:sources
  scraper/
    config.py            All source URLs and Telegram channels
    models.py            Vacancy dataclass + cache I/O
    sites.py             BeautifulSoup scrapers (static sites)
    dynamic.py           Playwright scrapers (JS-rendered sites)
    telegram.py          Telethon-based Telegram fetcher
    aggregator.py        Parallel fetch, dedup, cache
    cli.py               python -m scraper.cli entry point
  docs/
    index.html           Landing page (GitHub Pages)
    style.css            Dark ocean theme
    app.js               Search form + alert subscription
  requirements.txt
  .env.example
  .gitignore
  README.md
```

---

## Selector maintenance

Web scrapers break when sites redesign. If a scraper stops returning results:

1. Open the site in browser → Inspect Element on a vacancy card
2. Find the CSS selector for the card container
3. Update the `card.select()` call in `scraper/sites.py` for that scraper

Each scraper function has a `notes` field in `config.py` with hints.

---

## License

MIT — built for the maritime community.
