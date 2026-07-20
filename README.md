# CCA Event Reminder Bot

Discord bot for CCA event announcements + automatic `@CCA` role reminders.

## Setup

1. Install Python 3.12+.
2. `pip install -r requirements.txt`
3. Copy `.env.example` to `.env`, fill in:
   - `DISCORD_TOKEN` — Bot tab on https://discord.com/developers/applications
   - `GUILD_ID` — right-click server icon → Copy Server ID (enable Developer Mode first: User Settings → Advanced)
   - `EVENT_CHANNEL_ID` — right-click the announcements channel → Copy Channel ID
   - `CCA_ROLE_ID` — right-click the `CCA` role in Server Settings → Roles → Copy Role ID
   - `ORGANISER_ROLE_ID` — same, for the organiser/committee role
4. In Server Settings → Roles, drag the bot's own role above `CCA` and the organiser role (needed to assign/remove them).
5. Run:
   ```
   python bot.py
   ```
6. In the event channel, run `/cca_panel` once to post the Join/Leave buttons.

## Commands

- `/event_add name date time description [location] [remind_before]` — organiser only. Date `YYYY-MM-DD`, time 24h `HH:MM`.
- `/event_list` — upcoming events.
- `/event_delete event_id` — organiser only.
- `/cca_join` / `/cca_leave` — anyone.
- `/cca_panel` — admin only, posts persistent Join/Leave buttons.

## Notes

- SQLite file (`events.db`) sits next to `bot.py`; back it up if you care about event history.
- Reminder scheduler checks every 30s, fires once per event, survives restarts.
- Timezone hardcoded to `Asia/Singapore`.
