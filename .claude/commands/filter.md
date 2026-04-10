Filter the cached maritime job results without re-fetching all sources.

Run:

```bash
cd /data/data/com.termux/files/home/ocean-clouds && python -m scraper.cli filter $ARGUMENTS
```

If no cache exists (.cache/last_results.json missing), tell the user to run `/search` first.

Show filtered results as a markdown table. End with: `Showing N of M results after filters.`

Available filters:
- `--rank VALUE` — fuzzy match (e.g. "eng" matches all engineers)
- `--vessel VALUE` — fuzzy match vessel type
- `--region VALUE` — fuzzy match region
- `--salary MIN` — minimum salary in USD
- `--duration MAX` — max contract length in months
- `--source VALUE` — filter by source site or "telegram"
- `--urgent` — only urgent/immediate positions

Examples:
- `/filter --rank engineer --salary 6000`
- `/filter --vessel offshore --urgent`
- `/filter --source telegram`
