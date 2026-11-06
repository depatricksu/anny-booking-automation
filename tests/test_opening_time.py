import datetime

import pytz

from main import _today_at

TZ = pytz.timezone("Europe/Berlin")


def at(y, mo, d, h, mi):
    return TZ.localize(datetime.datetime(y, mo, d, h, mi))


def test_midnight_opening_found_before_midnight():
    # LMU: opens 00:00; run starts Friday 23:50 → next opening is Saturday 00:00
    assert _today_at("00:00:00", TZ, now=at(2026, 11, 6, 23, 50)) == at(2026, 11, 7, 0, 0)


def test_opening_later_today_unchanged():
    # KIT-style evening opening, run at 19:05
    assert _today_at("19:14:00", TZ, now=at(2026, 11, 6, 19, 5)) == at(2026, 11, 6, 19, 14)


def test_just_passed_opening_stays_today():
    assert _today_at("00:00:00", TZ, now=at(2026, 11, 7, 0, 1)) == at(2026, 11, 7, 0, 0)
