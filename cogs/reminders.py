import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone, date
import asyncio
import logging

log = logging.getLogger("discord-bot.reminder")

class Reminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders = []
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    def parse_time(self, input_str: str) -> datetime:
        input_str = input_str.strip().upper().replace("  ", " ")
        if not input_str.endswith("UTC"):
            raise ValueError("Time must end with 'UTC'")
        input_str = input_str[:-3].strip()
        for fmt in ["%Y-%m-%d %H:%M", "%H:%M"]:
            try:
                dt = datetime.strptime(input_str, fmt)
                if fmt == "%H:%M":
                    dt = datetime.combine(date.today(), dt.time())
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        raise ValueError("Invalid time format. Use 'HH:MM UTC' or 'YYYY-MM-DD HH:MM UTC'")

    @app_commands.command(name="remindonce", description="Set a one-time reminder")
    @app_commands.describe(time_str="Time (HH:MM UTC or YYYY-MM-DD HH:MM UTC)", message="Reminder message")
    async def remind_once(self, interaction: discord.Interaction, time_str: str, message: str):
        try:
            target_time = self.parse_time(time_str + " UTC")
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        reminder = {"channel_id": interaction.channel.id, "message": message, "time": target_time, "once": True}
        self.reminders.append(reminder)
        await interaction.response.send_message(
            f"✅ One-time reminder set for {target_time.strftime('%Y-%m-%d %H:%M UTC')}.", ephemeral=True
        )

    @app_commands.command(name="remind", description="Set a recurring daily reminder")
    @app_commands.describe(time_str="Time (HH:MM UTC)", message="Reminder message")
    async def remind(self, interaction: discord.Interaction, time_str: str, message: str):
        try:
            target_time = self.parse_time(time_str + " UTC")
        except ValueError as e:
            await interaction.response.send_message(f"❌ {e}", ephemeral=True)
            return

        reminder = {"channel_id": interaction.channel.id, "message": message, "time": target_time, "once": False}
        self.reminders.append(reminder)
        await interaction.response.send_message(
            f"✅ Daily reminder set for {target_time.strftime('%H:%M UTC')}.", ephemeral=True
        )

    @tasks.loop(seconds=30)
    async def check_reminders(self):
        now = datetime.now(timezone.utc)
        for reminder in list(self.reminders):
            delta = (reminder["time"] - now).total_seconds()
            if 0 <= delta <= 30:
                await asyncio.sleep(delta)
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
