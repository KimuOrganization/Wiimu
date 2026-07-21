import logging
import discord
from discord.ext import commands
from core.bot import Bot
import asyncio

logger = logging.getLogger(__name__)

from core.config import (
    WELCOME_IMAGE_PATH,
    WELCOME_CANVAS
)

from utils.image import create_welcome_image

class Welcome(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot : Bot = bot

    @property
    def channels(self):
        return self.bot.config.channels # type: ignore
    
    @property
    def roles(self):
        return self.bot.config.roles # type: ignore

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

    @commands.Cog.listener("on_member_join")
    async def welcome_on_member_join(self, member: discord.Member):
        # Creo una tarea para que se cree la imagen y se mande el mensaje de bienvenida en "paralelo" ya que no es prioritario
        asyncio.create_task(self.send_welcome(member))

        # Priorizo y espero a que se de el rol de bienvenida (critico)
        await self.give_welcome_role(member)

async def setup(bot: Bot):
    await bot.add_cog(Welcome(bot))