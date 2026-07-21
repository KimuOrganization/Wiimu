from __future__ import annotations
import math
from dataclasses import dataclass, field
import discord
from discord import app_commands
from discord.ext import commands
import time
from datetime import datetime, timedelta
from core.bot import Bot
from core.config import GUILD_ID
from core.config_sections.channels import Channels
from core.config_sections.colors import Colors
from utils.community import contains_banned_word
from typing import Union

VOTE_TIMEOUT = 300
VOTE_COOLDOWN = timedelta(minutes=10)
STATE_MAX_LENGTH = 500


@dataclass
class VoteSession:
    voice_channel: discord.VoiceChannel
    state: str
    message: Union[discord.Message, None] = None
    
    approvals: set[int] = field(default_factory=set)
    rejections: set[int] = field(default_factory=set)

    view: "VoteView | None" = None

class VoteView(discord.ui.View):
    def __init__(self, cog: "Community", session: VoteSession):
        super().__init__(timeout=VOTE_TIMEOUT)

        self.cog = cog
        self.session = session
    
    async def register_vote(
        self,
        interaction: discord.Interaction,
        approve: bool
    ):
        member = interaction.user

        if not isinstance(member, discord.Member):
            return

        if(member.voice is None or member.voice.channel != self.session.voice_channel):
            return await interaction.response.send_message(
                "Debes estar dentro del canal de voz.",
                ephemeral=True
            )

        self.session.approvals.discard(member.id)
        self.session.rejections.discard(member.id)

        if approve:
            self.session.approvals.add(member.id)
        else:
            self.session.rejections.add(member.id)
        
        await self.cog.update_vote_message(self.session)

        await interaction.response.send_message(
            "Tu voto fue registrado.",
            ephemeral=True
        )

        result = self.cog.vote_result(self.session)

        if result is True:
            await self.cog.finish_vote(self.session, True)
        elif result is False:
            await self.cog.finish_vote(self.session, False)

    @discord.ui.button(
        label="Aprobar",
        emoji="👍",
        style=discord.ButtonStyle.green,
    )
    async def approve_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.register_vote(interaction, True)

    @discord.ui.button(
        label="Rechazar",
        emoji="👎",
        style=discord.ButtonStyle.red
    )
    async def reject_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await self.register_vote(interaction, False)
    
    async def on_timeout(self):
        if self.session.voice_channel.id in self.cog.sessions:
            await self.cog.finish_vote(self.session, False)


