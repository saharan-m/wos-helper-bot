import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from utils.storage import load_json, save_json

logger = logging.getLogger("discord-bot.admin")

SETTINGS_FILE = "data/settings.json"

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.admins = set(load_json(SETTINGS_FILE, {}).get("admins", []))
        self.owner_id = None
        self._retry_task = None

    async def cog_load(self):
        # Start retry loop until owner_id is fetched
        self._retry_task = self.retry_fetch_owner.start()

    async def cog_unload(self):
        if self._retry_task:
            self._retry_task.cancel()

    @tasks.loop(seconds=10)
    async def retry_fetch_owner(self):
        """Keep retrying until we fetch the bot owner successfully."""
        try:
            app_info = await self.bot.application_info()
            self.owner_id = app_info.owner.id
            self.bot.owner_id = self.owner_id
            logger.info(f"✅ Bot owner set to {self.owner_id}")
            self.retry_fetch_owner.stop()  # success, stop retrying
        except Exception as e:
            logger.warning(f"⚠️ Retrying fetch owner info failed: {e}")

    @retry_fetch_owner.before_loop
    async def before_retry_fetch_owner(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_connect(self):
        """Retry fetching owner whenever the bot reconnects to Discord."""
        if not self.owner_id or not self.bot.owner_id:
            logger.info("🔄 Bot reconnected — retrying fetch owner.")
            if not self.retry_fetch_owner.is_running():
                self.retry_fetch_owner.start()

    def is_admin_or_owner(self, user: discord.User) -> bool:
        return user.id in self.admins or (self.owner_id and user.id == self.owner_id)

    @app_commands.command(name="addadmin", description="Add a user as bot admin (owner only)")
    async def add_admin(self, interaction: discord.Interaction, member: discord.Member):
        if not self.owner_id or interaction.user.id != self.owner_id:
            await interaction.response.send_message("🚫 Only the bot owner can add admins.", ephemeral=True)
            return

        self.admins.add(member.id)
        settings = load_json(SETTINGS_FILE, {})
        settings["admins"] = list(self.admins)
        save_json(SETTINGS_FILE, settings)

        await interaction.response.send_message(f"✅ {member.mention} has been added as an admin.", ephemeral=True)
        logger.info(f"Added admin: {member} ({member.id})")

    @app_commands.command(name="removeadmin", description="Remove a bot admin (owner only)")
    async def remove_admin(self, interaction: discord.Interaction, member: discord.Member):
        if not self.owner_id or interaction.user.id != self.owner_id:
            await interaction.response.send_message("🚫 Only the bot owner can remove admins.", ephemeral=True)
            return

        if member.id in self.admins:
            self.admins.remove(member.id)
            settings = load_json(SETTINGS_FILE, {})
            settings["admins"] = list(self.admins)
            save_json(SETTINGS_FILE, settings)

            await interaction.response.send_message(f"🗑️ {member.mention} has been removed as an admin.", ephemeral=True)
            logger.info(f"Removed admin: {member} ({member.id})")
        else:
            await interaction.response.send_message(f"⚠️ {member.mention} is not an admin.", ephemeral=True)

    @app_commands.command(name="listadmins", description="List all current admins (owner only)")
    async def list_admins(self, interaction: discord.Interaction):
        if not self.owner_id or interaction.user.id != self.owner_id:
            await interaction.response.send_message("🚫 Only the bot owner can list admins.", ephemeral=True)
            return

        if not self.admins:
            await interaction.response.send_message("ℹ️ No admins set.", ephemeral=True)
            return

        members = [f"<@{aid}>" for aid in self.admins]
        await interaction.response.send_message("👑 Current admins:\n" + "\n".join(members), ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))
