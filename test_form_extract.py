"""Standalone check: form scrape + local model extraction. Run: python test_form_extract.py"""
import asyncio
import os
os.environ.setdefault("DISCORD_TOKEN", "x")
os.environ.setdefault("GUILD_ID", "1")
os.environ.setdefault("EVENT_CHANNEL_ID", "1")
os.environ.setdefault("CCA_ROLE_ID", "1")
os.environ.setdefault("ORGANISER_ROLE_ID", "1")
os.environ["DB_PATH"] = ":memory:"

import bot as m

URL = "https://docs.google.com/forms/d/e/1FAIpQLSeROUvvdzjSExcGA5qb93rgfe_MRfiHclnCYwvNgOZtrMUhmg/viewform"


async def main():
    title, description = await m.fetch_form_text(URL)
    print("TITLE:", title)
    print("DESC:", description[:200], "...")
    assert "PWN" in title
    assert "Date" in description

    extracted = await m.ai_extract_event(title, description)
    print("EXTRACTED:", extracted)
    assert extracted, "model returned nothing"
    assert extracted.get("date") == "2026-07-30", extracted
    assert extracted.get("time") == "19:30", extracted
    print("ok")


asyncio.run(main())
