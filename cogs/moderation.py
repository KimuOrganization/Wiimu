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

class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    #region send_dm
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="enviar_dm", description="Envia un mensaje privado a un usuario.")
    @app_commands.describe(
        usuario = "Usuario concreto al que se le va enviar el mensaje por privado",
        mensaje = "Mensaje a enviar."
    )
    @app_commands.default_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    @app_commands.checks.has_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    async def send_dm(self, interaction: discord.Interaction, usuario: Union[discord.Member, discord.User], mensaje: str):
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("Ha ocurrido un error.")

        try:
            await send_moderation_dm(
                guild=guild,
                target=usuario,
                title="Mensaje del staff",
                description=mensaje,
                color=ModerationColors.PRIVATE_MESSAGE,
                mandar_dm=True
                )
        except:
            return await interaction.followup.send(f"Ha ocurrido un error al intentar enviarle el mensaje a {usuario.mention}.")

        # Moderation log
        log_embed = discord.Embed(
            title="Mensaje enviado a usuario.",
            color=ModerationColors.PRIVATE_MESSAGE,
            description=(
                f"**Moderador/a:** {interaction.user.mention}\n"
                f"**Usuario:** `{usuario.name} [{usuario.id}`]\n"
                f"**Mensaje:** {mensaje}"),
            timestamp=datetime.now()
        )
        log_embed.set_author(name=guild.name,icon_url=guild.icon.url if guild.icon else None)
        log_embed.set_footer(text=f"ID: {interaction.user.id}")

        await send_moderation_log(
            guild=guild,
            embed=log_embed
        )

        return await interaction.followup.send(f"El mensaje dirigido a {usuario.mention} fue enviado con exito.")

    #region ban
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="ban", description="Banear a un usuario")
    @app_commands.describe(
        usuario="Usuario o ID del usuario a banear.",
        razón = "La razón le va a llegar al DM.",
        borrar_mensajes = "Default = True",
        dias_de_purga = "Borrar mensajes de los últimos X días (default = 1 | máx = 7)",
        mandar_dm="Default = True"
    )
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        razón: str,
        borrar_mensajes: bool = True,
        dias_de_purga: app_commands.Range[int,0,7] = 1,
        mandar_dm: bool = True
    ):
        await interaction.response.defer(ephemeral=True)

        target = await resolve_user(interaction, usuario)
        if not target:
            return await interaction.followup.send(
                "Usuario invalido...", ephemeral=True
            )
        
        guild = interaction.guild
        if not guild:
            return

        if interaction.user.id == usuario.id:
            return await interaction.followup.send(
                "Te falla? te estas intentando banear a vos misma.", ephemeral=True
            )

        embed = discord.Embed(
            title="Usuario baneado",
            description=(
                f"**Razón:** {razón or 'No especificada'}\n"
                f"**Moderador/a:** {interaction.user.mention}\n"),
            timestamp=datetime.now(),
            color=ModerationColors.BAN
        )
        embed.set_author(name=f"{guild.name}",icon_url=guild.icon.url if guild.icon else None)
        embed.add_field(name="Baneado", value=f"\u2800\u2800`{target.name} [{target.id}]`", inline=False)
        embed.set_footer(text="ID: "+str(interaction.user.id))

        mensaje_privado = await send_moderation_dm(
            guild=guild,
            target=target,
            title="Has sido banead@ del servidor",
            description=f"**Razón:** {razón or 'No especificada'}",
            color=ModerationColors.BAN,
            mandar_dm=mandar_dm
        )

        try:
            await guild.ban(
                target,
                reason=razón or 'No especificada',
                delete_message_days=dias_de_purga if borrar_mensajes else 0,
            )
        except:
            if (mensaje_privado):
                # En caso de que no se haya podido banear al usuario, eliminar el mensaje privado.
                await mensaje_privado.delete()
            return await interaction.followup.send(
                f"No se pudo banear a {target.mention}. Posiblemente no tengo los permisos suficientes."
            )

        await interaction.followup.send(
            f"{target.mention} fue baneado.", ephemeral=True
        )

        return await send_moderation_log(guild, embed)

    #region kick
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="kick", description="Expulsa a un usuario")
    @app_commands.describe(
        usuario="Usuario o ID del usuario a expulsar.",
        razón = "La razón le va a llegar al DM.",
        mandar_dm="Default = True"
    )
    @app_commands.default_permissions(kick_members=True)
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        razón: str,
        mandar_dm: bool = True
        ):
        await interaction.response.defer(ephemeral=True)

        target = await resolve_user(interaction, usuario)
        if not target:
            return await interaction.followup.send(
                "Usuario invalido...", ephemeral=True
            )
        
        guild = interaction.guild
        if not guild:
            return
       
        if interaction.user.id == usuario.id:
            return await interaction.followup.send(
                "Te falla? te estas intentando expulsar a vos misma.", ephemeral=True
            )

        embed = discord.Embed(
            title="Usuario expulsado",
            description=(
                f"**Razón:** {razón or 'No especificada'}\n"
                f"**Moderador/a:** {interaction.user.mention}\n"),
            timestamp=datetime.now(),
            color=ModerationColors.KICK
        )
        embed.add_field(name="Expulsado", value=f"\u2800\u2800`{target.name} [{target.id}]`", inline=False)
        embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="ID: "+str(interaction.user.id))

        mensaje_privado = await send_moderation_dm(
            guild=guild,
            target=target,
            title="Has sido expulsad@ del servidor",
            description=f"**Razón:** {razón or 'No especificada'}",
            color=ModerationColors.KICK,
            mandar_dm=mandar_dm)

        try:
            await guild.kick(
                target,
                reason=razón
            )
        except:
            if (mensaje_privado):
                # En caso de que no se haya podido expulsar al usuario, eliminar el mensaje privado.
                await mensaje_privado.delete()
            return await interaction.followup.send(
                f"No se pudo expulsar a {target.mention}. Posiblemente no tengo los permisos suficientes."
            )

        await interaction.followup.send(
            f"{target.mention} fue expulsado.", ephemeral=True
        )

        return await send_moderation_log(guild, embed)

    #region mute
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="mute", description="Aisla a un usuario")
    @app_commands.describe(
        usuario="Usuario o ID del usuario a aislar.",
        # No es necesario poner todas las partes, ej: 1w2d3h4m5s o 1d2h3m4s o 1h2m3s o 1m2s o 1s
        duración="Formato 1w2d3h4m5s (La duración default es de 1 dia)",
        razón = "La razón le va a llegar al DM.",
        mandar_dm="Default = True"
    )
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.checks.has_permissions(moderate_members=True)
    async def mute(
        self,
        interaction: discord.Interaction,
        usuario: discord.Member,
        duración: Union[str,None] = "1d",
        razón: Union[str,None] = None,
        mandar_dm: bool = True
        ):
        await interaction.response.defer(ephemeral=True)

        target = await resolve_user(interaction, usuario)
        if not target or not isinstance(target, discord.Member):
            return await interaction.followup.send(
                "Usuario invalido...", ephemeral=True
            )

        if interaction.user.id == usuario.id:
            return await interaction.followup.send(
                "Te falla? te estas intentando mutear a vos misma.", ephemeral=True
            )
 
        if (not duración):
            return await interaction.followup.send(
                "Tenes que especificar una duración."
            )

        try:
            seconds = parse_duration(duración)
        except ValueError:
            return await interaction.followup.send(
                "Formato invalido. Ejemplo: 1w2d3h4m5s", ephemeral=True
            )
        
        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)

        guild = interaction.guild
        if not guild:
            return

        embed = discord.Embed(
            title="Usuario aislado",
            description=(
                f"**Razón:** {razón or 'No especificada'}\n"
                f"**Moderador/a:** {interaction.user.mention}\n"
                f"**Hasta:** <t:{int(until.timestamp())}:f>"),
            timestamp=datetime.now(),
            color=ModerationColors.MUTE,
        )
        embed.add_field(name="Aislado", value=f"\u2800\u2800`{target.name} [{target.id}]`", inline=False)
        embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="ID: "+str(interaction.user.id))

        mensaje_privado = await send_moderation_dm(
            guild=guild,
            target=target,
            title="Has sido aislad@ en el servidor",
            description=f"**Razón:** {razón or 'No especificada'}",
            color=ModerationColors.MUTE,
            mandar_dm=mandar_dm)

        try:
            await target.edit(
                timed_out_until=until
            )
        except:
            if (mensaje_privado):
                # En caso de que no se haya podido aislar al usuario, eliminar el mensaje privado.
                await mensaje_privado.delete()
            return await interaction.followup.send(
                f"No se pudo aislar a {target.mention}. Posiblemente no tengo los permisos suficientes."
            )

        await interaction.followup.send(
            f"{target.mention} fue aislado.", ephemeral=True
        )

        return await send_moderation_log(guild, embed)
    
    #region softban
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="softban", description="Banea a un usuario y lo desbanea al instante, util para echar a alguien y borrar sus mensajes.")
    @app_commands.describe(
        usuario="Usuario o ID del usuario a banear.",
        razón = "La razón le va a llegar al DM.",
        borrar_mensajes = "Default = True",
        dias_de_purga = "Borrar mensajes de los últimos X días (default = 1 | máx = 7)",
        mandar_dm="Default = True"
    )
    @app_commands.default_permissions(ban_members=True)
    @app_commands.checks.has_permissions(ban_members=True)
    async def soft_ban(
        self,
        interaction: discord.Interaction,
        usuario: discord.User,
        razón: str,
        borrar_mensajes: bool = True,
        dias_de_purga: app_commands.Range[int,0,7] = 1,
        mandar_dm: bool = True
    ):
        await interaction.response.defer(ephemeral=True)

        target = await resolve_user(interaction, usuario)
        if not target:
            return await interaction.followup.send(
                "Usuario invalido...", ephemeral=True
            )
        
        guild = interaction.guild
        if not guild:
            return
        
        if (interaction.user.id == usuario.id):
            return await interaction.followup.send(
                "Te falla? estas intentando soft-banear a vos misma.", ephemeral=True
            )

        embed = discord.Embed(
            title="Usuario soft-baneado",
            description=(
                f"**Razón:** {razón or 'No especificada'}\n"
                f"**Moderador/a:** {interaction.user.mention}\n"),
            timestamp=datetime.now(),
            color=ModerationColors.SOFT_BAN
        )
        embed.add_field(name="Soft-baneado", value=f"\u2800\u2800`{target.name} [{target.id}]`", inline=False)
        embed.set_author(name=f"{guild.name}",icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="ID: "+str(interaction.user.id))

        mensaje_privado = await send_moderation_dm(
            guild=guild,
            target=target,
            title="Has sido expulsad@ del servidor",
            description=f"**Razón:** {razón or 'No especificada'}",
            color=ModerationColors.KICK,
            mandar_dm=mandar_dm)

        try:
            await guild.ban(
                target,
                reason=razón,
                delete_message_days=dias_de_purga if borrar_mensajes else 0,
            )

            await guild.unban(
                target,
                reason=f"Desbaneo automatico por soft-ban\nModerador/a: {interaction.user.name} ({interaction.user.id})"
            )
        except:
            if (mensaje_privado):
                # En caso de que no se haya podido soft-banear al usuario, eliminar el mensaje privado.
                await mensaje_privado.delete()
            return await interaction.followup.send(
                f"No se pudo soft-banear a {target.mention}. Posiblemente no tengo los permisos suficientes."
            )

        await interaction.followup.send(
            f"{target.mention} fue soft-baneado.", ephemeral=True
        )

        return await send_moderation_log(guild, embed)
    
    #region purgar_mensajes
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(name="purgar_mensajes", description="Elimina una cantidad determinada de mensajes, en el canal actual.")
    @app_commands.describe(
        cantidad = "Cantidad de mensajes a eliminar desde el ultimo enviado en el canal actual.",
        usuario = "Usuario concreto al que se le van a borrar los mensajes.",
        canal = "Canal en el que se van a borrar los mensajes."
    )
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.checks.has_permissions(manage_messages=True)
    async def purgar_mensajes(
        self,
        interaction: discord.Interaction,
        cantidad: app_commands.Range[int, 1 , 100],
        razón: Union[str,None] = None,
        usuario: Union[discord.Member, discord.User, None] = None,
        canal: Union[discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread, None] = None
        ):
        await interaction.response.defer(ephemeral=True)
        if (cantidad <= 0):
            return await interaction.followup.send("La cantidad tiene que ser mayor a 0 y menor o igual a 100.")
        
        guild = interaction.guild
        if (not guild):
            return

        current_channel = interaction.channel
        desired_channel = canal
        channel_to_purge = desired_channel if desired_channel else current_channel
        
        if (channel_to_purge and (channel_to_purge.id in SPECIAL_CHANNELS)):
            return await interaction.followup.send("No puedes ejecutar este comando en canales de moderación.")


        if (not isinstance(channel_to_purge, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread))):
            return await interaction.followup.send("No puedes ejecutar este comando en este tipo de canal.")

        def purge_check(message: discord.Message):
            if usuario and message.author.id != usuario.id:
                return False
            return True
        
        try:
            deleted = await channel_to_purge.purge(
                limit=cantidad,
                bulk=True,
                reason=razón,
                check=purge_check
            )

        except discord.Forbidden:
            return await interaction.followup.send("Parece que no tengo los permisos necesarios para purgar mensajes.")
        except:
            return await interaction.followup.send("Ha ocurrido un error al intentar purgar los mensajes.")

        additional_line = f"Usuario: `{usuario.name if usuario else ''} [{usuario.id if usuario else ''}]`\n"
        embed = discord.Embed(
            title="Purga de mensajes",
            description=(
                f"{additional_line if usuario else ''}"
                f"**Canal:** `{channel_to_purge.name} [{channel_to_purge.id}]`\n"
                f"**Razón:** {razón or 'No especificada'}\n"
                f"**Moderador/a:** {interaction.user.mention}\n"
                f"**Cantidad de mensajes eliminados:** {len(deleted)}\n"),
            timestamp=datetime.now(),
            color=ModerationColors.MESSAGE_PURGE
        )
        embed.set_author(name=f"{guild.name}",icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(text="ID: "+str(interaction.user.id))

        await interaction.followup.send(
            f"Se borraron **{len(deleted)}** mensajes.",
            ephemeral=True
        )

        return await send_moderation_log(guild, embed)

async def setup(bot):
    await bot.add_cog(Moderation(bot))
