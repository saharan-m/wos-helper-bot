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

# === Custom Help Command ===
class MyHelpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        embed = discord.Embed(
            title="🤖 Bot Commands",
            description="Here’s a list of available commands:",
            color=discord.Color.green()
        )
        for page in self.paginator.pages:
            embed.add_field(name="Commands", value=page, inline=False)
        await destination.send(embed=embed)

# === Bot Setup ===
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True  # Needed to read command text
intents.members = True          # Needed for user lookups

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=MyHelpCommand()
)

# === Load Extensions ===
async def load_extensions():
    extensions = ["cogs.users", "cogs.codes", "cogs.reminders", "cogs.health"]
    for ext in extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"✅ Loaded extension: {ext}")
        except Exception as e:
            logger.error(f"❌ Failed to load extension {ext}: {e}")

@bot.event
async def on_ready():
    logger.info(f"🤖 Bot is online as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="!help for commands"))

# === Main Entrypoint ===
async def main():
    # Ensure token.txt exists or ask for token
    token_file = "data/token.txt"
    if not os.path.exists("data"):
        os.makedirs("data")

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
