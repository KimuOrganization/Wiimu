import discord
from discord.ext import commands
from datetime import timedelta
from core.bot import Bot
from core.config_sections.channels import Channels
from core.config_sections.colors import Colors
from core.config_sections.roles import Roles
from utils.message import INVITE_REGEX, BANNED_PHRASES
from datetime import datetime
from utils.time import format_duration
from typing import Union
import logging
logger = logging.getLogger(__name__)
# Cambiar para la duración de los mutes automaticos
MUTE_DURATION = timedelta(hours=24)

PARSED_DURATION = format_duration(MUTE_DURATION)

class MessageFilter(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @property
    def colors(self) -> Colors:
        return self.bot.config.colors # type:ignore

    @property
    def channels(self) -> Channels:
        return self.bot.config.channels # type: ignore
    
    @property
    def roles(self) -> Roles:
        return self.bot.config.roles # type: ignore

    async def log_filter(self,guild: discord.Guild, member:Union[discord.User,discord.Member], message: discord.Message, reason:str, sanctionWithBan:bool = True):
        log_channel = guild.get_channel(self.channels.staff.COMMAND_LOGS)
        
        duration_message = f"Duración del aislamiento: {PARSED_DURATION}\n"

        staff_role : Union[discord.Role, None] = guild.get_role(self.roles.staff.MODERATORS)
        staff_members : Union[list[str],None] = None
        staff_mention : Union[str,None] = None
        if staff_role:
            staff_members = [
                f"{member.name}: https://discord.com/users/{member.id}"
                for member in staff_role.members
            ]
            staff_mention = (
                "\n\nSi crees que esto fue un error, comunícate con alguien del staff.\n"
                + "\n".join(staff_members)
            )

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
                color=self.colors.moderation.BAN if sanctionWithBan else self.colors.moderation.MUTE
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

            description_text += f"{staff_mention if staff_role and staff_members and staff_mention else ''}"

            dm_embed = discord.Embed(
                title=f"Has sido {'banead@' if sanctionWithBan else 'aislad@'} en {guild.name}",
                description=description_text,
                timestamp=datetime.now()
            )
            dm_embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
            dm_embed.set_footer(text="Mensaje automatico")

            return await member.send(embed=dm_embed)

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
            # En caso de que no se borre la invitación, avisar al STAFF
            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            if not staff_role:
                return
            await message.reply(
                staff_role.mention, silent=False
            )
            return
        
        reason="Se detecto una invitación a un servidor de discord. (spam)"

        dm_sended = True
        dm_reference = None
        # TODO: Implementar logging
        try:
            dm_reference = await self.log_filter(guild,member,message,reason)
        except:
            dm_sended = False
            logger.exception("No se pudo enviar el mensaje a %s [%s]. (Baneo por invitación a un servidor de discord)",member.name,member.id)
            cmd_channel = guild.get_channel(self.channels.staff.COMMAND_LOGS)
            if isinstance(cmd_channel,discord.TextChannel):
                await cmd_channel.send(f"No se pudo notificar por privado a `{member.name} [{member.id}]` ({member.mention}), sobre su baneo por mandar una invitación a otro servidor de discord.")
            pass
        
        try:
            await guild.ban(
                member,
                reason=reason,
                delete_message_days=1
            )
        except discord.Forbidden:
            # Borrar el mensaje privado porque no se pudo realizar la sanción
            if dm_sended and dm_reference is not None:
                await dm_reference.delete()
            return
        
       

    async def handle_banned_phrases(self, message:discord.Message):
        if not isinstance(message.author, discord.Member):
            return

        if not isinstance(message.guild, discord.Guild):
            return

        guild = message.guild
        member = message.author
        
        normalized_message = message.content.lower()
        
        # Busqueda de coincidencias
        if not any(phrase.lower() in normalized_message for phrase in BANNED_PHRASES):
            return
        
        try:
            await message.delete()
        except discord.Forbidden:
            logger.exception("No se pudo borrar el mensaje [%s] de %s [%s], que contiene una frase baneada. **Es probable que no tenga los permisos necesarios.**",message.id,member.name,member.id)
            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            if staff_role:
                await message.reply(staff_role.mention)
        except discord.HTTPException:
            logger.exception("No se pudo borrar el mensaje [%s] de %s [%s], que contiene una frase baneada. **Ha ocurrido un error por parte de Discord.**",message.id,member.name,member.id)
            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            if staff_role:
                await message.reply(staff_role.mention)

        reason="Se detecto una frase baneada."

        try:
            await member.timeout(
                MUTE_DURATION,
                reason=reason
            )
        except discord.Forbidden:
            logger.exception("No se ha podido aislar a %s [%s], debido al uso de una frase baneada, en el mensaje [%s]. **Es probable que no tenga los permisos necesarios para aislar al usuario.**",member.name,member.id,message.id)
            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            cmd_channel = guild.get_channel(self.channels.staff.COMMAND_LOGS)
            if isinstance(cmd_channel,discord.TextChannel):
                timeout_in_hours = int(MUTE_DURATION.total_seconds() / 3600)
                await cmd_channel.send(f"{staff_role.mention if staff_role else ''}\n\nNo se ha podido aplicar el aislamiento de {timeout_in_hours} horas, a `{member.name} [{member.id}]` ({member.mention}), por utilizar una frase baneada.\nMensaje:\n```\n{message.content}\n```\n\n**Es necesario aplicar sanción de forma manual.**",)
            return
        except discord.HTTPException:
            logger.exception("No se ha podido aislar a %s [%s], debido al uso de una frase baneada, en el mensaje [%s]. **Ha ocurrido un error por parte de Discord.**",member.name,member.id,message.id)
            staff_role = guild.get_role(self.roles.staff.MODERATORS)
            cmd_channel = guild.get_channel(self.channels.staff.COMMAND_LOGS)
            if isinstance(cmd_channel,discord.TextChannel):
                timeout_in_hours = int(MUTE_DURATION.total_seconds() / 3600)
                await cmd_channel.send(f"{staff_role.mention if staff_role else ''}\n\nNo se ha podido aplicar el aislamiento de {timeout_in_hours} horas, a `{member.name} [{member.id}]` ({member.mention}), por utilizar una frase baneada.\nMensaje:\n```\n{message.content}\n```\n\n**Es necesario aplicar sanción de forma manual.**",)
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
