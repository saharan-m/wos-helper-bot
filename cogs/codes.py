import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from utils.scraper import scrape_active_codes
from utils.storage import load_json, save_json

logger = logging.getLogger("discord-bot.codes")

SETTINGS_FILE = "data/settings.json"

class Codes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.previous_codes = set()
        self.alert_channel_id = None
        self.check_codes.start()

        settings = load_json(SETTINGS_FILE, {})
        self.alert_channel_id = settings.get("alert_channel_id")

    def get_admin_cog(self):
        return self.bot.get_cog("Admin")

    def is_admin_or_owner(self, user: discord.User) -> bool:
        admin_cog = self.get_admin_cog()
        if not admin_cog:
            return False
        return admin_cog.is_admin_or_owner(user)

    @app_commands.command(name="setalert", description="Set the alert channel for new gift codes (admins only)")
    async def set_alert_channel(self, interaction: discord.Interaction):
        if not self.is_admin_or_owner(interaction.user):
            await interaction.response.send_message("🚫 You don’t have permission to set the alert channel.", ephemeral=True)
            return

        self.alert_channel_id = interaction.channel.id
        settings = load_json(SETTINGS_FILE, {})
        settings["alert_channel_id"] = self.alert_channel_id
        save_json(SETTINGS_FILE, settings)

        await interaction.response.send_message(
            f"✅ This channel is now set for gift code alerts: {interaction.channel.mention}",
            ephemeral=True
        )
        logger.info(f"Alert channel set to {interaction.channel.name} ({interaction.channel.id})")

    @app_commands.command(name="codes", description="Show active gift codes")
    async def show_active_codes(self, interaction: discord.Interaction):
        active_codes = await scrape_active_codes()
        if not active_codes:
            await interaction.response.send_message("⚠️ No active gift codes found.", ephemeral=True)
            return
        message = "**🎁 Active WOS Gift Codes:**\n" + "\n".join(f"• `{c}`" for c in active_codes)
        await interaction.response.send_message(message, ephemeral=True)

    @tasks.loop(minutes=15)
    async def check_codes(self):
        try:
            active_codes = await scrape_active_codes()
        except Exception as e:
            logger.error(f"Failed to scrape codes: {e}")
            return

        new_codes = [c for c in active_codes if c not in self.previous_codes]
        if not new_codes or not self.alert_channel_id:
            return

        self.previous_codes.update(new_codes)
        channel = self.bot.get_channel(self.alert_channel_id)
        if not channel:
            logger.warning(f"Alert channel {self.alert_channel_id} not found.")
            return

        for code in new_codes:
            await channel.send(f"🎉 @everyone New WOS Gift Code: `{code}`")
            logger.info(f"Notified new code: {code}")

    @check_codes.before_loop
    async def before_check_codes(self):
        await self.bot.wait_until_ready()

async def setup(bot: commands.Bot):
    await bot.add_cog(Codes(bot))
