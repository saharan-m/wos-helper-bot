import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone, date
import asyncio
import logging

log = logging.getLogger("discord-bot")

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    # --- Utility: forgiving time parser ---
    def parse_time(self, input_str: str) -> datetime:
        """
        Parse 'YYYY-MM-DD HH:MM UTC' or 'HH:MM UTC'.
        Case-insensitive, flexible spacing, defaults to today's date if not given.
        """
        input_str = input_str.strip().upper().replace("  ", " ")

        if not input_str.endswith("UTC"):
            raise ValueError("Time must end with 'UTC'")

        # Remove UTC suffix
        input_str = input_str[:-3].strip()

        # Try full date format first
        try:
            return datetime.strptime(input_str, "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        except ValueError:
            pass

        # Try time-only format (defaults to today)
        try:
            t = datetime.strptime(input_str, "%H:%M").time()
            return datetime.combine(date.today(), t).replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError("Invalid time format. Use 'HH:MM UTC' or 'YYYY-MM-DD HH:MM UTC'")

    # --- Commands ---
    @commands.command(name="remindonce")
    async def remind_once(self, ctx, time_str: str, tz: str, *, message: str):
        """Set a one-time reminder. Format:
        !remindonce HH:MM UTC <message>
        !remindonce YYYY-MM-DD HH:MM UTC <message>
        """
        try:
            target_time = self.parse_time(f"{time_str} {tz}")
        except ValueError as e:
            await ctx.send(f"❌ {e}")
            return

        reminder = {
            "channel_id": ctx.channel.id,
            "message": message,
            "time": target_time,
            "once": True
        }
        self.reminders.append(reminder)
        await ctx.send(f"✅ One-time reminder set for {target_time.strftime('%Y-%m-%d %H:%M UTC')}.")

    @commands.command(name="remind")
    async def remind(self, ctx, time_str: str, tz: str, *, message: str):
        """Set a recurring daily reminder. Format:
        !remind HH:MM UTC <message>
        """
        try:
            target_time = self.parse_time(f"{time_str} {tz}")
        except ValueError as e:
            await ctx.send(f"❌ {e}")
            return

        reminder = {
            "channel_id": ctx.channel.id,
            "message": message,
            "time": target_time,
            "once": False
        }
        self.reminders.append(reminder)
        await ctx.send(f"✅ Daily reminder set for {target_time.strftime('%H:%M UTC')}.")

    # --- Background loop ---
    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now(timezone.utc)
        for reminder in list(self.reminders):  # Copy so we can remove safely
            delta = (reminder["time"] - now).total_seconds()

            # If within 30s, switch to fine-grained 5s checks
            if 0 <= delta <= 30:
                await asyncio.sleep(delta)  # Wait until exact moment
                channel = self.bot.get_channel(reminder["channel_id"])
                if channel:
                    await channel.send(f"@everyone ⏰ Reminder: {reminder['message']}")
                if reminder["once"]:
                    self.reminders.remove(reminder)
                else:
                    reminder["time"] += timedelta(days=1)

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminder(bot))
