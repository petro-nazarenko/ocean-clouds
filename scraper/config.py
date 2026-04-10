"""Configuration for all maritime job sources."""

# ---------------------------------------------------------------------------
# Job board URLs
# type: "bs4"       — static HTML, scraped with BeautifulSoup + requests
# type: "playwright" — JavaScript-rendered, scraped with Playwright
# ---------------------------------------------------------------------------
JOB_SITES = [
    {
        "name": "AllCrewing",
        "url": "https://allcrewing.com/vacancies",
        "type": "bs4",
        "enabled": True,
        "notes": "Large international database. Inspect vacancy cards for selector updates.",
    },
    {
        "name": "Maritime Connector",
        "url": "https://maritime-connector.com/seafarer-jobs/",
        "type": "bs4",
        "enabled": True,
        "notes": "EU-focused, well-structured HTML.",
    },
    {
        "name": "SeafarerJobs",
        "url": "https://www.seafarerjobs.com/jobs",
        "type": "bs4",
        "enabled": True,
        "notes": "Global listings, good rank metadata.",
    },
    {
        "name": "MarineJobs",
        "url": "https://www.marinejobs.net/vacancies",
        "type": "bs4",
        "enabled": True,
    },
    {
        "name": "Crewtoo",
        "url": "https://www.crewtoo.com/maritime-jobs",
        "type": "bs4",
        "enabled": True,
    },
    {
        "name": "Safety4Sea Jobs",
        "url": "https://jobs.safety4sea.com/search-jobs/",
        "type": "playwright",
        "enabled": True,
        "notes": "JS-rendered job board.",
    },
    {
        "name": "Viking Crew",
        "url": "https://www.vikingcrewing.com/crew/vacancies",
        "type": "playwright",
        "enabled": True,
        "notes": "Large Norwegian crewing company.",
    },
    {
        "name": "Barents Group",
        "url": "https://www.barentsgroup.com/vacancies",
        "type": "bs4",
        "enabled": True,
    },
    {
        "name": "Jobs.ua Maritime",
        "url": "https://www.jobs.ua/ukr/vacancies-in-sphere-marine_vessels/",
        "type": "bs4",
        "enabled": True,
        "notes": "Ukrainian job board, maritime category.",
    },
    {
        "name": "Work.ua Maritime",
        "url": "https://www.work.ua/jobs-sea/",
        "type": "bs4",
        "enabled": True,
        "notes": "Ukrainian job board, sea/shipping category.",
    },
    {
        "name": "Cadet Jobs",
        "url": "https://www.cadetships.com/vacancies",
        "type": "bs4",
        "enabled": True,
        "notes": "Cadet and entry-level positions.",
    },
    {
        "name": "Offshore Center",
        "url": "https://offshore-center.com/jobs",
        "type": "bs4",
        "enabled": True,
        "notes": "Offshore-specific vacancies.",
    },
]

# ---------------------------------------------------------------------------
# Telegram sources
# type: "channel" — broadcast channel (read-only)
# type: "group"   — group chat (read messages if member)
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
    # Add private groups by invite link or ID:
    # {"name": "My Private Group", "username": None, "id": -1001234567890, "type": "group", "enabled": True},
]

# ---------------------------------------------------------------------------
# Rank taxonomy (used for filtering and keyword extraction from Telegram)
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
# Vessel type taxonomy
# ---------------------------------------------------------------------------
VESSEL_TYPES = [
    "Container", "Bulk Carrier", "Tanker", "Chemical Tanker",
    "LNG", "LPG", "VLCC", "Aframax", "Suezmax",
    "PSV", "AHTS", "MPSV", "Offshore", "Drillship",
    "Cruise", "Ferry", "Ro-Ro", "Reefer",
    "General Cargo", "Dredger", "Tug", "Salvage",
    "Research", "Cable Layer", "Heavy Lift",
]

# ---------------------------------------------------------------------------
# Cache settings
# ---------------------------------------------------------------------------
CACHE_DIR = ".cache"
TG_CACHE_DIR = ".tg_cache"
CACHE_TTL_HOURS = 2          # How long to use cached results before re-fetching
TG_CACHE_TTL_HOURS = 1       # Telegram cache TTL

# ---------------------------------------------------------------------------
# Scraper behaviour
# ---------------------------------------------------------------------------
REQUEST_TIMEOUT = 15         # seconds
REQUEST_DELAY = 1.5          # seconds between requests (be polite)
MAX_RETRIES = 2
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
