import discord
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Tuple, Sequence
import asyncio
import logging
logger = logging.getLogger(__name__)

async def get_actor_for_action(
    guild: discord.Guild,
    target_id: int,
    action: discord.AuditLogAction,
) -> discord.User | discord.Member | None:
    try:
        async for entry in guild.audit_logs(limit=1, action=action):
            target = getattr(entry.target, "id", None)

            if target == target_id:
                return entry.user

    except discord.Forbidden:
        logger.warning(
            "El bot no tiene permisos para leer Audit Logs en '%s' (%s).",
            guild.name,
            guild.id,
        )

    except discord.DiscordServerError as ex:
        # Error 5xx del lado de Discord/Cloudflare
        logger.warning(
            "Discord devolvió un error de servidor al consultar Audit Logs (%s)."
            "Se omitirá el actor de la acción.",
            ex.status,
        )

    except discord.HTTPException as ex:
        logger.warning(
            "HTTPException al consultar Audit Logs: %s (status=%s)",
            ex,
            getattr(ex, "status", "unknown"),
        )

    except Exception:
        logger.exception(
            "Excepción inesperada al consultar Audit Logs."
        )

    return None

async def get_actor_for_moderation_action(
    guild: discord.Guild,
    target_id: int,
    action: discord.AuditLogAction,
) -> tuple[
    Optional[Union[discord.Member, discord.User]],
    Optional[str],
]:
    # Esperar a que Discord genere el audit log
    await asyncio.sleep(1.5)

    try:
        async for entry in guild.audit_logs(limit=5, action=action):
            target = getattr(entry.target, "id", None)

            if target != target_id:
                continue

            # utcnow() de discord.py ya devuelve datetime aware en UTC
            delta = discord.utils.utcnow() - entry.created_at

            # Aceptar entradas recientes (10 segundos)
            if delta.total_seconds() < 10:
                return entry.user, entry.reason

    except discord.Forbidden:
        logger.warning(
            "El bot no tiene permisos para leer Audit Logs en '%s' (%s).",
            guild.name,
            guild.id,
        )

    except discord.DiscordServerError as ex:
        # Errores 5xx del lado de Discord/Cloudflare (como el 520 que viste)
        logger.warning(
            "Discord devolvió un error de servidor al consultar Audit Logs "
            "para la acción %s en '%s' (%s). status=%s",
            action,
            guild.name,
            guild.id,
            ex.status,
        )

    except discord.HTTPException as ex:
        logger.warning(
            "HTTPException al consultar Audit Logs para la acción %s en '%s' (%s): %s (status=%s)",
            action,
            guild.name,
            guild.id,
            ex,
            getattr(ex, "status", "unknown"),
        )

    except Exception:
        logger.exception(
            "Excepción inesperada al consultar Audit Logs para la acción %s en '%s' (%s).",
            action,
            guild.name,
            guild.id,
        )

    return None, None
        

async def send_moderation_log(
    guild:discord.Guild,
    embed: discord.Embed,
    command_log_channel_id : int,
    message: Union[str, None] = None
):
    channel= guild.get_channel(command_log_channel_id)

    if (not isinstance(channel, discord.TextChannel)):
        raise RuntimeError(
            "[ERROR(utils/logs.py - send_moderation_log)]: El canal de logs de moderación no es del tipo 'TextChannel'. Revisar variable de entorno 'COMMAND_CHANNEL_ID'."
        )
    
    await channel.send(f"{message if message else ''}",embed=embed)

async def send_common_log(guild:discord.Guild, embed: discord.Embed,log_channel_id:int, message: Union[str, None] = None, files: Sequence[discord.File] = []):
    channel= guild.get_channel(log_channel_id)

    if (not isinstance(channel, discord.TextChannel)):
        raise RuntimeError(
            "[ERROR(utils/moderation.py - send_common_log)]: El canal de logs no es del tipo 'TextChannel'. Revisar ID del canal de logs en la base de datos."
        )
    
    await channel.send(f"{message if message else ''}", embed=embed, files=files)

async def send_moderation_dm(
    *,
    guild:discord.Guild,
    target: Union[discord.User, discord.Member],
    title: str,
    description: str,
    color: int,
    mandar_dm: bool,
    staff_role_id:int,
    message: Union[str,None] = None
    ) -> Union[discord.Message, None]:
    if not mandar_dm:
        return None
    

    staff_role : Union[discord.Role, None] = guild.get_role(staff_role_id)
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

    dm_embed = discord.Embed(
        title=title,
        description=(
            f"{description}"
            f"{staff_mention if staff_role and staff_members and staff_mention else ''}"
        ),
        color=color,
        timestamp=datetime.now()
    )
    dm_embed.set_author(
        name=guild.name,
        icon_url=guild.icon.url if guild.icon else None
    )

    try:
        return await target.send(f"{message if message else ''}",embed=dm_embed, silent=True)
    except:
        return None # DMs Cerrados
