"""Standalone check: pasted-text extraction (the /event_from_text path). Run: python test_text_extract.py"""
import asyncio
import os
os.environ.setdefault("DISCORD_TOKEN", "x")
os.environ.setdefault("GUILD_ID", "1")
os.environ.setdefault("EVENT_CHANNEL_ID", "1")
os.environ.setdefault("CCA_ROLE_ID", "1")
os.environ.setdefault("ORGANISER_ROLE_ID", "1")
os.environ["DB_PATH"] = ":memory:"

import bot as m

TEXT = """Ready to dive into the world of binary exploitation? Join Gryphons for an introductory workshop on PWN, where you'll learn the fundamentals of low-level vulnerability research and binary exploitation.
📅 Date: 30 July 2026, Thursday
🕢 Time: 7:30 PM – 9:00 PM
💻 Venue: Online
We look forward to seeing you there!"""


async def main():
    extracted = await m.ai_extract_event("", TEXT)
    print("EXTRACTED:", extracted)
    assert extracted, "model returned nothing"
    assert extracted.get("date") == "2026-07-30", extracted
    assert extracted.get("time") == "19:30", extracted
    event_name = extracted.get("name") or TEXT.strip().split("\n")[0][:100]
    assert event_name, "no fallback name"
    print("ok")


asyncio.run(main())
