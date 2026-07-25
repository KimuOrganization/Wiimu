from __future__ import annotations

from typing import Optional, Sequence
import discord

from core.bot import Bot


class DiscordLoggingService:
    def __init__(self, bot: Bot):
        self.bot = bot

    #region Helpers
    @property
    def guild(self) -> discord.Guild | None:
        return self.bot.get_guild(self.bot.config.guild_id) # type: ignore

    @property
    def logs_channel(self) -> discord.TextChannel | None:
        guild = self.guild
        if guild is None:
            return None

        return guild.get_channel(
            self.bot.config.channels.staff.LOGS # type: ignore
        )

    @property
    def command_logs_channel(self) -> discord.TextChannel | None:
        guild = self.guild
        if guild is None:
            return None

        return guild.get_channel(
            self.bot.config.channels.staff.COMMAND_LOGS # type: ignore
        )

    #region Log
    async def send_log(
        self,
        *,
        content: Optional[str] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        files: Optional[Sequence[discord.File]] = None,
    ) -> discord.Message | None:
        channel = self.logs_channel

        if channel is None:
            return None

        return await channel.send(
            content=content,
            embeds=embeds or [],
            files=files or [],
        )

    #region Command log
    async def send_command_log(
        self,
        *,
        content: str | None = None,
        embeds: Sequence[discord.Embed] | None = None,
        files: Sequence[discord.File] | None = None,
    ) -> discord.Message | None:
        channel = self.command_logs_channel

        if channel is None:
            return None

        return await channel.send(
            content=content,
            embeds=embeds or [],
            files=files or [],
        )

    # Region DM
    async def send_dm(
        self,
        user: discord.User | discord.Member,
        *,
        content: Optional[str] = None,
        embeds: Optional[Sequence[discord.Embed]] = None,
        files: Optional[Sequence[discord.File]] = None,
    ) -> bool:
        try:
            await user.send(
                content=content,
                embeds=embeds or [],
                files=files or [],
            )
            return True

        except discord.Forbidden:
            return False

        except discord.HTTPException:
            return False