import discord
from discord import app_commands
from discord.ext import commands
from utils import api, storage
import json, os, logging

logger = logging.getLogger("discord-bot.users")
DATA_FILE = "data/users.json"

def load_users():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        logger.error("users.json corrupt, resetting")
        return {}

def save_users(users):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w") as f:
        json.dump(users, f, indent=2)

class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = load_users()

    @app_commands.command(name="register", description="Register your WOS Game ID")
    @app_commands.describe(game_id="Your Whiteout Survival Game ID")
    async def register(self, interaction: discord.Interaction, game_id: str):
        discord_id = str(interaction.user.id)
        data = await api.get_player_info(game_id)
        if not data or "data" not in data:
            await interaction.response.send_message(
                f"⚠️ Failed to fetch data for Game ID `{game_id}`.", ephemeral=True
            )
            return
        player = data["data"]
        # Save user info
        self.users[discord_id] = {
            "game_id": str(player.get("fid")),
            "nickname": player.get("nickname"),
            "state_id": player.get("kid"),
            "furnace_level": player.get("stove_lv"),
            "furnace_image": player.get("stove_lv_content"),
            "avatar": player.get("avatar_image"),
        }
        save_users(self.users)
        try:
            await interaction.user.edit(nick=player.get("nickname"))
        except discord.Forbidden:
            logger.warning(f"Missing permission to update nickname for {interaction.user}")
        await interaction.response.send_message(
            f"✅ Registered **{player.get('nickname')}** (Game ID: {player.get('fid')})",
            ephemeral=True
        )

    @app_commands.command(name="userinfo", description="Get player info")
    @app_commands.describe(target="Mention user or enter Game ID (optional)")
    async def userinfo(self, interaction: discord.Interaction, target: str = None):
        game_id = None
        member = None
        if target is None:
            discord_id = str(interaction.user.id)
            if discord_id not in self.users:
                await interaction.response.send_message(
                    "❌ You are not registered.", ephemeral=True
                )
                return
            game_id = self.users[discord_id]["game_id"]
            member = interaction.user
        elif interaction.guild and target in [m.mention for m in interaction.guild.members]:
            member = interaction.guild.get_member(int(target.strip("<@!>")))
            if not member or str(member.id) not in self.users:
                await interaction.response.send_message(
                    f"❌ {target} is not registered.", ephemeral=True
                )
                return
            game_id = self.users[str(member.id)]["game_id"]
        else:
            game_id = target

        data = await api.get_player_info(game_id)
        if not data or "data" not in data:
            await interaction.response.send_message(
                f"⚠️ Failed to fetch info for Game ID `{game_id}`.", ephemeral=True
            )
            return
        player = data["data"]
        embed = discord.Embed(
            title=f"🎮 Player Info: {player.get('nickname')}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=player.get("avatar_image"))
        embed.add_field(name="Game ID", value=player.get("fid"), inline=True)
        embed.add_field(name="State ID", value=player.get("kid"), inline=True)
        embed.add_field(name="Furnace Level", value=player.get("stove_lv"), inline=True)
        embed.set_image(url=player.get("stove_lv_content"))
        if member:
            embed.set_footer(text=f"Requested by {interaction.user}", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Users(bot))
