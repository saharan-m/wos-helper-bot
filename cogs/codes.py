import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from utils.scraper import scrape_active_codes

logger = logging.getLogger('discord-bot.codes')

class Codes(commands.Cog):
    """Handles gift code scraping and notifications."""

    def __init__(self, bot):
        self.bot = bot
        self.previous_codes = set()
        self.alert_channel_id = None
        self.check_codes.start()

    @app_commands.command(name="setalert", description="Set the channel for gift code alerts")
    async def set_alert_channel(self, interaction: discord.Interaction):
        self.alert_channel_id = interaction.channel.id
        await interaction.response.send_message(
            f"✅ This channel has been set for gift code alerts: {interaction.channel.mention}", ephemeral=True
        )
        logger.info(f"Alert channel set to {interaction.channel.name} ({interaction.channel.id})")

    @app_commands.command(name="codes", description="Show current active WOS gift codes")
    async def show_active_codes(self, interaction: discord.Interaction):
        active_codes = await scrape_active_codes()
        if not active_codes:
            await interaction.response.send_message("⚠️ No active gift codes found at the moment.", ephemeral=True)
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
            logger.warning(f"Alert channel ID {self.alert_channel_id} not found.")
            return

        for code in new_codes:
            await channel.send(f"🎉 @everyone New WOS Gift Code: `{code}`")
            logger.info(f"Notified new code: {code}")

    @check_codes.before_loop
    async def before_check_codes(self):
        await self.bot.wait_until_ready()
        logger.info("Codes notifier is ready and background task starting.")

async def setup(bot):
    await bot.add_cog(Codes(bot))
