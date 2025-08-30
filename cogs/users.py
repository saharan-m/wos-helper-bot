import discord
from discord.ext import commands
import json
import os
import logging
from utils import api

logger = logging.getLogger("users")

DATA_FILE = "data/users.json"


class Users(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.users = self.load_users()

    def load_users(self):
        if not os.path.exists(DATA_FILE):
            return {}
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
                if not isinstance(data, dict):  # 🚑 ensure dict, not list
                    logger.warning("users.json was not a dict, resetting to {}")
                    return {}
                return data
            except json.JSONDecodeError:
                logger.error("❌ Failed to load users.json (corrupt). Resetting.")
                return {}

    def save_users(self):
        os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(self.users, f, indent=2)

    @commands.command(name="register")
    async def register(self, ctx, game_id: str):
        """Register your Whiteout Survival game ID"""
        discord_id = str(ctx.author.id)

        data = await api.get_player_info(game_id)
        if not data or "data" not in data:
            await ctx.send(f"⚠️ Failed to fetch data for Game ID `{game_id}`. Please check the ID.")
            logger.error(f"Register failed: Could not fetch API data for {game_id}")
            return

        player = data["data"]

        # Save full player info
        self.users[discord_id] = {
            "game_id": str(player.get("fid")),
            "nickname": player.get("nickname"),
            "state_id": player.get("kid"),
            "furnace_level": player.get("stove_lv"),
            "furnace_image": player.get("stove_lv_content"),
            "avatar": player.get("avatar_image"),
        }

        self.save_users()
        await ctx.send(f"✅ Registered **{player.get('nickname')}** (Game ID: {player.get('fid')})")
        logger.info(f"Registered {ctx.author} as {player.get('nickname')} ({game_id})")

    @commands.command(name="userinfo")
    async def userinfo(self, ctx, target: str = None):
        """Check a user's registered game info or fetch by Game ID"""
        game_id = None
        member = None

        # Case 1: no argument -> use self
        if target is None:
            discord_id = str(ctx.author.id)
            if discord_id not in self.users:
                await ctx.send("❌ You are not registered. Use `!register <game_id>` first.")
                logger.warning(f"{ctx.author} tried !userinfo but is not registered.")
                return
            game_id = self.users[discord_id]["game_id"]
            member = ctx.author

        # Case 2: mentioned user
        elif target.isdigit() is False and ctx.message.mentions:
            member = ctx.message.mentions[0]
            discord_id = str(member.id)
            if discord_id not in self.users:
                await ctx.send(f"❌ {member.mention} is not registered yet.")
                logger.warning(f"Lookup failed: {member} not registered.")
                return
            game_id = self.users[discord_id]["game_id"]

        # Case 3: raw game ID
        elif target.isdigit():
            game_id = target
            logger.info(f"{ctx.author} requested info for raw Game ID {game_id}")

        # Fetch from API
        data = await api.get_player_info(game_id)
        if not data or "data" not in data:
            await ctx.send(f"⚠️ Failed to fetch info for Game ID `{game_id}`.")
            logger.error(f"API returned no data for Game ID {game_id}")
            return

        player = data["data"]

        # Embed formatting
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
            embed.set_footer(
                text=f"Requested by {ctx.author}",
                icon_url=ctx.author.avatar.url if ctx.author.avatar else None
            )

        await ctx.send(embed=embed)
        logger.info(f"Sent player info for Game ID {game_id}: {player}")


async def setup(bot):
    await bot.add_cog(Users(bot))
