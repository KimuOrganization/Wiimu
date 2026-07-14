from typing import cast
import discord
from discord.ext import commands
from core.bot import Bot

from core.config import (
    WELCOME_CHANNEL_ID,
    WELCOME_ROLE_ID,
    WELCOME_IMAGE_PATH,
    WELCOME_CANVAS
)

from utils.image import create_welcome_image

class Welcome(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild

        # Canal de bienvenida
        channel = guild.get_channel(int(WELCOME_CHANNEL_ID))
        if not channel or not isinstance(channel, discord.TextChannel):
            return
        
        bot = cast(Bot, self.bot)
        if (not bot or not bot.http_session):
            return

        # Asignar rol
        role = guild.get_role(int(WELCOME_ROLE_ID))
        if role:
            await member.add_roles(role, reason="Rol automatico al unirse")

        # Avatar URL
        avatar_url = member.display_avatar.replace(
            format="png", size=128
        ).url

        image_buffer = await create_welcome_image(
            session=bot.http_session,
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

async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))