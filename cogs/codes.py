import discord
from discord.ext import commands, tasks
import logging
from utils.scraper import scrape_active_codes  # your scraper function

logger = logging.getLogger('discord-bot')

class Codes(commands.Cog):
    """Handles gift code scraping and notifications."""

    def __init__(self, bot):
        self.bot = bot
        self.previous_codes = set()
        self.alert_channel_id = None  # store alert channel ID
        self.check_codes.start()

    @commands.command(name="setalert")
    async def set_alert_channel(self, ctx):
        """Set the channel for gift code alerts."""
        self.alert_channel_id = ctx.channel.id
        await ctx.send(f"✅ This channel has been set for gift code alerts: {ctx.channel.mention}")
        logger.info(f"Alert channel set to {ctx.channel.name} ({ctx.channel.id})")

    @commands.command(name="codes")
    async def show_active_codes(self, ctx):
        """Show current active codes."""
        active_codes = await scrape_active_codes()
        if not active_codes:
            await ctx.send("⚠️ No active gift codes found at the moment.")
            return

        message = "**🎁 Active WOS Gift Codes:**\n"
        for code in active_codes:
            message += f"• `{code}`\n"

        await ctx.send(message)

    @tasks.loop(minutes=15)
    async def check_codes(self):
        """Background task that scrapes website and notifies on new codes."""
        try:
            active_codes = await scrape_active_codes()
        except Exception as e:
            logger.error(f"Failed to scrape codes: {e}")
            return

        new_codes = [code for code in active_codes if code not in self.previous_codes]

        if not new_codes:
            return  # nothing new

        self.previous_codes.update(new_codes)

        if not self.alert_channel_id:
            logger.warning("No alert channel set; skipping notification.")
            return

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
