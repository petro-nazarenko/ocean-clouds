"""Configuration for all maritime job sources."""

# ---------------------------------------------------------------------------
# Job sites — fetched as raw text, then parsed by LLM
# No CSS selectors needed. Just the URL.
# ---------------------------------------------------------------------------
JOB_SITES = [
    {
        "name": "UkrCrewingUA",
        "url": "https://ukrcrewing.com.ua/ua/vacancy/?on_page=50&v_sort=0&v_sort_dir=0",
        "enabled": True,
    },
    {
        "name": "MarineJobs",
        "url": "https://www.marinejobs.net/vacancies",
        "enabled": True,
    },
    {
        "name": "SeafarerJobs",
        "url": "https://www.seafarerjobs.com/jobs",
        "enabled": True,
    },
    # Add more job boards here — LLM handles any site structure
    # {"name": "My Site", "url": "https://example.com/jobs", "enabled": True},
]

# ---------------------------------------------------------------------------
# Telegram channels and groups
# ---------------------------------------------------------------------------
TELEGRAM_SOURCES = [
    {"name": "Seafarer Jobs Global",   "username": "seafarer_jobs",          "type": "channel", "enabled": True},
    {"name": "Marine Vacancies",       "username": "marine_vacancies",        "type": "channel", "enabled": True},
    {"name": "Crew Vacancies Global",  "username": "crew_vacancies_global",   "type": "channel", "enabled": True},
    {"name": "Offshore Jobs",          "username": "offshore_vacancies",      "type": "channel", "enabled": True},
    {"name": "Maritime Jobs UA",       "username": "maritime_jobs_ukraine",   "type": "channel", "enabled": True},
    {"name": "Моряки України",         "username": "moryaki_ua",              "type": "channel", "enabled": True},
    {"name": "Ships Crew Intl",        "username": "ships_crew_jobs",         "type": "group",   "enabled": True},
    {"name": "Offshore Crew Network",  "username": "offshore_crew_network",   "type": "group",   "enabled": True},
    # Private groups: add id instead of username
    # {"name": "My Group", "id": -1001234567890, "type": "group", "enabled": True},
]

# ---------------------------------------------------------------------------
# Rank keywords — used by Telegram scraper for job-post filtering
# ---------------------------------------------------------------------------
RANK_KEYWORDS = {
    "Master / Captain":    ["master", "captain", "commanding officer"],
    "Chief Officer":       ["chief officer", "chief mate", "first officer"],
    "Second Officer":      ["second officer", "second mate", "2nd officer"],
    "Third Officer":       ["third officer", "third mate", "3rd officer"],
    "Deck Cadet":          ["deck cadet", "nautical cadet"],
    "Chief Engineer":      ["chief engineer", "c/e"],
    "Second Engineer":     ["second engineer", "2nd engineer", "2/e"],
    "Third Engineer":      ["third engineer", "3rd engineer", "3/e"],
    "Fourth Engineer":     ["fourth engineer", "4th engineer", "4/e"],
    "ETO / Electrician":   ["eto", "electrician", "electro-technical officer"],
    "Engine Cadet":        ["engine cadet"],
    "Bosun":               ["bosun", "boatswain"],
    "AB":                  [" ab ", "able seaman", "able bodied"],
    "OS":                  [" os ", "ordinary seaman"],
    "Fitter":              ["fitter"],
    "Oiler":               ["oiler"],
    "Wiper":               ["wiper"],
    "Cook":                ["cook", "chief cook"],
    "Steward":             ["steward", "messman"],
    "DP Operator":         ["dp operator", "dynamic positioning"],
    "Crane Operator":      ["crane operator"],
    "OIM":                 ["oim", "offshore installation manager"],
    "Barge Master":        ["barge master"],
    "ROV Pilot":           ["rov pilot", "rov supervisor"],
    "Diver":               ["diver", "saturation diver"],
}

# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------
CACHE_DIR         = ".cache"
TG_CACHE_DIR      = ".tg_cache"
CACHE_TTL_HOURS   = 2
TG_CACHE_TTL_HOURS = 1

# ---------------------------------------------------------------------------
# HTTP fetch settings
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 15
REQUEST_DELAY   = 1.0
MAX_RETRIES     = 2
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
