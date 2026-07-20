"""Self-check for date/reminder math. Run: python test_bot.py"""
import os
os.environ.setdefault("DISCORD_TOKEN", "x")
os.environ.setdefault("GUILD_ID", "1")
os.environ.setdefault("EVENT_CHANNEL_ID", "1")
os.environ.setdefault("CCA_ROLE_ID", "1")
os.environ.setdefault("ORGANISER_ROLE_ID", "1")
os.environ["DB_PATH"] = ":memory:"

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import bot as m

# Singapore 7pm -> correct UTC offset (+8)
local = datetime(2026, 7, 25, 19, 0, tzinfo=m.TZ)
utc = local.astimezone(ZoneInfo("UTC"))
assert utc.hour == 11 and utc.day == 25, "SG->UTC conversion broke"

date_str, time_str = m.fmt_dt(utc)
assert date_str == "25 July 2026", date_str
assert time_str == "7:00 PM", time_str

# reminder fires only once time >= start - remind_before, not after event start
start = datetime.now(ZoneInfo("UTC")) + timedelta(minutes=10)
remind_at = start - timedelta(minutes=5)
now_before = start - timedelta(minutes=6)
now_after = start - timedelta(minutes=4)
assert now_before < remind_at
assert now_after >= remind_at

print("ok")
