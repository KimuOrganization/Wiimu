import discord
from discord import app_commands
from discord.ext import commands
from core.config import GUILD_ID

from core.bot import Bot

class Minecraft(commands.Cog):
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="servidor_minecraft",
        description="Información para ingresar y vincular tu cuenta del servidor de Minecraft"
    )
    async def minecraft_server(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            return
        
        embed = discord.Embed(
            title="Servidor de minecraft",
            description=(
                "Conectate a nuestro servidor de minecraft y vinculá tu cuenta de discord al ingresar al servidor! __No importa si sos premium o no premium__ <3.\n"
                "Por cierto, hay un mapa web del mundo 👀\n"
                "https://map.kimu.moe/\n\n\u2800"
            )
        )
        embed.add_field(
            name="**🌐 Información del servidor**",
            value="**IP:** `play.kimu.moe`\n**Versión:** `Java 26.2`\n\n\u2800",
            inline=False
        )
        embed.add_field(
            name="**🔐 ¿Cómo ingreso si soy no premium?**",
            value=(
                "**1.** Ingresa al servidor.\n"
                "**2.** Si es tu primera vez, registrate con:\n"
                "   `/register contraseña contraseña`\n"
                "**3.** En tus proximos ingresos, inicia sesión con:\n"
                "   `/login contraseña`\n\n\u2800"
            ),
            inline=False
        )
        embed.add_field(
            name="**🔗 Vincula tu cuenta con Discord**",
            value=(
                "**1.** Una vez dentro del servidor, veras que en el chat de minecraft aparecera un mensaje diciendo que utilices `/link xxxxx`.\n"
                "**2.** Ve al servidor de discord, escribe `/link` en cualquier canal de texto, y veras el comando de un bot llamado `Kimu.jar`, presionalo e ingresa el código que te brindo el servidor de minecraft. (No te preocupes, nadie vera que ejecutas el comando!)\n"
                "**3.** Si la vinculación es exitosa, ya te podras mover en el servidor de minecraft, y veras tu rol del servidor de discord en la lista de jugadores de minecraft presionando TAB.\n\n\u2800"
            ),
            inline=False
        )
        embed.set_author(name=f"{guild.name}",icon_url=guild.icon.url if guild.icon else None)
        embed.set_footer(
            text="Net café • ¡Nos vemos dentro!"
        )
        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )

async def setup(bot: Bot):
    await bot.add_cog(Minecraft(bot))