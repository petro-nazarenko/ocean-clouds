Search maritime job vacancies from all configured sources.

Run this command to fetch jobs:

```bash
cd /data/data/com.termux/files/home/ocean-clouds && python -m scraper.cli search $ARGUMENTS
```

Display the results in a clean markdown table with columns: Rank | Vessel | Company | Salary | Duration | Source | Link

Group results: job boards first, then Telegram posts.

Show a summary line at the end: `Found N vacancies across M sources`.

If a source fails, skip it and note which ones were unreachable.

If Telegram credentials are missing (.env not configured), skip Telegram and suggest:
`python -m scraper.telegram --setup`

If Playwright is not installed, skip dynamic sites and suggest:
`pip install playwright && playwright install chromium`

Example usage:
- `/search` — all ranks, all sources  
- `/search Chief Officer Tanker` — filtered
- `/search AB` — ratings only
