"""Standalone check: Microsoft Forms scrape (headless render) + local model extraction.
Run: python test_msform_extract.py
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

# public Microsoft Forms example, confirmed live during dev (not event-related -
# this test only proves the render/scrape pipeline works, not date/time accuracy,
# see test_form_extract.py and test_text_extract.py for that)
URL = ("https://forms.office.com/pages/responsepage.aspx?"
       "id=n9_vioCHv0aPt0ySRlOovupaSgomKdtAgAzmQnuCl2NUNU5WUEVHUU1TSzhUMDVYSTFLNU5DTUdTTi4u"
       "&route=shorturl")


async def main():
    title, description = await m.fetch_msform_text(URL)
    print("TITLE:", title)
    print("DESC (first 300):", description[:300])
    assert title and title != "Untitled Event"
    assert len(description) > 20

    extracted = await m.ai_extract_event(title, description)
    print("EXTRACTED:", extracted)
    assert extracted is not None
    print("ok (manually verify date/time above are sane - no fixed ground truth for this public template)")


asyncio.run(main())
