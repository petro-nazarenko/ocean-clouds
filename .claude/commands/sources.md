List and manage all configured maritime job sources.

Run:

```bash
cd /data/data/com.termux/files/home/ocean-clouds && python -m scraper.cli sources $ARGUMENTS
```

Default (no args): show two tables — Job Boards and Telegram Channels — with name, URL/handle, type, enabled status.

With `--test-all`: ping every source and show HTTP status + response time.

To add sources, edit `scraper/config.py`:
- Job boards → `JOB_SITES` list
- Telegram → `TELEGRAM_SOURCES` list
