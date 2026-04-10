# ⚓ Ocean Clouds

**Maritime job search for all seafarer ranks.**

Fetches job board pages + Telegram channels, then uses Claude AI to extract structured vacancy data — no fragile CSS selectors, works on any site.

- 🌐 **Landing page** → [petro-nazarenko.github.io/ocean-clouds](https://petro-nazarenko.github.io/ocean-clouds)
- 🔌 **Claude Code plugin** — 4 slash commands
- 🐍 **Python** — requests + Claude API + Telethon

---

## How it works

```
1. fetch.py    — GET job site pages, strip to plain text
2. llm.py      — Claude Haiku reads text, returns vacancies as JSON
3. telegram.py — Telethon pulls messages from configured channels
4. aggregator  — combines, deduplicates, caches results
```

No CSS selectors. New site → add URL to `config.py`, done.

---

## Setup

```bash
git clone https://github.com/petro-nazarenko/ocean-clouds
cd ocean-clouds
pip install -r requirements.txt
cp .env.example .env
# Edit .env — add ANTHROPIC_API_KEY (required) and TG credentials (optional)
```

Get your API key: **https://console.anthropic.com/** → API Keys

---

## Usage

### CLI

```bash
python -m scraper.cli search                          # all sources
python -m scraper.cli search --rank "Chief Officer"   # filtered
python -m scraper.cli search --no-telegram            # skip Telegram
python -m scraper.cli filter --salary 5000 --urgent   # filter cache
python -m scraper.cli sources                         # list sources
```

### Claude Code plugin

```
/search Chief Officer Tanker
/search AB --no-telegram
/tg --since 48
/filter --rank engineer --salary 6000
/sources
```

---

## Add sources

**Job board** — edit `scraper/config.py`:
```python
JOB_SITES.append({
    "name": "My Site",
    "url": "https://example.com/jobs",
    "enabled": True,
})
```
No scraper code needed — Claude handles the extraction automatically.

**Telegram channel/group**:
```python
TELEGRAM_SOURCES.append({
    "name": "My Channel",
    "username": "channel_handle",
    "type": "channel",
    "enabled": True,
})
```

### Telegram auth (first time)

```bash
python -m scraper.telegram --setup
# You need TG_API_ID + TG_API_HASH from https://my.telegram.org/apps
```

---

## Project structure

```
ocean-clouds/
  .claude/commands/       Claude Code slash commands
  scraper/
    config.py             Job site URLs + Telegram sources
    models.py             Vacancy dataclass + cache
    fetch.py              Simple HTTP page fetcher
    llm.py                Claude API vacancy extraction
    telegram.py           Telethon channel/group reader
    aggregator.py         Orchestrates fetch + LLM + cache
    cli.py                python -m scraper.cli entry point
  docs/                   GitHub Pages landing page
  requirements.txt
  .env.example
```

---

## License

MIT
