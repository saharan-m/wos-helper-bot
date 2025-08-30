import logging
from discord.ext import commands, tasks
from utils.storage import load_json, save_json
from utils.api import redeem_code
from datetime import datetime

logger = logging.getLogger("discord-bot.auto_redeem")
USERS_FILE = "data/users.json"
LAST_CODES_FILE = "data/last_codes.json"
SETTINGS_FILE = "data/settings.json"

class AutoRedeem(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_codes.start()

    def cog_unload(self):
        self.check_codes.cancel()

    @tasks.loop(minutes=1)
    async def check_codes(self):
        await self.bot.wait_until_ready()
        # try to get Codes cog and call its scrape_codes (async)
        codes_cog = self.bot.get_cog("Codes")
        if not codes_cog:
            return
        try:
            codes = await codes_cog.scrape_codes()
        except Exception as e:
            logger.exception("Failed to scrape codes")
            return

        # extract active code strings
        active_codes = [c["code"] for c in codes if isinstance(c, dict) and not c.get("error")]
        last = load_json(LAST_CODES_FILE, [])
        new = [c for c in active_codes if c not in last]
        if not new:
            return

        users = load_json(USERS_FILE, [])
        settings = load_json(SETTINGS_FILE, {})
        channel_id = settings.get("channel_id")
        channel = self.bot.get_channel(channel_id) if channel_id else None

        for code in new:
            for u in users:
                fid = u.get("game_id")
                try:
                    result = await redeem_code(fid, code)
                except Exception as e:
                    logger.exception(f"redeem_code exception for fid={fid}, code={code}")
                    result = {"status":"error","message":str(e)}

                status_msg = "✅ Success" if result.get("status") == "ok" else f"⚠️ {result.get('message')}"
                if channel:
                    await channel.send(f"🎁 Auto-redeem attempt for **{code}** → <@{u['discord_id']}> : {status_msg}")

        # persist current active codes as last seen
        save_json(LAST_CODES_FILE, active_codes)
        logger.info(f"AutoRedeem processed new codes: {new}")

async def setup(bot):
    await bot.add_cog(AutoRedeem(bot))
