import discord
from discord.ext import commands
from datetime import timedelta
from core.bot import Bot
from core.config_sections.channels import Channels
from core.config_sections.roles import Roles
from utils.message import INVITE_REGEX, BANNED_PHRASES
from utils.colors import ModerationColors
from datetime import datetime
from utils.time import format_duration
from typing import Union

# Cambiar para la duración de los mutes automaticos
MUTE_DURATION = timedelta(hours=24)

PARSED_DURATION = format_duration(MUTE_DURATION)

class MessageFilter(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @property
    def channels(self) -> Channels:
        return self.bot.config.channels # type: ignore
    
    @property
    def roles(self) -> Roles:
        return self.bot.config.roles # type: ignore

    async def log_filter(self,guild: discord.Guild, member:Union[discord.User,discord.Member], message: discord.Message, reason:str, sanctionWithBan:bool = True):
        log_channel = guild.get_channel(self.channels.staff.COMMAND_LOGS)
        
        duration_message = f"Duración del aislamiento: {PARSED_DURATION}\n"

        if (log_channel and isinstance(log_channel, discord.TextChannel)):
            embed = discord.Embed(
                title=f"Filtro automatico ({'BAN' if sanctionWithBan else 'MUTE'})",
                description=(
                    f"Usuario: {member.mention}\n"
                    f"Canal: {message.channel.mention if not isinstance(message.channel, (discord.DMChannel, discord.GroupChannel)) else 'Desconocido'}\n"
                    f"{duration_message if not sanctionWithBan else ''}"
                    f"Razón: {reason}\n\n"
                    f"Contenido del mensaje:\n`{message.content}`"
                ),
                timestamp=datetime.now(),
                color=ModerationColors.FILTER_MUTE
            )
            embed.set_author(name=guild.name,icon_url=guild.icon.url if guild.icon else None)
            embed.set_footer(text=f"ID: {member.id}")

            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            newline = "\n"
            additional_line : Union[str,None] = f"{(newline+staff_role.mention*3) if staff_role else None}"
            await log_channel.send(additional_line,embed=embed,silent=True)
            
            description_text = f"Razón: {reason}\n"
            if not sanctionWithBan:
                description_text += f"{duration_message}"
                description_text += f"Espere mientras el staff revisa su caso."

            dm_embed = discord.Embed(
                title=f"Has sido {'banead@' if sanctionWithBan else 'aislad@'} en {guild.name}",
                description=description_text,
                timestamp=datetime.now()
            )
            dm_embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
            dm_embed.set_footer(text="Mensaje automatico")

            await member.send(embed=dm_embed)

    async def handle_discord_invites(self, message: discord.Message):
        match = INVITE_REGEX.search(message.content)
        if not match:
            return
        
        if not isinstance(message.author, discord.Member):
            return
        
        if not isinstance(message.guild, discord.Guild):
            return
        
        guild = message.guild
        member = message.author
        invite_code = match.group(1)

        try:
            invite = await self.bot.fetch_invite(invite_code)

        # Invitación invalida o expirada = spam
        except discord.NotFound:
            invite = None

        # No se puede ver la invitación por falta de permisos = spam
        except discord.Forbidden:
            invite = None

        # Ocurre un error del lado de discord = spam
        except discord.HTTPException:
            return

        # Si la invitación es del mismo servidor desde el que se envia entonces permitir
        if (invite and invite.guild and invite.guild.id == guild.id):
            return

        try:
            await message.delete()
        except discord.Forbidden:
            return
        
        reason="Se detecto una invitación a un servidor de discord. (spam)"

        try:
            await guild.ban(
                member,
                reason=reason,
                delete_message_days=1
            )
        except discord.Forbidden:
            return
        
        await self.log_filter(guild,member,message,reason)

    async def handle_banned_phrases(self, message:discord.Message):
        if not isinstance(message.author, discord.Member):
            return

        if not isinstance(message.guild, discord.Guild):
            return

        guild = message.guild
        member = message.author
        
        normalized_message = message.content.lower()
        finded : bool = False
        
        # Busqueda de coincidencias
        for phrase in BANNED_PHRASES:
            if phrase.lower() in normalized_message:
                finded = True

        if not finded:
            return
        
        try:
            await message.delete()
        except discord.Forbidden:
            return

        reason="Se detecto una frase baneada."

        try:
            await member.timeout(
                MUTE_DURATION,
                reason=reason
            )
        except discord.Forbidden:
            return
        
        await self.log_filter(guild,member,message,reason,False)

    #region on_message
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Ignorar DMs
        if not message.guild:
            return
        
        # Para evitar errores de pylance
        if not isinstance(message.author, discord.Member):
            return

        # Ignorar bots
        if message.author.bot:
            return
        
        # Ignorar al staff
        if message.author.guild_permissions.administrator:
            return
        
        # Filtros
        await self.handle_discord_invites(message)
        await self.handle_banned_phrases(message)

async def setup(bot: Bot):
    await bot.add_cog(MessageFilter(bot))
