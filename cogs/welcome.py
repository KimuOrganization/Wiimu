import logging
import discord
from discord.ext import commands
from core.bot import Bot
import time
import asyncio
from core.config import (
    WELCOME_IMAGE_PATH,
    WELCOME_CANVAS
)
from utils.image import create_welcome_image
import json
logger = logging.getLogger(__name__)

HANDLED_TTL_SECONDS = 600

class Welcome(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot : Bot = bot

        self._handled:dict[int, float] = {}
        self._handled_lock = asyncio.Lock()

        self._bg_tasks: set[asyncio.Task] = set()

    @property
    def channels(self):
        return self.bot.config.channels # type: ignore
    
    @property
    def roles(self):
        return self.bot.config.roles # type: ignore

    def _spawn(self, coro) -> None:
        """Lanza una tarea en segundo plano manteniendo una referencia a ella"""
        task = asyncio.create_task(coro)
        self._bg_tasks.add(task)
        task.add_done_callback(self._bg_tasks.discard)

    async def send_welcome(self, member: discord.Member):
        guild = member.guild
        # Canal de bienvenida
        channel = guild.get_channel(self.channels.common.WELCOME)
        # Evitar warnings de pylance
        if not channel or not isinstance(channel, discord.TextChannel):
            logger.critical(
                "No se encontró el canal de bienvenida configurado (ID: %s) en el servidor '%s' (%s). "
                "Revisar clave CHANNELS_ID.COMMON.WELCOME en la DB.",
                self.channels.common.WELCOME,
                guild.name,
                guild.id
            )
            return
        
        if self.bot.http_session is None:
            logger.warning("La sesión HTTP del bot para crear las imagenes de bienvenida, no existe.")
            return
        
        try:
            # Avatar URL
            avatar_url = member.display_avatar.replace(
                format="png", size=128
            ).url

            image_buffer = await create_welcome_image(
                session=self.bot.http_session,
                background_path=WELCOME_IMAGE_PATH,
                avatar_url=avatar_url,
                display_name=member.display_name,
                username=member.name,
                size=(WELCOME_CANVAS["width"], WELCOME_CANVAS["height"])
            )

            file = discord.File(
                fp=image_buffer,
                filename=f"welcome_{member.id}.png"
            )

            await channel.send(
                content=(
                    f"Welcome to *{guild.name}* {member.mention}. Take a seat and get comfy!"
                ),
                file=file
            )
        except Exception:
            logger.exception(
                "Error enviando bienvenida (imagen + mensaje) para %s (%s)",
                member,
                member.id
            )


    async def give_welcome_role(self, member: discord.Member):
        guild = member.guild

        # Asignar rol
        role = guild.get_role(self.roles.common.WELCOME)
        if role is None:
            logger.critical(
                "No se encontró el rol de bienvenida configurado (ID: %s) en el servidor '%s' (%s)."
                "Revisar la clave ROLES_ID.COMMON.WELCOME en la db.",
                self.roles.common.WELCOME,
                guild.name,
                guild.id
            )
            return
        
        try:
            await member.add_roles(role, reason="Rol automático al unirse")
        except discord.Forbidden:
            logger.error(
                "Permisos insuficientes al asignar el rol '%s' (%s) en el servidor '%s' (%s).",
                role.name,
                role.id,
                guild.name,
                guild.id
            )
        except discord.HTTPException:
            logger.exception(
                "Discord devolvió un HTTPException al asignar el rol '%s' (%s) al usuario '%s' (%s).",
                role.name,
                role.id,
                member,
                member.id
            )

    async def handle_new_member(self, member: discord.Member, source:str) -> bool:
        """Punto idempotente de entrada de miembros al servidor. (puede ser llamado de distintos lugares sin duplicar la bienvenida)"""
        if member.bot:
            return False

        async with self._handled_lock:
            now = time.monotonic()
            # Limpieza de entradas vencidas
            self._handled = {
                member_id: ts
                for member_id, ts in self._handled.items()
                if now - ts < HANDLED_TTL_SECONDS
            }

            if member.id in self._handled:
                logger.info(
                    "Bienvenida ya procesada para %s (%s). Origen ingorado: %s",
                    member, member.id, source
                )
                return False

            if any(role.id == self.roles.common.WELCOME for role in member.roles):
                logger.info(
                    "El usuario %s (%s) ya posee el rol de bienvenida. Origen ignorado. %s",
                    member, member.id, source
                )
                return False

            self._handled[member.id] = now

        logger.info(
            "Procesando bienvenida para %s (%s). Origen: %s",
            member, member.id, source
        )

        # Imagen + mensaje en paralelo, no es prioritario
        self._spawn(self.send_welcome(member))

        # Priorizo rol de bienvenida
        await self.give_welcome_role(member)

        return True

    @commands.Cog.listener("on_member_join")
    async def welcome_on_member_join(self, member: discord.Member):
        await self.handle_new_member(member, source="on_member_join")

    @commands.Cog.listener("on_member_remove")
    async def forget_member_on_leave(self, member: discord.Member):
        # Si se va y vuelve a entrar, limpiarlo en los registros recientes para que reciba la bienvenida de nuevo
        async with self._handled_lock:
            self._handled.pop(member.id, None)

    @commands.Cog.listener("on_socket_raw_receive")
    async def raw_member_add_fallback(self, msg):
        """Utiliza la información del socket para darle la bienvenida a los miembros que tengan roles con integraciones a la hora de unirse al servidor y no disparen el evento de on_member_join"""
        # Descartar casi todo el tráfico del gateway sin parsear JSON
        if not isinstance(msg, str) or "GUILD_MEMBER_ADD" not in msg:
            return
        try:
            data = json.loads(msg)
        except ValueError:
            return
        if data.get("t") != "GUILD_MEMBER_ADD":
            return

        d = data["d"]
        if d.get("user", {}).get("bot"):
            return

        self._spawn(self._fallback_welcome(int(d["guild_id"]), int(d["user"]["id"])))

    async def _fallback_welcome(self, guild_id: int, user_id: int):
        # Dejar que on_member_join corra primero si es que se dispara
        await asyncio.sleep(2)
        try:
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                return
            member = guild.get_member(user_id) or await guild.fetch_member(user_id)
            await self.handle_new_member(member, source="raw_member_add_fallback")
        except Exception:
            logger.exception("Error en respaldo de bienvenida para %s", user_id)

async def setup(bot: Bot):
    await bot.add_cog(Welcome(bot))