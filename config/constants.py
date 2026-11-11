from os import getenv

from dotenv import load_dotenv

AUTH_BASE_URL = "https://auth.anny.eu"
ANNY_BASE_URL = "https://anny.eu"
BOOKING_API_BASE = "https://b.anny.eu/api/v1"
CHECKOUT_FORM_API = "https://b.anny.eu/api/ui/checkout-form"

DEFAULT_HEADERS = {
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:140.0) Gecko/20100101 Firefox/140.0',
    'accept-encoding': 'plain'
}

# Get variables from dotenv file. ENV_FILE picks another file, e.g. one per
# university account: ENV_FILE=lmu.env python main.py
load_dotenv(getenv("ENV_FILE") or '.env', override=True)

USERNAME = getenv("USERNAME")
PASSWORD = getenv("PASSWORD")

TIMEZONE = getenv("TIMEZONE") or "Europe/Berlin"

# Provider — available: kit, tum, lmu (add more in auth/providers/)
SSO_PROVIDER = getenv("SSO_PROVIDER") or "kit"

# Resource config is optional: if unset, the tool auto-discovers all bookable
# floors/buildings for your account. Set these only to pin a single resource.
RESOURCE_URL_PATH = getenv("RESOURCE_URL_PATH")
SERVICE_ID = getenv("SERVICE_ID")
RESOURCE_URL = f"{BOOKING_API_BASE}{RESOURCE_URL_PATH}" if RESOURCE_URL_PATH else None

# Verbose request/error logging
DEBUG = getenv("DEBUG") == "True"

# ── Booking strategy ─────────────────────────────────────────────────────────
# "opening"   → wait for each floor's real advance_start_time and book calmly the
#               moment it opens (recommended; slots open ahead of time and are
#               uncontested for minutes). Self-adjusting: reads the times live.
# "immediate" → just book what is available right now (classic flow / testing).
BOOKING_MODE = (getenv("BOOKING_MODE") or "opening").strip().lower()

# Which day to book: today + this many days.
BOOK_DAYS_AHEAD = int(getenv("BOOK_DAYS_AHEAD") or "4")

# Floor selection & priority. Empty = auto-discover and use ALL floors. Otherwise
# a comma-separated priority list of name/slug substrings (case-insensitive).
FLOORS = [f.strip().lower() for f in (getenv("FLOORS") or "").split(",") if f.strip()]

# Favorite seats tried first within a floor (comma-separated, priority order;
# case-insensitive substring match against the seat name). A preference, not a filter.
PREFERRED_RESOURCES = [r.strip().lower() for r in (getenv("PREFERRED_RESOURCES") or "").split(",") if r.strip()]

# Also auto-prioritize the seats/floors you starred in anny itself.
# Empty/unset → default ON (unset CI variables become empty strings).
USE_ANNY_FAVORITES = (getenv("USE_ANNY_FAVORITES") or "True").strip().lower() not in ("false", "0", "no")

# "opening" mode only: wake up / log in only when the next opening is within this
# many minutes; otherwise exit silently so a cron heartbeat re-checks later.
SNIPE_ACTIVATE_MIN = int(getenv("SNIPE_ACTIVATE_MIN") or "20")

# "opening" mode only: after a floor opens, keep trying its seats for at most this
# long (absorbs clock jitter / a few seconds of "not yet open").
SNIPE_WINDOW_S = int(getenv("SNIPE_WINDOW_S") or "20")

# "opening" mode only: when the run starts long before the opening, sleep and
# log in again this many minutes before it (keeps the anny session fresh).
RELOGIN_LEAD_MIN = int(getenv("RELOGIN_LEAD_MIN") or "4")

# Organization-specific checkout agreements you accept for every booking
# (comma-separated keys of the "agreements.<key>" checkboxes), e.g. "lmu-ub" for
# the LMU library's Terms of Use / Privacy Policy. Only list ones you agreed to.
ACCEPT_AGREEMENTS = [a.strip() for a in (getenv("ACCEPT_AGREEMENTS") or "").split(",") if a.strip()]

# MAX_BOOKINGS=1 → BOOKING_TIMES become alternatives: tried one after another in
# priority order, stopping at the first success (one booking per run). Empty /
# 0 = book one resource per time window (default).
MAX_BOOKINGS = int(getenv("MAX_BOOKINGS") or "0")

# Last day that may be booked (YYYY-MM-DD), e.g. the end of the semester.
BOOK_UNTIL = (getenv("BOOK_UNTIL") or "").strip() or None

# Different time windows per weekday of the target day, e.g.
# "fri=13:00-17:00; tue=16:00-20:00; sun=15:00-19:00" (several windows per day:
# "fri=13:00-17:00,09:00-12:00"). When set, only these weekdays are booked and
# BOOKING_TIMES / BOOK_WEEKDAYS are ignored.
def _hms(t):
    t = t.strip()
    return t if t.count(":") == 2 else f"{t}:00"


BOOKING_TIMES_BY_WEEKDAY = {}
for _part in (getenv("BOOKING_TIMES_BY_WEEKDAY") or "").split(";"):
    if "=" not in _part:
        continue
    _day, _wins = _part.split("=", 1)
    _day = _day.strip().lower()[:3]
    if _day not in ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]:
        continue
    BOOKING_TIMES_BY_WEEKDAY[["mon", "tue", "wed", "thu", "fri", "sat", "sun"].index(_day)] = [
        {"start": _hms(w.split("-")[0]), "end": _hms(w.split("-")[1])}
        for w in _wins.split(",") if "-" in w
    ]

# Only book when the target day falls on one of these weekdays (comma-separated,
# e.g. "fri" or "mon,wed,fri"). Empty = every day.
_WEEKDAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
BOOK_WEEKDAYS = sorted({
    _WEEKDAY_NAMES.index(d.strip().lower()[:3])
    for d in (getenv("BOOK_WEEKDAYS") or "").split(",")
    if d.strip() and d.strip().lower()[:3] in _WEEKDAY_NAMES
})

# Print the services/opening-hours anny offers for the resource, then continue
DISCOVER_SLOTS = getenv("DISCOVER_SLOTS") == "True"

# Booking time slots (comma-separated HH:MM:SS-HH:MM:SS, in order of priority)
BOOKING_TIMES_CSV = getenv("BOOKING_TIMES") or "14:00:00-19:00:00, 09:00:00-13:00:00, 20:00:00-23:45:00"
BOOKING_TIMES = [
    {"start": b.split("-")[0].strip(), "end": b.split("-")[1].strip()}
    for b in BOOKING_TIMES_CSV.split(",") if "-" in b
]
