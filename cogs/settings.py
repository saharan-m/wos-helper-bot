import discord
from discord import app_commands
from discord.ext import commands
from utils.storage import load_json, save_json

SETTINGS_FILE = "data/settings.json"

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setchannel", description="Set the default channel for notifications")
    @app_commands.describe(channel="Mention the channel")
    async def setchannel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        settings = load_json(SETTINGS_FILE, {})
        settings["channel_id"] = channel.id
        save_json(SETTINGS_FILE, settings)
        await interaction.response.send_message(
            f"✅ Notifications will now go to {channel.mention}", ephemeral=True
        )

async def setup(bot):
    await bot.add_cog(Settings(bot))
