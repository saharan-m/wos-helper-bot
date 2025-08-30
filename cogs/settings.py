from discord.ext import commands
from utils.storage import load_json, save_json

SETTINGS_FILE = "data/settings.json"

class Settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def setchannel(self, ctx, channel: commands.TextChannelConverter):
        """Set the default channel for notifications. Usage: !setchannel #channel"""
        settings = load_json(SETTINGS_FILE, {})
        # channel param comes as Channel object when using annotation, but to be safe:
        ch = getattr(channel, "id", None) or channel
        settings["channel_id"] = ch
        save_json(SETTINGS_FILE, settings)
        await ctx.send(f"✅ Notifications will now go to {ctx.message.channel.mention if ch == ctx.channel.id else f'<#{ch}>'}")

async def setup(bot):
    await bot.add_cog(Settings(bot))