class Community(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.sessions: dict[int, VoteSession] = {}
        self.last_vote: dict[int, datetime] = {}

        # Cooldown individual por usuario para cambiarse el nombre
        self.nickname_change_cooldown : float = timedelta(minutes=3).total_seconds()
        self.nickname_change_last_user : Union[int, None] = None
        self.nickname_change_last_use : float = 0.00

    @property
    def colors(self) -> Colors:
        return self.bot.config.colors # type: ignore

    @property
    def channels(self) -> Channels:
        return self.bot.config.channels # type: ignore

    def required_votes(self, channel: discord.VoiceChannel) -> int:
        members = len([
            m for m in channel.members
            if not m.bot
        ])

        return max(1, math.floor(members / 2))

    def vote_result(self, session: VoteSession):
        members = [
            m for m in session.voice_channel.members
            if not m.bot
        ]

        total = len(members)

        approvals = len(session.approvals)
        rejections = len(session.rejections)

        required = self.required_votes(session.voice_channel)

        if approvals >= required:
            return True

        remaining = total - approvals - rejections

        if approvals + remaining < required:
            return False

        return None

    async def update_vote_message(self, session: VoteSession):
        channel = session.voice_channel
        required = self.required_votes(channel)

        embed = discord.Embed(
            title=":ballot_box: Cambiar estado del canal",
            colour=discord.Colour.blurple()
        )
        embed.add_field(
            name="Nuevo estado",
            value=session.state,
            inline=False
        )
        embed.add_field(
            name=":thumbsup: A favor",
            value=str(len(session.approvals)),
            inline=True
        )
        embed.add_field(
            name=":thumbsdown: En contra",
            value=str(len(session.rejections)),
            inline=True
        )
        embed.add_field(
            name="Necesarios",
            value=str(required),
            inline=True
        )

        embed.add_field(
            name="Usuarios en VC",
            value=str(len([
                m for m in channel.members
                if not m.bot
            ])),
            inline=True
        )

        # Evitar warnings de pylance      
        if session.message is None:
            return

        await session.message.edit(
            embed=embed,
            view=session.view
        )
    
    async def finish_vote(
        self,
        session: VoteSession,
        success: bool
    ):
        self.last_vote[session.voice_channel.id] = datetime.now()
        self.sessions.pop(session.voice_channel.id, None)

        if success:
            await session.voice_channel.edit(
                status=session.state
            )
        
            embed = discord.Embed(
                title=":white_check_mark: Estado actualizado",
                description=session.state,
                colour=discord.Colour.green()
            )
        
        else:
            embed = discord.Embed(
                title=":x:  Propuesta rechazada",
                description="No se alcanzaron los votos necesarios :(",
                colour=discord.Colour.red()
            )

        # Evitar warnings de pylance
        if session.message is None:
            return
        
        await session.message.edit(
            embed=embed,
            view=None
        )
    
    @commands.Cog.listener("on_voice_state_update")
    async def on_voice_state_update_community(
        self,
        member,
        before,
        after
    ):
        channels = {
            before.channel,
            after.channel
        }

        for channel in channels:
            if not isinstance(channel, discord.VoiceChannel):
                continue

            session = self.sessions.get(channel.id)

            if session is None:
                continue

            valid_members = {
                m.id
                for m in channel.members
                if not m.bot
            }

            session.approvals.intersection_update(valid_members)
            session.rejections.intersection_update(valid_members)

            if len(valid_members) == 0:
                await self.finish_vote(session, False)
                continue

            result = self.vote_result(session)

            if result is True:
                await self.finish_vote(session, True)
                continue

            elif result is False:
                await self.finish_vote(session, False)
                continue

            await self.update_vote_message(session)

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="cambiar_estado_vc",
        description="Inicia una votación para cambiar el estado del VC."
    )
    @app_commands.describe(
        estado="Nuevo estado del canal."
    )
    async def cambiar_estado_vc(
        self,
        interaction: discord.Interaction,
        estado: str
    ):
        if not interaction.guild:
            return

        if len(estado) > STATE_MAX_LENGTH:
            return await interaction.response.send_message(
                f"Máximo {STATE_MAX_LENGTH} caracteres.",
                ephemeral=True
            )

        member = interaction.user

        if not isinstance(member, discord.Member):
            return

        if member.voice is None:
            return await interaction.response.send_message(
                "Debes estar en un canal de voz.",
                ephemeral=True
            )

        channel = member.voice.channel

        if not isinstance(channel, discord.VoiceChannel):
            return await interaction.response.send_message(
                "Este comando solo puede utilizarse en un canal de voz.",
                ephemeral=True
            )

        if channel.id in self.sessions:
            return await interaction.response.send_message(
                "Ya existe una votación en curso para este canal.",
                ephemeral=True
            )
        
        now = datetime.now()
        last_vote = self.last_vote.get(channel.id)

        if last_vote is not None:
            elapsed = now - last_vote
            if elapsed < VOTE_COOLDOWN:
                remaining = VOTE_COOLDOWN - elapsed
                minutes = int(remaining.total_seconds() // 60)
                seconds = int(remaining.total_seconds() % 60)

                return await interaction.response.send_message(
                    f":hourglass_flowing_sand: Deben esperar **{minutes}m {seconds}s** antes de iniciar otra votación.",
                    ephemeral=True
                )

        log_embed = discord.Embed(
            title="Intento establecer un estado en VC",
            description=f"{member.mention} intento cambiar el estado de {channel.mention}",
            color=self.colors.logs.PROFILE_NAME,
            timestamp=datetime.now()
        )
        log_embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        log_embed.set_footer(text="ID: "+str(member.id))
        log_embed.add_field(name="Estado", value=f"```{estado}```",inline=False)

        log_channel = interaction.guild.get_channel(self.channels.staff.LOGS)

        # Evitar warnings pylance
        if not isinstance(log_channel, discord.TextChannel):
            return

        await log_channel.send(embed=log_embed)

        if contains_banned_word(estado):
            return await interaction.response.send_message(
                ":x: Ese estado contiene una o mas palabras prohibidas.",
                ephemeral=True
            )

        human_members = [
            m for m in channel.members if not m.bot
        ]

        if len(human_members) == 1:
            self.last_vote[channel.id] = datetime.now()
            await channel.edit(status=estado)

            return await interaction.response.send_message(
                ":white_check_mark: Estado del canal actualizado",
                ephemeral=True
            )

        embed = discord.Embed(
            title=":ballot_box: Cambiar estado del canal",
            colour=discord.Colour.blurple()
        )

        embed.add_field(
            name="Nuevo estado",
            value=estado,
            inline=False
        )
        
        embed.add_field(
            name=":thumbsup: A favor",
            value="0",
            inline=True
        )
        embed.add_field(
            name=":thumbsdown: En contra",
            value="0",
            inline=True
        )
        embed.add_field(
            name="Necesarios",
            value=str(self.required_votes(channel)),
            inline=True
        )

        embed.add_field(
            name="Usuarios en VC",
            value=str(len([
                m for m in channel.members
                if not m.bot
            ])),
            inline=True
        )

        session = VoteSession(
            voice_channel=channel,
            state=estado,
        )

        view = VoteView(self, session)

        session.view = view
        
        message = await channel.send(
            embed=embed,
            view=view
        )
        session.message = message

        self.sessions[channel.id] = session

        await interaction.response.send_message(
            ":white_check_mark: Se inició una votación en el chat del canal de voz.",
            ephemeral=True
        )

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="cambiar_mi_nick",
        description="Cambia tu nickname de discord en el servidor."
    )
    @app_commands.describe(
        nickname="Tu nuevo nickname."
    )
    async def change_nickname(self, interaction: discord.Interaction, nickname:str):
        user:  Union[discord.Member, discord.User] = interaction.user
        # Evitar errores de pylance
        if not isinstance(user, discord.Member):
            return

        if len(nickname) > 32:
            return await interaction.response.send_message(
                "El nickname no puede superar los 32 caracteres.",
                ephemeral=True
            )

        # Verificar palabras prohibidas
        if contains_banned_word(nickname):
            return await interaction.response.send_message(
                "Ese nickname contiene palabras no permitidas.",
                ephemeral=True
            )
        
        now = time.time()

        if (self.nickname_change_last_user == interaction.user.id 
            and now - self.nickname_change_last_use < self.nickname_change_cooldown):
            
            remaining = int(self.nickname_change_cooldown - (now - self.nickname_change_last_use))
            
            return await interaction.response.send_message(
                f"Debes esperar **{remaining} segundos** antes de volver a cambiar tu nickname.",
                ephemeral=True
            )

        self.nickname_change_last_user = interaction.user.id
        self.nickname_change_last_use = now

        try:
            await user.edit(nick=nickname)
            await interaction.response.send_message(
                f"Tu nickname fue cambiado a **{nickname}**.",
                ephemeral=True
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                "No tengo permisos para cambiar tu nickname.",
                ephemeral=True
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "Ocurrió un error al cambiar tu nickname.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Community(bot))
