import discord
from discord import app_commands
from discord.ext import commands
import time
import logging

logger = logging.getLogger("discord-bot.health")

class Health(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    # --- Classic command for latency/uptime ---
    @commands.command(name="ping")
    async def ping(self, ctx):
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

    # --- Slash command version of ping ---
    @app_commands.command(name="ping", description="Check bot latency, uptime, and server count")
    async def ping_slash(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
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
        logger.info("Ping slash command used.")

    # --- Shutdown (classic command) ---
    @commands.command(name="shutdown")
    @commands.is_owner()
    async def shutdown(self, ctx):
        await ctx.send("⚠️ Shutting down bot...")
        logger.info("Shutdown invoked via classic command.")
        await self.bot.close()

    # --- Shutdown (slash command) ---
    @app_commands.command(name="shutdown", description="Shutdown the bot (owner only)")
    async def shutdown_slash(self, interaction: discord.Interaction):
        app_owner = await self.bot.application_info()
        if interaction.user.id != app_owner.owner.id:
            await interaction.response.send_message("🚫 You don’t have permission to shut down the bot.", ephemeral=True)
            return
        await interaction.response.send_message("⚠️ Shutting down bot...", ephemeral=True)
        logger.info(f"Shutdown invoked via slash command by {interaction.user}.")
        await self.bot.close()


async def setup(bot: commands.Bot):
    await bot.add_cog(Health(bot))
