import discord
from discord.ext import commands
import asyncio
import logging
import os

# === Logging Setup ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("discord-bot")

# === Bot Setup ===
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None  # We use slash commands instead
)

# === Load Extensions ===
async def load_extensions():
    extensions = [
        "cogs.users",
        "cogs.codes",
        "cogs.reminders",
        "cogs.health",
        "cogs.help",
        "cogs.settings",
        "cogs.auto_redeem",
        "cogs.verify",
        "cogs.admin"
    ]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"✅ Loaded extension: {ext}")
        except Exception as e:
            logger.error(f"❌ Failed to load extension {ext}: {e}")

# === Sync slash commands with Discord ===
@bot.event
async def on_ready():
    logger.info(f"🤖 Bot is online as {bot.user} (ID: {bot.user.id})")
    # Register slash commands globally (can take up to 1 hour) or per guild for instant update
    # For development/testing, use guild-specific IDs to speed up
    GUILD_IDS = []  # Optional: add guild IDs to sync immediately
    if GUILD_IDS:
        for guild_id in GUILD_IDS:
            guild = discord.Object(id=guild_id)
            await bot.tree.sync(guild=guild)
            logger.info(f"🔄 Synced slash commands to guild {guild_id}")
    else:
        await bot.tree.sync()
        logger.info("🔄 Synced global slash commands")

    await bot.change_presence(activity=discord.Game(name="Use /help"))

# === Main Entrypoint ===
async def main():
    # Ensure data folder exists
    if not os.path.exists("data"):
        os.makedirs("data")

    # Load token
    token_file = "data/token.txt"
    if os.path.exists(token_file):
        with open(token_file, "r") as f:
            TOKEN = f.read().strip()
            logger.info("🔑 Loaded token from token.txt")
    else:
        TOKEN = input("Enter your Discord bot token: ").strip()
        with open(token_file, "w") as f:
            f.write(TOKEN)
        logger.info("🔑 Token saved to token.txt")

    await load_extensions()
    await bot.start(TOKEN)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually")
