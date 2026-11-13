# 📚 Anny Booking Automation — LMU edition

Automatically books **LMU library group rooms and study seats** on [anny.eu](https://anny.eu)
the moment they are released, every week, with no server of your own.

> **Credit:** this is a fork of
> [wiestju/anny-booking-automation](https://github.com/wiestju/anny-booking-automation)
> (MIT License, © 2025 github.com/wiestju), which built the original tool for KIT and TUM.
> This fork adds LMU München support and a fully automated weekly setup. All original
> licensing terms apply; see [LICENSE](LICENSE).

⚠️ Please use it responsibly; see [DISCLAIMER](DISCLAIMER.md). It books with your own
account, one room per time slot, exactly as you could by hand.

## What this fork adds

| Change | Why |
| --- | --- |
| **LMU login** (`SSO_PROVIDER=lmu`) | Signs in through LMU's Shibboleth login (`lmuidp.lrz.de`) with your LMU campus ID. |
| **LMU library terms** (`ACCEPT_AGREEMENTS=lmu-ub`) | LMU's library requires its own Terms of Use / Privacy Policy checkbox at checkout; without it every booking is rejected. |
| **Midnight releases** | LMU releases slots **7 days ahead at 00:00**. The original only looked for openings later the same day, so a run started at 23:50 never booked. |
| **Per-weekday times** (`BOOKING_TIMES_BY_WEEKDAY`) | e.g. Friday 13–17, Tuesday 16–20, Sunday 15–19, each day with its own window. |
| **Semester end** (`BOOK_UNTIL`) | Stops booking after a date, e.g. `2027-03-31`. |
| **One booking per run** (`MAX_BOOKINGS=1`) | Treats several time windows as alternatives: first one that books wins. |
| **Fresh login before the release** | If a run starts long before midnight, it sleeps and logs in again 4 minutes before, so the session doesn't expire. |
| **Several accounts** (`ENV_FILE`, `scripts/run_all.sh`) | e.g. an LMU and a TUM login side by side, one settings file each. |
| **Honest results** | A checkout rejected for missing terms is reported as *NOT booked* instead of "Secured". |
| **Fixes** | Account-ID detection for LMU's anny pages; the workflow now passes `SSO_PROVIDER` (it was missing). |

KIT and TUM work as before.

## How LMU releases rooms

- Every LMU area on anny releases slots **7 days in advance at 00:00** (Berlin time).
  On Thursday at midnight, the Friday one week later opens.
- Popular slots (e.g. Philologicum group rooms in the afternoon) are gone **within minutes**,
  so the booking has to fire right at midnight.
- Philologicum has 4 group rooms, bookable for up to 4 hours.

Check the release times yourself with `python scripts/check_advance.py`.

## Full automation: cron-job.org + GitHub Actions

GitHub's own scheduler is **not** reliable enough for a midnight release. In testing it
started 3 h 20 min late once and skipped a run entirely. So the run is started by
[cron-job.org](https://cron-job.org) (free, minute-exact), and GitHub Actions does the booking.

```
cron-job.org (every night 23:50 Berlin)
   └─▶ GitHub API: start workflow "Library Reservation"
          └─▶ logs in via LMU → waits → logs in again at 23:56 → books at 00:00
              (exits right away on nights where the target day isn't one you want)
```

### 1. Copy the repo

Fork it, or create a new **private** repo and push this code into it. Your credentials live
in GitHub Secrets, never in the code.

### 2. GitHub Secrets and Variables

In your repo: **Settings → Secrets and variables → Actions**.

**Secrets:**

| Secret | Value |
| --- | --- |
| `LMU_USERNAME` | your LMU campus ID (or LMU e-mail) |
| `LMU_PASSWORD` | your LMU password |

**Variables** (example: Philologicum group rooms three times a week until semester end):

| Variable | Example |
| --- | --- |
| `LMU_ACCEPT_AGREEMENTS` | `lmu-ub` *(required for LMU)* |
| `LMU_FLOORS` | `philologicum` |
| `LMU_BOOKING_TIMES_BY_WEEKDAY` | `fri=13:00-17:00; tue=16:00-20:00; sun=15:00-19:00` |
| `LMU_BOOK_DAYS_AHEAD` | `7` |
| `LMU_BOOK_UNTIL` | `2027-03-31` |
| `LMU_SNIPE_ACTIVATE_MIN` | `45` |

Every variable can be set per university (`LMU_…`, `TUM_…`) or without a prefix for all.
A university whose `<UNI>_USERNAME` secret is missing is skipped.

### 3. GitHub token

Create a fine-grained token at **github.com/settings/personal-access-tokens/new**:

- **Repository access:** only select repositories → your copy of this repo
- **Permissions:** **Actions → Read and write** (in the newer UI: *Add permissions* → Actions → change *Read-only* to *Read and write*)

### 4. cron-job.org job

Create a free account at [cron-job.org](https://cron-job.org) and add one job:

| Setting | Value |
| --- | --- |
| URL | `https://api.github.com/repos/YOUR_USER/YOUR_REPO/actions/workflows/schedule.yml/dispatches` |
| Schedule | every day, **23:50**, time zone **Europe/Berlin** |
| Request method | `POST` |
| Headers | `Accept: application/vnd.github+json` and `Authorization: Bearer YOUR_TOKEN` |
| Request body | `{"ref":"main"}` |

Create **only one** job. The workflow has a lock so runs never overlap, but a second trigger
could still book a second room.

A successful trigger returns HTTP **204**. `401` means the token is wrong, `404` usually means the token lacks
*Actions: Read and write*, and `422` means the body is missing. cron-job.org's *Test run* button may
fail with a verification error inside some embedded browsers; try it in a normal browser,
or wait for the first scheduled run and check the job's **History**.

### 5. Check the results

In your repo under **Actions → Library Reservation**, each run's log shows
`✅ BOOKED resource=… ` or the reason it didn't book (`0 available`, `NOT booked — terms`, …).

## Run it locally

```bash
python -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example lmu.env      # fill in USERNAME, PASSWORD, SSO_PROVIDER="lmu", ACCEPT_AGREEMENTS="lmu-ub"
```

Useful commands (all read-only except the last two):

```bash
ENV_FILE=lmu.env venv/bin/python scripts/check_advance.py     # areas and their release times
ENV_FILE=lmu.env venv/bin/python scripts/list_resources.py    # room/seat names for PREFERRED_RESOURCES
ENV_FILE=lmu.env venv/bin/python main.py                      # one booking run
scripts/run_all.sh                                            # one run per *.env file, in parallel
```

`*.env` files are git-ignored, so your password is never committed.
In `opening` mode a run exits unless a release is within `SNIPE_ACTIVATE_MIN` minutes.
Set `BOOKING_MODE="immediate"` to book whatever is free right now.

## All settings

| Variable | Default | Description |
| --- | --- | --- |
| `USERNAME`, `PASSWORD` | — | University login (required). |
| `SSO_PROVIDER` | `kit` | `kit`, `tum` or `lmu`. |
| `ACCEPT_AGREEMENTS` | *(none)* | Library-specific checkout agreements you accept, e.g. `lmu-ub`. |
| `BOOKING_MODE` | `opening` | `opening` = book at the release time; `immediate` = book what's free now. |
| `BOOK_DAYS_AHEAD` | `4` | Book the day this many days ahead (`7` for LMU). |
| `BOOKING_TIMES` | 3 windows | `HH:MM:SS-HH:MM:SS`, comma-separated, in priority order. |
| `BOOKING_TIMES_BY_WEEKDAY` | *(none)* | Windows per target weekday; overrides `BOOKING_TIMES` and `BOOK_WEEKDAYS`. |
| `BOOK_WEEKDAYS` | *(every day)* | Only book these target weekdays, e.g. `fri` or `mon,wed`. |
| `BOOK_UNTIL` | *(none)* | Last bookable day, `YYYY-MM-DD`. |
| `MAX_BOOKINGS` | *(per window)* | `1` = windows are alternatives, stop after the first booking. |
| `FLOORS` | *(all)* | Areas in priority order (name substrings), e.g. `philologicum`. |
| `PREFERRED_RESOURCES` | *(none)* | Favorite seats/rooms tried first. |
| `USE_ANNY_FAVORITES` | `True` | Also prioritize what you starred in anny. |
| `SNIPE_ACTIVATE_MIN` | `20` | Only stay running if a release is within N minutes. |
| `RELOGIN_LEAD_MIN` | `4` | Log in again N minutes before the release after a long wait. |
| `ENV_FILE` | `.env` | Which settings file to load. |
| `DEBUG` | `False` | Verbose request logging. |

## Development

```bash
venv/bin/pip install ruff pytest
venv/bin/ruff check . --exclude venv
venv/bin/pytest
```

The tests need no credentials or network.

## License

[MIT](LICENSE). Original work © 2025 [wiestju](https://github.com/wiestju/anny-booking-automation);
LMU support and automation changes in this fork are released under the same license.
