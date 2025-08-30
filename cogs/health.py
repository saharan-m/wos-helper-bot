import discord
from discord.ext import commands
import time
import logging

logger = logging.getLogger("discord-bot.health")

class Health(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.command(name="ping")
    async def ping(self, ctx):
        """Check bot latency, uptime, and server count"""
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

        await ctx.send(embed=embed)
        logger.info("Ping command used.")

    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx):
        """Shutdown the bot (bot owner only)"""
        await ctx.send("⚠️ Shutting down bot...")
        logger.info("Shutdown invoked via Discord command.")
        await self.bot.close()

    @shutdown.error
    async def shutdown_error(self, ctx, error):
        if isinstance(error, commands.NotOwner):
            await ctx.send("🚫 You don’t have permission to shut down the bot.")

async def setup(bot):
    await bot.add_cog(Health(bot))
