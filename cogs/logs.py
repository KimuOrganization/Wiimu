import discord
from discord.ext import commands
from datetime import datetime, timezone, timedelta
from core.config import APP_ID, SPECIAL_CHANNELS, STAFF_ROLE_ID, LOG_BLACKLISTED_BOTS
from utils.time import format_duration
from utils.permissions import diff_permission, diff_overwrites
from utils.moderation import get_actor_for_action, get_actor_for_moderation_action, send_common_log, send_moderation_log
from utils.colors import LogColors, ModerationColors
from typing import Union, Sequence
discord.abc.GuildChannel
from io import BytesIO

GuildChannel = Union[discord.TextChannel,discord.VoiceChannel,discord.StageChannel,discord.ForumChannel,discord.CategoryChannel]

class Logs(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    #region on_member_join
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        age_days = (datetime.now(timezone.utc) - member.created_at).days
        alert = "\n⚠️ CUENTA NUEVA ⚠️" if age_days < 7 else ""

        embed = discord.Embed(
            title ="Nuevo miembro",
            description=f"{member.mention}\nCuenta Creada el <t:{int(member.created_at.timestamp())}:D>.{alert}",
            color=LogColors.JOIN,
            timestamp=datetime.now()
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_footer(text="ID: " +str(member.id))

        await send_common_log(guild=member.guild, embed=embed)

    #region on_member_remove
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        actor, reason = await get_actor_for_moderation_action(member.guild, member.id, discord.AuditLogAction.kick)

        # Verificar expulsiones manuales que no hayan sido realizadas por el bot
        if (actor and actor.id != int(APP_ID)):
            staff_role = member.guild.get_role(int(STAFF_ROLE_ID))
            newline = "\n"
            staff_mention : Union[str,None] = f"{(newline+staff_role.mention*3) if staff_role else None}"
            embed = discord.Embed(
                title="Expulsión manual",
                description=(
                    f"Se ha realizado un expulsión manual."
                    f"\nModerador/a: {actor.mention if actor else 'Desconocido/a'}" 
                    f"\n\nExpulsado:\n\u2800\u2800`{member.name} [{member.id}]`"
                    f"\n\nRazón: {reason if reason else 'No especificada'}"),
            timestamp=datetime.now(),
            color=ModerationColors.UNBAN
            )
            embed.set_author(name=member.guild.name, icon_url=f"{member.guild.icon.url}" if member.guild.icon else None)
            embed.set_footer(text=f"ID: {member.id}")

            await send_moderation_log(guild=member.guild,message=staff_mention,embed=embed)

        embed = discord.Embed(
            title="Salida del servidor",
            description=f"{member.mention}",
            color=LogColors.LEAVE,
            timestamp=datetime.now()
        )
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_footer(text="ID: " +str(member.id))

        joined_at = member.joined_at
        if (joined_at):
            delta = discord.utils.utcnow() - joined_at
            duration = format_duration(delta)

            embed.add_field(
                name="Tiempo en el servidor",
                value=duration,
                inline=False
            )
        
        await send_common_log(guild=member.guild, embed=embed)

    #region on_message_delete
    @commands.Cog.listener()
    async def on_message_delete(self, message : discord.Message):
        # No es un mensaje de servidor
        if (not isinstance(message.guild, discord.Guild)):
            return
        
        if (isinstance(message.channel, (discord.DMChannel, discord.GroupChannel))):
            return
        
        if (message.author.id in LOG_BLACKLISTED_BOTS):
            return

        message_content = message.content
        if (not message.content):
            message_content = "*Sin texto*"

        message_attachments = ""
        if (len(message.attachments) > 0):
            for attachment in message.attachments:
                message_attachments += "\n\u2800\u2800"
                message_attachments += f"{attachment.url}"
        
        embed = discord.Embed(
            title="Mensaje eliminado",
            description=f"**Canal:** {message.channel.mention}\n```{message_content}```\n**Attachments:**{message_attachments}",
            color=LogColors.MESSAGE_DELETE,
            timestamp=datetime.now()
        )
        embed.set_author(name=message.author.name, icon_url=message.author.display_avatar.url)
        embed.set_footer(text="ID: " +str(message.author.id))

        # Previene que se eliminen logs
        if message.author.id == int(APP_ID) and message.channel.id in SPECIAL_CHANNELS:
            staff_role = message.guild.get_role(int(STAFF_ROLE_ID))
            newline = "\n"
            additional_line : Union[str,None] = f"{(newline+staff_role.mention*3) if staff_role else None}"
            return await message.channel.send(f"### :exclamation: Se intento borrar este log, re-subida automatica :exclamation:{additional_line}",embeds=message.embeds)

        await send_common_log(guild=message.guild, embed=embed)

    #region on_message_edit
    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild:
            return
        
        if isinstance(before.channel, (discord.DMChannel, discord.GroupChannel)):
            return

        if before.content == after.content:
            return
        
        if before.author.bot:
            return

        embed = discord.Embed(
            title="Mensaje editado",
            color=LogColors.MESSAGE_EDIT,
            timestamp=datetime.now(),
            description=f"**Canal:** {before.channel.mention}\n"
        )

        # Declaraciones
        text : Union[str, None] = None
        file : Union[discord.File, None] = None
        files : Sequence[discord.File] = []
        
        # Evitar excepciones de discord por superar el limite de caracteres
        if (len(before.content) > 1024 or len(after.content) > 1024):
            text = (
                "# Antes:\n\n"
                f"{before.content}\n\n"
                "----------------------------------------------------------------\n\n"
                "# Despues:\n\n"
                f"{after.content}"
            )
            file = discord.File(
                BytesIO(text.encode("utf-8")),
                filename=f"mensaje_editado_{before.id}.txt"
            )
            embed.add_field(
                name="Contenido",
                value="El mensaje es demasiado largo. Se adjunta un archivo con el contenido completo.",
                inline=False
            )
        else:
            embed.add_field(name="Antes", value=before.content, inline=False)
            embed.add_field(name="Despues", value=after.content, inline=False)
        embed.set_author(name=before.author.name, icon_url=before.author.display_avatar.url)
        embed.set_footer(text="ID: " +str(before.author.id))

        # Agrego el archivo si es que se creo uno
        if not file is None:
            files = [file]

        await send_common_log(guild=before.guild, embed=embed, files=files)

    #region on_voice_state_update
    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState):
        if before.channel == after.channel:
            return
        
        embed = discord.Embed()

        if before.channel is None and after.channel is not None:
            title = "Se unio a canal de voz"
            description = f"{member.mention} se unio a #{after.channel.mention}"
            embed.colour = LogColors.VOICE_JOIN

        elif before.channel is not None and after.channel is None:
            title = "Salio de canal de voz"
            description = f"{member.mention} salio de #{before.channel.mention}"
            embed.colour = LogColors.VOICE_LEAVE
        else:
            title = "Cambio de canal de voz"
            description = (
                f"{member.mention} cambio de VC\n"
                f"\n**Antes:** {before.channel.mention if (before.channel) else 'Desconocido'}"
                f"\n**Despues:** {after.channel.mention if (after.channel) else 'Desconocido'}"
                ) 
            embed.colour = LogColors.VOICE_CHANGE

        embed.title = title
        embed.description = description
        embed.timestamp = datetime.now()
        embed.set_author(name=member.name, icon_url=member.display_avatar.url)
        embed.set_footer(text="ID: "+str(member.id))

        await send_common_log(guild=member.guild, embed=embed)

    #region on_guild_channel_create
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel:discord.abc.GuildChannel):
        embed = discord.Embed(
            title="Canal creado",
            description=f"Se creo el canal {channel.mention}",
            color=LogColors.CHANNEL_CREATE,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"{channel.name}", icon_url=channel.guild.icon.url if channel.guild.icon else None)

        actor = await get_actor_for_action(channel.guild, channel.id,discord.AuditLogAction.channel_create)
        if actor:
            embed.set_footer(text=f"Creado por: {actor.name} ({actor.id})")
        else:
            embed.set_footer(text=f"Creado por: desconocido")
        
        await send_common_log(guild=channel.guild, embed=embed)

    #region on_guild_channel_delete
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel:discord.abc.GuildChannel):
        embed = discord.Embed(
            title="Canal eliminado",
            description=f"Se elimino el canal `{channel.name} ({channel.id})`",
            color=LogColors.CHANEL_DELETE,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"{channel.name}", icon_url=channel.guild.icon.url if channel.guild.icon else None)

        actor = await get_actor_for_action(channel.guild, channel.id,discord.AuditLogAction.channel_delete)
        if actor:
            embed.set_footer(text=f"Eliminado por: {actor.name} ({actor.id})")
        else:
            embed.set_footer(text=f"Eliminado por: desconocido")
        
        await send_common_log(guild=channel.guild, embed=embed)


    #region on_guild_channel_update
    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: GuildChannel,
        after: GuildChannel
    ):

        embed = discord.Embed(
            title="Canal actualizado",
            description=f"El canal {before.mention} fue actualizado",
            color=LogColors.CHANNEL_EDIT,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"{before.name}", icon_url=before.guild.icon.url if before.guild.icon else None)
        actor = await get_actor_for_action(after.guild, after.id,discord.AuditLogAction.channel_update)
        if actor:
            embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
        else:
            embed.set_footer(text=f"Modificado por: desconocido")

        # Names
        if (before.name != after.name):
            embed.add_field(name="Nombre antes", value=f"{before.name}", inline=False)
            embed.add_field(name="Nombre despues", value=f"{after.name}", inline=False)

        # Topics
        if (not isinstance(before, (discord.VoiceChannel, discord.CategoryChannel)) and not isinstance(after, (discord.VoiceChannel, discord.CategoryChannel)) and before.topic != after.topic):
            embed.add_field(name="Topico antes", value=f"{before.topic if before.topic else 'Ninguno'}", inline=False)
            embed.add_field(name="Topico despues", value=f"{after.topic if after.topic else 'Ninguno'}", inline=False)
        
        # Slowmode
        if (not isinstance(before, discord.CategoryChannel) and not isinstance(after, discord.CategoryChannel))  and before.slowmode_delay != after.slowmode_delay:
            before_delay = before.slowmode_delay
            after_delay= after.slowmode_delay
            before_formatted = format_duration(timedelta(seconds=before_delay))
            after_formatted = format_duration(timedelta(seconds=after_delay))
            embed.add_field(name="Modo lento antes", value=f"{'Desactivado' if before_delay == 0 else before_formatted}")
            embed.add_field(name="Modo lento despues", value=f"{'Desactivado' if after_delay == 0 else after_formatted}")

        # RTC Regions
        if (isinstance(before, (discord.StageChannel, discord.VoiceChannel)) and isinstance(after, (discord.StageChannel, discord.VoiceChannel))) and before.rtc_region != after.rtc_region:
            embed.add_field(name="Región de voz (RTC) antes", value=f"{before.rtc_region if before.rtc_region else 'Automatico'}")
            embed.add_field(name="Región de voz (RTC) despues", value=f"{after.rtc_region if after.rtc_region else 'Automatico'}")

        # Permission Overwrites
        if before.overwrites != after.overwrites:
            actor = await get_actor_for_action(after.guild, after.id,discord.AuditLogAction.overwrite_update)
            if (not actor):
                actor = await get_actor_for_action(after.guild, after.id, discord.AuditLogAction.overwrite_create)
            if (not actor):
                actor = await get_actor_for_action(after.guild, after.id, discord.AuditLogAction.overwrite_delete)
            
            if actor:
                embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
            else:
                embed.set_footer(text=f"Modificado por: desconocido")
            overwrite_changes = diff_overwrites(before.overwrites, after.overwrites)

            # Los divido en chunks por el limite de discord
            if (overwrite_changes):
                chunk = ""
                for line in overwrite_changes:
                    if len(chunk) + len(line) > 900:
                        embed.add_field(
                            name="Permisos modificados",
                            value=chunk,
                            inline=False
                        )
                        chunk = ""

                    chunk += line + "\n"
                
                if chunk:
                    embed.add_field(
                        name="Permisos modificados",
                        value=chunk,
                        inline=False
                    )
        
        await send_common_log(guild=before.guild,embed=embed)
        

    #region on_member_update
    @commands.Cog.listener()
    async def on_member_update(
        self,
        before: discord.Member,
        after: discord.Member
        ):
        # Cambio de nombre (usuario)
        if before.display_name != after.display_name:
            embed = discord.Embed(
                title="Nombre actualizado",
                color=LogColors.PROFILE_NAME,
                timestamp=datetime.now(),
                description=f"`{before.name} [{before.id}]`"
            )
            embed.add_field(name="Antes",value=f"{before.display_name}",inline=False)
            embed.add_field(name="Despues", value=f"{after.display_name}", inline=False)
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)

            actor = await get_actor_for_action(after.guild, after.id,discord.AuditLogAction.member_update)
            if actor:
                embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
            else:
                embed.set_footer(text=f"Modificado por: desconocido")
            await send_common_log(guild=before.guild,embed=embed)

        # Cambio de PFP
        if before.display_avatar.url != after.display_avatar.url:
            embed = discord.Embed(
                title="Foto de perfil actualizada",
                color=LogColors.PROFILE_AVATAR,
                timestamp=datetime.now(),
                description=f"`{before.name} [{before.id}]`"
            )
            embed.add_field(name="Antes", value=f"{before.display_avatar.url}", inline=False)
            embed.add_field(name="Despues", value=f"{after.display_avatar.url}", inline=False)
            embed.set_author(name=after.name, icon_url=after.display_avatar.url)
            embed.set_thumbnail(url=after.display_avatar.url)
            actor = await get_actor_for_action(after.guild, after.id,discord.AuditLogAction.member_update)
            if actor:
                embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
            else:
                embed.set_footer(text=f"Modificado por: desconocido")
            await send_common_log(guild=before.guild, embed=embed)
        
        # Cambio de roles (usuario)
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added_roles = after_roles - before_roles
        removed_roles = before_roles - after_roles
        
        if added_roles or removed_roles:
            embed = discord.Embed(
                title="Usuario actualizado",
                color=LogColors.PROFILE_DATA,
                timestamp=datetime.now(),
                description=f"`{before.name} [{before.id}]`"
            )
            embed.set_author(name=before.name,icon_url=before.display_avatar.url)

            if added_roles:
                roles = ", ".join(r.mention for r in added_roles)
                embed.add_field(name="Roles añadidos", value=roles, inline=False)

            if removed_roles:
                roles = ", ".join(r.mention for r in removed_roles)
                embed.add_field(name="Roles quitados", value=roles, inline=False)

            actor = await get_actor_for_action(after.guild, after.id,discord.AuditLogAction.member_role_update)
            if actor:
                embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
            else:
                embed.set_footer(text=f"Modificado por: desconocido")

            await send_common_log(guild=before.guild, embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(
        self,
        before:discord.Role,
        after:discord.Role
    ):
        embed = discord.Embed(
            title="Rol actualizado",
            description=f"El rol {before.mention} fue actualizado.",
            color=LogColors.ROLE_EDIT,
            timestamp=datetime.now()
        )
        embed.set_author(name=f"{before.name}", icon_url=before.guild.icon.url if before.guild.icon else None)

        # Obtener quien realizo la modificación
        actor = await get_actor_for_action(after.guild, after.id, discord.AuditLogAction.role_update)
        if actor:
            embed.set_footer(text=f"Modificado por: {actor.name} ({actor.id})")
        else:
            embed.set_footer(text=f"Modificado por: desconocido")

        if (before.name != after.name):
            embed.add_field(name="Nombre", value=f"Antes: `{before.name}`\nDespues: `{after.name}`", inline=False)

        if (before.color != after.color):
            embed.add_field(name="Color",value=f"Antes: `{before.color}`\nDespues: `{after.color}`", inline=False)
        
        permission_changes = diff_permission(
            before.permissions,
            after.permissions
        )
        if (permission_changes):
            chunks = []
            current_chunk = ""

            permission_changes.sort(key=lambda p: p.name)
            for perm in permission_changes:
                icon_before = ":white_check_mark:" if perm.before else ":x:"
                icon_after = ":white_check_mark:" if perm.after else ":x:"
                
                block = (
                    f"# **{perm.name}**\n"
                    f"Antes: {icon_before}\u2800\u2800Después: {icon_after}\n\n"
                )

                if (len(current_chunk) + len(block) > 900):
                    chunks.append(current_chunk)
                    current_chunk = ""

                current_chunk += block
            
            if current_chunk:
                chunks.append(current_chunk)

            for i, chunk in enumerate(chunks):
                embed.add_field(
                    name="Permisos modificados:" if i == 0 else "Permisos modificados (cont.)",
                    value=chunk,
                    inline=False)

        await send_common_log(guild=before.guild,embed=embed)

    #region on_member_ban
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user : Union[discord.User,discord.Member]):
        # Si el desbaneo es realizado por Wiimu entonces ignorar acción
        # (los comandos de ban crean un log automatico al banear)
        actor, reason = await get_actor_for_moderation_action(guild, user.id, discord.AuditLogAction.ban) 
        if (actor and actor.id == int(APP_ID)):
            return
        
        staff_role = guild.get_role(int(STAFF_ROLE_ID)) 
        staff_mention : Union[str,None] = f"{(staff_role.mention*3) if staff_role else None}"
        embed = discord.Embed(
            title="Baneo manual",
            description=(
                f"Se ha realizado un baneo manual."
                f"\nModerador/a: {actor.mention if actor else 'Desconocido/a'}" 
                f"\n\nBaneado:\n\u2800\u2800`{user.name} [{user.id}]`"
                f"\n\nRazón: {reason if reason else 'No especificada'}"),
            timestamp=datetime.now(),
            color=ModerationColors.BAN
            )
        embed.set_author(name=guild.name, icon_url=f"{guild.icon.url}" if guild.icon else None)
        embed.set_footer(text=f"ID: {user.id}")

        await send_moderation_log(guild=guild,message=staff_mention,embed=embed)

    #region on_member_unban
    @commands.Cog.listener()
    async def on_member_unban(self, guild:discord.Guild, user:Union[discord.User,discord.Member]):
        # Si el desbaneo es realizado por Wiimu entonces ignorar acción
        # (los comandos de moderación crean un log automatico al banear)
        actor, reason = await get_actor_for_moderation_action(guild, user.id, discord.AuditLogAction.unban) 
        if (actor and actor.id == int(APP_ID)):
            return
        
        staff_role = guild.get_role(int(STAFF_ROLE_ID)) 
        staff_mention : Union[str, None] = f"{(staff_role.mention*3) if staff_role else None}"
        embed = discord.Embed(
            title="Desbaneo manual",
            description=(
                f"Se ha realizado un desbaneo manual."
                f"\nModerador/a: {actor.mention if actor else 'Desconocido/a'}" 
                f"\n\nDesbaneado:\n\u2800\u2800`{user.name} [{user.id}]`"
                f"\n\nRazón: {reason if reason else 'No especificada'}"),
            timestamp=datetime.now(),
            color=ModerationColors.UNBAN
            )
        embed.set_author(name=guild.name, icon_url=f"{guild.icon.url}" if guild.icon else None)
        embed.set_footer(text=f"ID: {user.id}")

        await send_moderation_log(guild=guild,message=staff_mention,embed=embed)

async def setup(bot):
    await bot.add_cog(Logs(bot))
