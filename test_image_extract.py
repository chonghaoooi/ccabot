"""Standalone check: screenshot OCR + local model extraction. Run: python test_image_extract.py
Needs scratch_form_screenshot.png present (generated ad hoc from a real form screenshot).
"""
import asyncio
import os
os.environ.setdefault("DISCORD_TOKEN", "x")
os.environ.setdefault("GUILD_ID", "1")
os.environ.setdefault("EVENT_CHANNEL_ID", "1")
os.environ.setdefault("CCA_ROLE_ID", "1")
os.environ.setdefault("ORGANISER_ROLE_ID", "1")
os.environ["DB_PATH"] = ":memory:"

import bot as m


async def main():
    image_bytes = open("scratch_form_screenshot.png", "rb").read()
    transcribed = m.read_image_text(image_bytes)
    print("TRANSCRIBED:", transcribed[:400])
    assert transcribed.strip()
    assert "PWN" in transcribed

    extracted = await m.ai_extract_event("", transcribed)
    print("EXTRACTED:", extracted)
    assert extracted
    print("ok (manually verify date=2026-07-30, time=19:30 above)")


asyncio.run(main())
