import discord
from discord import app_commands
from discord.ext import commands
from utils.help_data import HELP_COMMANDS, OPTIONAL_ARGUMENTS_INFO
from core.config import GUILD_ID
from typing import Union

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="wiimu_mensaje",
        description="Haz que Wiimu envie un mensaje en el canal actual"
    )
    @app_commands.default_permissions(
        administrator=True
    )
    async def wiimu_mensaje(self, interaction: discord.Interaction, mensaje:str):
        await interaction.response.defer(ephemeral=True)
        if (not mensaje):
            return await interaction.followup.send("¿un mensaje vacio? no voy a enviar eso >:(",ephemeral=True)

        if not isinstance(interaction.channel, (discord.TextChannel, discord.VoiceChannel, discord.StageChannel, discord.Thread)):
            return await interaction.followup.send("Esto no es un canal de texto owo")

        await interaction.channel.send(mensaje)

        return await interaction.followup.send("Mensaje enviado uwu",ephemeral=True,silent=True)

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="help",
        description="Guía detallada de comandos de moderación (solo staff)"
    )
    @app_commands.default_permissions(ban_members=True, manage_messages=True, kick_members=True, moderate_members=True)
    async def help(
        self,
        interaction: discord.Interaction,
        comando: Union[str,None] = None
    ):
        await interaction.response.defer(ephemeral=True)

        # ---------- AYUDA GENERAL ----------
        if not comando:
            embed = discord.Embed(
                title="Ayuda de Moderación",
                description="Usa `/help <comando>` para ver detalles.\n\n"
                            "**Comandos disponibles:**",
                color=discord.Color.blurple()
            )

            for cmd in HELP_COMMANDS.values():
                embed.add_field(
                    name=f"/{cmd.name}",
                    value=cmd.description,
                    inline=False
                )

            return await interaction.followup.send(embed=embed, ephemeral=True)

        # ---------- AYUDA ESPECÍFICA ----------
        cmd = HELP_COMMANDS.get(comando.lower())
        if not cmd:
            return await interaction.followup.send(
                ":x: Comando no encontrado.",
                ephemeral=True
            )

        embed = discord.Embed(
            title=f":pushpin: /{cmd.name}",
            description=cmd.description,
            color=discord.Color.green()
        )

        embed.add_field(
            name=":zap: Uso",
            value=f"`{cmd.usage}`",
            inline=False
        )

        embed.add_field(
            name=":paperclip: Ejemplos",
            value="\n".join(f"`{e}`" for e in cmd.examples),
            inline=False
        )

        if cmd.notes:
            embed.add_field(
                name=":warning: Notas",
                value=cmd.notes + OPTIONAL_ARGUMENTS_INFO,
                inline=False
            )

        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.guilds(int(GUILD_ID))
    @help.autocomplete("comando")
    async def help_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        return [
            app_commands.Choice(name=cmd, value=cmd)
            for cmd in HELP_COMMANDS.keys()
            if current.lower() in cmd
        ]

async def setup(bot):
    await bot.add_cog(Help(bot))
