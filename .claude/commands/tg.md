Fetch latest maritime job posts from configured Telegram channels and groups.

Run:

```bash
cd /data/data/com.termux/files/home/ocean-clouds && python -m scraper.telegram fetch $ARGUMENTS
```

Display results grouped by channel, showing:
- Channel name
- Message date/time
- Extracted rank, vessel type, salary (if detected)
- Direct Telegram link

Highlight posts containing: urgent/immediate, salary mentions, rank keywords.

If credentials missing, guide the user:
```
Run: python -m scraper.telegram --setup
You need TG_API_ID and TG_API_HASH from https://my.telegram.org/apps
```

Example usage:
- `/tg` — last 24h from all channels
- `/tg --since 48 --limit 100`
- `/tg --channel @seafarer_jobs`
