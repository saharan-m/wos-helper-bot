import discord
from discord.ext import commands

class Help(commands.Cog):
    """Beautiful help command showing commands grouped by cog."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="help")
    async def help_command(self, ctx, *, query: str = None):
        """
        Usage:
          !help            -> show all commands grouped by category
          !help <command>  -> show usage for a specific command
        """
        # If user asked for a specific command, show detailed help
        if query:
            cmd = self.bot.get_command(query)
            if not cmd:
                return await ctx.send(f"❌ Command `{query}` not found.")
            embed = discord.Embed(
                title=f"Help — `{cmd.qualified_name}`",
                color=discord.Color.blurple()
            )
            embed.add_field(name="Usage", value=f"`!{cmd.qualified_name} {cmd.signature}`" if cmd.signature else f"`!{cmd.qualified_name}`", inline=False)
            embed.add_field(name="Description", value=cmd.help or "No description provided.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            await ctx.send(embed=embed)
            return

        # Full help embed
        embeds = []
        base_embed = discord.Embed(
            title="✨ WOS Giftcode Bot — Help",
            description="• Use `!help <command>` for detailed usage\n• All times are UTC where applicable\n\n",
            color=discord.Color.teal()
        )
        base_embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2920/2920251.png")
        base_embed.set_footer(text="Tip: try `!help remindonce` or `!help remind` for examples")

        # build fields grouped by cog
        for cog_name, cog in self.bot.cogs.items():
            # collect visible (non-hidden) commands
            lines = []
            for cmd in cog.get_commands():
                if cmd.hidden:
                    continue
                # brief one-line help (first line of doc)
                short = (cmd.help or "").splitlines()[0] if cmd.help else "No description"
                signature = f" {cmd.signature}" if cmd.signature else ""
                lines.append(f"**`!{cmd.name}{signature}`** — _{short}_")

            if lines:
                # if too large for one embed field, chunk it
                chunk_text = "\n".join(lines)
                base_embed.add_field(name=f"⚙️ {cog_name}", value=chunk_text, inline=False)

        # add commands not in a cog (standalone)
        uncategorized = []
        for cmd in self.bot.commands:
            if cmd.cog_name is None and not cmd.hidden:
                signature = f" {cmd.signature}" if cmd.signature else ""
                uncategorized.append(f"**`!{cmd.name}{signature}`** — _{(cmd.help or 'No description').splitlines()[0]}_")
        if uncategorized:
            base_embed.add_field(name="🛠 General", value="\n".join(uncategorized), inline=False)

        # Ensure embed size is safe — if huge, split into smaller embeds
        raw_len = sum(len(f.value) for f in base_embed.fields) if base_embed.fields else len(base_embed.description or "")
        if raw_len < 3500:
            await ctx.send(embed=base_embed)
            return

        # Fallback: split into multiple embeds if content is large
        # (we split by cog fields: one embed per 3 fields)
        fields = base_embed.fields
        for i in range(0, len(fields), 3):
            e = discord.Embed(title=base_embed.title, color=base_embed.color)
            e.set_thumbnail(url=base_embed.thumbnail.url if base_embed.thumbnail else None)
            for f in fields[i:i+3]:
                e.add_field(name=f.name, value=f.value, inline=False)
            e.set_footer(text=base_embed.footer.text or "")
            await ctx.send(embed=e)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
