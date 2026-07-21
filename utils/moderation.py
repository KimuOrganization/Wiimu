import discord
from datetime import datetime, timedelta, timezone
from typing import Union, Optional, Tuple, Sequence
import asyncio
import logging
logger = logging.getLogger(__name__)

async def get_actor_for_action(guild: discord.Guild,target_id: int, action: discord.AuditLogAction) -> Union[discord.User, discord.Member, None]:
    async for entry in guild.audit_logs(limit=1, action=action):
        if (entry is None or entry.target is None):
            return None
        
        if (entry.target.id == target_id):
            if (entry.created_at < discord.utils.utcnow() - timedelta(seconds=5)):
                return None
            return entry.user

    return None

async def get_actor_for_moderation_action(guild: discord.Guild, target_id: int, action: discord.AuditLogAction) -> Tuple[Optional[Union[discord.Member, discord.User]],Optional[str]]:
    await asyncio.sleep(1.5) # Delay para esperar a que el audit log se genere

    async for entry in guild.audit_logs(limit=5, action=action):
        if entry.target and entry.target.id == target_id:
            delta = datetime.now(timezone.utc) - entry.created_at
            if (delta.total_seconds() < 10):
                return entry.user, entry.reason
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
    channel= guild.get_channel(int(log_channel_id))

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
