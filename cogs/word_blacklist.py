import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from core.config import SPECIAL_CHANNELS, GUILD_ID
from utils.colors import ModerationColors
from utils.user import resolve_user
from utils.time import parse_duration
from utils.moderation import send_moderation_log, send_moderation_dm
from typing import Union

class WordBlacklist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #region list_blacklisted_words
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="palabras_prohibidas", description="Lista las palabras prohibidas del servidor")
    async def list_blacklisted_words(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("Ha ocurrido un error.")

        words=(
        "n word\n"
        "femboy\n"
        "israel\n"
        "palestina\n"
        "judío\n"
        )

        return await interaction.followup.send(f"**Palabras prohibidas:**\n{words}")

async def setup(bot: commands.Bot):
    await bot.add_cog(WordBlacklist(bot))
