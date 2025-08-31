import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
import asyncio
from utils import api, storage

log = logging.getLogger("discord-bot.verify")

USERS_FILE = "data/users.json"
UNVERIFIED_ROLE_NAME = "Unverified"
VERIFIED_ROLE_NAME = "Verified"

class Verify(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        storage.ensure_data_dir()
        self.users = storage.load_json(USERS_FILE, {})
        self.sync_nicknames.start()

    def cog_unload(self):
        self.sync_nicknames.cancel()

    # --- Verification modal ---
    class VerifyModal(discord.ui.Modal):
        def __init__(self, cog, user):
            super().__init__(title="Verify your Game ID")
            self.cog = cog
            self.user = user
            self.add_item(discord.ui.TextInput(label="Enter your Game ID"))

        async def on_submit(self, interaction: discord.Interaction):
            game_id = self.children[0].value.strip()
            data = await api.get_player_info(game_id)
            if not data or "data" not in data:
                await interaction.response.send_message("❌ Invalid Game ID, try again.", ephemeral=True)
                return
            player = data["data"]

            # Update users.json
            self.cog.users[str(self.user.id)] = {
                "game_id": str(player.get("fid")),
                "nickname": player.get("nickname"),
                "state_id": player.get("kid"),
                "furnace_level": player.get("stove_lv"),
                "furnace_image": player.get("stove_lv_content"),
                "avatar": player.get("avatar_image"),
            }
            storage.save_json(USERS_FILE, self.cog.users)

            # Roles
            guild = self.user.guild
            verified_role = discord.utils.get(guild.roles, name=VERIFIED_ROLE_NAME)
            unverified_role = discord.utils.get(guild.roles, name=UNVERIFIED_ROLE_NAME)
            if unverified_role:
                await self.user.remove_roles(unverified_role)
            if verified_role:
                await self.user.add_roles(verified_role)

            # Update nickname
            try:
                await self.user.edit(nick=player.get("nickname"))
                log.info(f"Updated nickname for {self.user} to {player.get('nickname')}")
            except discord.Forbidden:
                log.warning(f"Missing permissions to update nickname for {self.user}")

            # Delete temporary channel
            try:
                await interaction.channel.delete()
            except Exception:
                pass

            await interaction.response.send_message(f"✅ Verified as {player.get('nickname')}!", ephemeral=True)

    # --- Event: new member joins ---
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if str(member.id) not in self.users:
            await self.assign_unverified(member)
            await self.send_verification_channel(member)

    async def assign_unverified(self, member):
        role = discord.utils.get(member.guild.roles, name=UNVERIFIED_ROLE_NAME)
        if role:
            await member.add_roles(role)

    async def send_verification_channel(self, member):
        overwrites = {
            member.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            member: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        temp_channel = await member.guild.create_text_channel(
            name=f"verify-{member.name}", overwrites=overwrites, reason="Verification channel"
        )
        modal = self.VerifyModal(self, member)
        view = discord.ui.View()
        button = discord.ui.Button(label="Verify", style=discord.ButtonStyle.green)
        async def button_callback(interaction: discord.Interaction):
            await interaction.response.send_modal(modal)
        button.callback = button_callback
        view.add_item(button)
        msg = await temp_channel.send(
            f"Hello {member.mention}, click the button below to verify your Game ID.", view=view
        )
        await asyncio.sleep(3600)  # auto-delete channel after 1 hour if still exists
        try:
            await temp_channel.delete()
        except Exception:
            pass

    # --- Event: member leaves ---
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if str(member.id) in self.users:
            del self.users[str(member.id)]
            storage.save_json(USERS_FILE, self.users)
            log.info(f"Deleted {member} from users.json due to leaving the server.")

    # --- Hourly nickname sync ---
    @tasks.loop(hours=1)
    async def sync_nicknames(self):
        for guild in self.bot.guilds:
            for member in guild.members:
                uid = str(member.id)
                if uid in self.users:
                    target_nick = self.users[uid].get("nickname")
                    if target_nick and member.nick != target_nick:
                        try:
                            await member.edit(nick=target_nick)
                            log.info(f"Synced nickname for {member} to {target_nick}")
                        except discord.Forbidden:
                            log.warning(f"Missing permissions to sync nickname for {member}")

    @sync_nicknames.before_loop
    async def before_sync(self):
        await self.bot.wait_until_ready()


async def setup(bot: commands.Bot):
    await bot.add_cog(Verify(bot))
