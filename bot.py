"""Discord CCA event reminder bot. One file, MVP scope."""
import os
import sqlite3
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import discord
from discord import app_commands
from discord.ext import tasks
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ["DISCORD_TOKEN"]
GUILD_ID = int(os.environ["GUILD_ID"])
EVENT_CHANNEL_ID = int(os.environ["EVENT_CHANNEL_ID"])
CCA_ROLE_ID = int(os.environ["CCA_ROLE_ID"])
ORGANISER_ROLE_ID = int(os.environ["ORGANISER_ROLE_ID"])
TZ = ZoneInfo("Asia/Singapore")
DB_PATH = os.environ.get("DB_PATH", "events.db")

REMIND_CHOICES = [
    app_commands.Choice(name="5 minutes", value=5),
    app_commands.Choice(name="10 minutes", value=10),
    app_commands.Choice(name="15 minutes", value=15),
    app_commands.Choice(name="30 minutes", value=30),
    app_commands.Choice(name="1 hour", value=60),
    app_commands.Choice(name="2 hours", value=120),
    app_commands.Choice(name="1 day", value=1440),
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("cca-bot")

os.makedirs(os.path.dirname(DB_PATH) or ".", exist_ok=True)
db = sqlite3.connect(DB_PATH)
db.execute("""
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    creator_id TEXT,
    name TEXT,
    description TEXT,
    location TEXT,
    start_time_utc TEXT,
    remind_before_minutes INTEGER,
    reminder_sent INTEGER DEFAULT 0,
    status TEXT DEFAULT 'scheduled'
)
""")
db.commit()


def is_organiser(interaction: discord.Interaction) -> bool:
    if interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_guild:
        return True
    return any(r.id == ORGANISER_ROLE_ID for r in interaction.user.roles)


def fmt_dt(dt_utc: datetime) -> tuple[str, str]:
    local = dt_utc.astimezone(TZ)
    hour12 = local.strftime("%I").lstrip("0") or "12"
    return f"{local.day} {local.strftime('%B %Y')}", f"{hour12}:{local.strftime('%M %p')}"


class CCARoleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Join Notifications", style=discord.ButtonStyle.success, custom_id="cca_join")
    async def join(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(CCA_ROLE_ID)
        try:
            await interaction.user.add_roles(role)
            await interaction.response.send_message("You have joined CCA event notifications.", ephemeral=True)
        except discord.Forbidden:
            log.error("role assign failed for %s", interaction.user.id)
            await interaction.response.send_message(
                "Could not assign CCA role. Bot role must be above CCA role.", ephemeral=True)

    @discord.ui.button(label="Leave Notifications", style=discord.ButtonStyle.danger, custom_id="cca_leave")
    async def leave(self, interaction: discord.Interaction, button: discord.ui.Button):
        role = interaction.guild.get_role(CCA_ROLE_ID)
        try:
            await interaction.user.remove_roles(role)
            await interaction.response.send_message("You will no longer receive CCA event notifications.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("Could not remove CCA role.", ephemeral=True)


class Bot(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents(guilds=True, members=True))
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(CCARoleView())
        await self.tree.sync(guild=discord.Object(id=GUILD_ID))
        reminder_loop.start()

    async def on_ready(self):
        log.info("logged in as %s", self.user)


client = Bot()
guild_obj = discord.Object(id=GUILD_ID)


@client.tree.command(name="event_add", description="Create a CCA event", guild=guild_obj)
@app_commands.describe(name="Event name", date="YYYY-MM-DD", time="HH:MM (24h)",
                        description="Event description", location="Location (optional)",
                        remind_before="Reminder timing (default 5 minutes)")
@app_commands.choices(remind_before=REMIND_CHOICES)
async def event_add(interaction: discord.Interaction, name: str, date: str, time: str,
                     description: str, location: str = None,
                     remind_before: app_commands.Choice[int] = None):
    if not is_organiser(interaction):
        await interaction.response.send_message("You do not have permission to manage events.", ephemeral=True)
        return
    if len(name) > 100 or len(description) > 1000 or (location and len(location) > 200):
        await interaction.response.send_message("Name/description/location too long.", ephemeral=True)
        return
    try:
        naive = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    except ValueError:
        await interaction.response.send_message(
            "Invalid date/time. Use YYYY-MM-DD and 24h HH:MM.", ephemeral=True)
        return
    start_local = naive.replace(tzinfo=TZ)
    start_utc = start_local.astimezone(ZoneInfo("UTC"))
    now_utc = datetime.now(ZoneInfo("UTC"))
    if start_utc <= now_utc:
        await interaction.response.send_message("Event must be scheduled in the future.", ephemeral=True)
        return
    remind_minutes = remind_before.value if remind_before else 5
    if now_utc + timedelta(minutes=remind_minutes) > start_utc:
        await interaction.response.send_message("Reminder time is longer than time remaining before event.", ephemeral=True)
        return

    cur = db.execute(
        "INSERT INTO events (creator_id, name, description, location, start_time_utc, remind_before_minutes) "
        "VALUES (?, ?, ?, ?, ?, ?)",
        (str(interaction.user.id), name, description, location, start_utc.isoformat(), remind_minutes))
    db.commit()
    event_id = cur.lastrowid
    log.info("event %s created by %s", event_id, interaction.user.id)

    date_str, time_str = fmt_dt(start_utc)
    embed = discord.Embed(title=f"✅ Event created\n\n{name}", description=description, color=discord.Color.blue())
    embed.add_field(name="📅 Date", value=date_str, inline=True)
    embed.add_field(name="🕖 Time", value=time_str, inline=True)
    if location:
        embed.add_field(name="📍 Location", value=location, inline=True)
    embed.add_field(name="🔔 Reminder", value=f"{remind_minutes} minutes before", inline=False)
    embed.set_footer(text=f"Event ID: {event_id}")
    await interaction.response.send_message(embed=embed)


@client.tree.command(name="event_list", description="List upcoming events", guild=guild_obj)
async def event_list(interaction: discord.Interaction):
    now_utc = datetime.now(ZoneInfo("UTC")).isoformat()
    rows = db.execute(
        "SELECT id, name, location, start_time_utc, remind_before_minutes FROM events "
        "WHERE status='scheduled' AND start_time_utc > ? ORDER BY start_time_utc",
        (now_utc,)).fetchall()
    if not rows:
        await interaction.response.send_message("No upcoming events.")
        return
    lines = ["**Upcoming Events**\n"]
    for eid, name, location, start_utc, remind in rows:
        d, t = fmt_dt(datetime.fromisoformat(start_utc))
        lines.append(f"**#{eid} {name}**\n{d}, {t}" + (f" @ {location}" if location else "") +
                      f"\nReminder: {remind} minutes before\n")
    await interaction.response.send_message("\n".join(lines))


@client.tree.command(name="event_delete", description="Delete an event", guild=guild_obj)
@app_commands.describe(event_id="Event ID")
async def event_delete(interaction: discord.Interaction, event_id: int):
    if not is_organiser(interaction):
        await interaction.response.send_message("You do not have permission to manage events.", ephemeral=True)
        return
    row = db.execute("SELECT name FROM events WHERE id=?", (event_id,)).fetchone()
    if not row:
        await interaction.response.send_message(f"Event #{event_id} could not be found.", ephemeral=True)
        return
    db.execute("UPDATE events SET status='deleted' WHERE id=?", (event_id,))
    db.commit()
    log.info("event %s deleted by %s", event_id, interaction.user.id)
    await interaction.response.send_message(f"Deleted event #{event_id}: {row[0]}")


@client.tree.command(name="cca_join", description="Join CCA event notifications", guild=guild_obj)
async def cca_join(interaction: discord.Interaction):
    role = interaction.guild.get_role(CCA_ROLE_ID)
    try:
        await interaction.user.add_roles(role)
        await interaction.response.send_message("You have joined CCA event notifications.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Could not assign CCA role.", ephemeral=True)


@client.tree.command(name="cca_leave", description="Leave CCA event notifications", guild=guild_obj)
async def cca_leave(interaction: discord.Interaction):
    role = interaction.guild.get_role(CCA_ROLE_ID)
    try:
        await interaction.user.remove_roles(role)
        await interaction.response.send_message("You will no longer receive CCA event notifications.", ephemeral=True)
    except discord.Forbidden:
        await interaction.response.send_message("Could not remove CCA role.", ephemeral=True)


@client.tree.command(name="cca_panel", description="Post the CCA role panel (admin only)", guild=guild_obj)
async def cca_panel(interaction: discord.Interaction):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Admin only.", ephemeral=True)
        return
    embed = discord.Embed(title="🔔 CCA Event Notifications",
                           description="Join this role to receive reminders about upcoming CCA events.",
                           color=discord.Color.blue())
    await interaction.response.send_message(embed=embed, view=CCARoleView())


@tasks.loop(seconds=30)
async def reminder_loop():
    now_utc = datetime.now(ZoneInfo("UTC"))
    rows = db.execute(
        "SELECT id, name, description, location, start_time_utc, remind_before_minutes FROM events "
        "WHERE status='scheduled' AND reminder_sent=0")
    channel = client.get_channel(EVENT_CHANNEL_ID)
    for eid, name, description, location, start_utc_s, remind_minutes in rows.fetchall():
        start_utc = datetime.fromisoformat(start_utc_s)
        reminder_time = start_utc - timedelta(minutes=remind_minutes)
        if now_utc < reminder_time:
            continue
        if now_utc >= start_utc:
            db.execute("UPDATE events SET status='completed' WHERE id=?", (eid,))
            db.commit()
            continue
        d, t = fmt_dt(start_utc)
        mins_left = int((start_utc - now_utc).total_seconds() // 60)
        embed = discord.Embed(title=name, description=description, color=discord.Color.gold())
        embed.add_field(name="📅 Date", value=d, inline=True)
        embed.add_field(name="🕖 Time", value=t, inline=True)
        if location:
            embed.add_field(name="📍 Location", value=location, inline=True)
        try:
            await channel.send(content=f"🔔 <@&{CCA_ROLE_ID}> {name} starts in {mins_left} minutes!", embed=embed)
            db.execute("UPDATE events SET reminder_sent=1 WHERE id=?", (eid,))
            db.commit()
            log.info("reminder sent for event %s", eid)
        except discord.HTTPException as e:
            log.error("reminder send failed for event %s: %s", eid, e)


if __name__ == "__main__":
    client.run(TOKEN)
