import discord
from discord import app_commands
from discord.ext import commands
import time
import logging

logger = logging.getLogger("discord-bot.health")

class Health(commands.Cog):
    """Health-related commands: ping and shutdown"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="ping", description="Check bot latency, uptime, and server count")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)  # ms
        uptime = time.time() - self.start_time

        days, remainder = divmod(int(uptime), 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"

        embed = discord.Embed(title="🤖 Bot Health Check", color=discord.Color.green())
        embed.add_field(name="Latency", value=f"{latency} ms", inline=True)
        embed.add_field(name="Uptime", value=uptime_str, inline=True)
        embed.add_field(name="Servers", value=str(len(self.bot.guilds)), inline=True)

        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info("Ping command used.")

    @app_commands.command(name="shutdown", description="Shutdown the bot (owner only)")
    async def shutdown(self, interaction: discord.Interaction):
        if await self.bot.is_owner(interaction.user):
            await interaction.response.send_message("⚠️ Shutting down bot...", ephemeral=True)
            logger.info(f"Shutdown invoked by {interaction.user}")
            await self.bot.close()
        else:
            await interaction.response.send_message(
                "🚫 You don’t have permission to shut down the bot.", ephemeral=True
            )
            logger.warning(f"Unauthorized shutdown attempt by {interaction.user}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Health(bot))
