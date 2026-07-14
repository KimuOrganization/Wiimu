import discord
from discord.ext import commands
from typing import Union
from core.config import HONEYPOT_CHANNEL_ID, COMMAND_CHANNEL_ID, ART_CHANNEL_ID, PROJECTS_CHANNEL_ID, DESKTOPS_CHANNEL_ID
from utils.colors import ModerationColors
from datetime import datetime

AUTO_THREAD_CHANNELS = [ART_CHANNEL_ID, PROJECTS_CHANNEL_ID, DESKTOPS_CHANNEL_ID]

class HoneyPot(commands.Cog):
    def __init__(self,bot:commands.Bot):
        self.bot = bot

    async def _send_ban_dm(self,guild:discord.Guild, user:Union[discord.User, discord.Member], reason:str):
        """Enviar un dm ANTES del baneo"""
        embed = discord.Embed(
            title= "Has sido banead@ del servidor",
            description=f"**Razón:** {reason or 'No especificada.'}",
            color=ModerationColors.BAN,
            timestamp=datetime.now()
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )
        embed.set_footer(
            text="Este baneo se realizo de forma automática. En caso de recuperar tu cuenta y querer acceder al servidor otra vez, contactate con algún miembro del staff para que tu situación sea evaluada."
        )
        
        try:
            return await user.send(embed=embed)
        except:
            return None # DMs cerrados

    async def _send_ban_log(self, guild:discord.Guild, user: Union[discord.User, discord.Member], reason:str):
        """Como tenga que documentar esta funcion con lo claro que es el nombre me cueteo"""
        # Evitar warnings de pylance
        if self.bot.user is None:
            return

        embed = discord.Embed(
            title="[HoneyPot] Usuario baneado",
            description=(
                f"**Razón:** {reason}\n"
                f"**Moderador/a:** {self.bot.user.mention}\n"
            ),
            color=discord.Color.orange(),
            timestamp=datetime.now()
        )
        embed.set_author(
            name=guild.name,
            icon_url=guild.icon.url if guild.icon else None
        )
        embed.add_field(name=f"Baneado", value=f"\u2800\u2800`{user.name} [{user.id}]`", inline=False)
        embed.set_footer(text="ID: "+str(user.id))
        
        log_channel = guild.get_channel(int(COMMAND_CHANNEL_ID))

        # Evitar warning de pylance
        if not isinstance(log_channel, discord.TextChannel):
            return
        
        await log_channel.send(embed=embed)

    async def _ban_member(self, guild: discord.Guild, member: Union[discord.User, discord.Member], reason: str):
        """PARA QUE SERVIRA ESTA FUNCIÓN?"""
        await guild.ban(
            member,
            reason=reason,
            delete_message_days=1
        )
    
    @commands.Cog.listener("on_message")
    async def on_honeypot_message(self, message: discord.Message):
        # Ignorar DMs
        if message.guild is None:
            return
        
        # Ignorar otros canales
        if str(message.channel.id) !=str(HONEYPOT_CHANNEL_ID):
            return


        # Enviar DM
        await self._send_ban_dm(message.guild, message.author, "Comportamiento de bot de spam.")

        # Enviar log de Baneo
        await self._send_ban_log(message.guild, message.author, "Mensaje en canal trampa.")

        # Realizar baneo
        await self._ban_member(message.guild, message.author, "[HoneyPot] Mensaje en canal trampa.")

async def setup(bot):
    await bot.add_cog(HoneyPot(bot))
