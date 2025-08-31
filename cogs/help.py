import discord
from discord import app_commands
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all commands or help for a specific command")
    @app_commands.describe(command="Optional: command to get detailed help")
    async def help_command(self, interaction: discord.Interaction, command: str = None):
        if command:
            cmd = self.bot.get_command(command)
            if not cmd:
                await interaction.response.send_message(f"❌ Command `{command}` not found.", ephemeral=True)
                return
            embed = discord.Embed(
                title=f"Help — `{cmd.qualified_name}`", color=discord.Color.blurple()
            )
            embed.add_field(name="Usage", value=f"`/{cmd.qualified_name} {cmd.signature}`" if cmd.signature else f"`/{cmd.qualified_name}`")
            embed.add_field(name="Description", value=cmd.help or "No description provided.", inline=False)
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join(cmd.aliases), inline=False)
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        embed = discord.Embed(title="✨ WOS Giftcode Bot — Help", color=discord.Color.teal())
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2920/2920251.png")
        embed.set_footer(text="Tip: try `/remindonce` or `/remind` for examples")

        for cog_name, cog in self.bot.cogs.items():
            lines = []
            for cmd in cog.get_commands():
                if cmd.hidden:
                    continue
                signature = f" {cmd.signature}" if cmd.signature else ""
                lines.append(f"**`/{cmd.name}{signature}`** — _{(cmd.help or 'No description').splitlines()[0]}_")
            if lines:
                embed.add_field(name=f"⚙️ {cog_name}", value="\n".join(lines), inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
