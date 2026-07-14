import discord
from discord.ext import commands
from discord import app_commands
from core.config import BOT_FEATURES, BOT_ENABLED_FEATURES, BOT_DISABLED_FEATURES, GUILD_ID

class Dev(commands.Cog):
    def __init__(self,bot):
        self.bot = bot

    async def enabled_cogs_autocomplete(
            self,
            interaction: discord.Interaction,
            current:str
        ):
        results = []
        
        for cog in BOT_ENABLED_FEATURES:
            if current.lower() in cog.lower():
                results.append(
                    app_commands.Choice(
                        name=cog,
                        value=cog
                    )
                )
        return results [:25]

    async def disabled_cogs_autocomplete(self, interaction: discord.Interaction, current:str):
        results = []
        for cog in BOT_DISABLED_FEATURES:
            if current.lower() in cog.lower():
                results.append(
                    app_commands.Choice(
                        name=cog,
                        value=cog
                    )
                )
        return results [:25]

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="dev_reload_cog",
        description="Recarga una feature específica."
    )
    @app_commands.autocomplete(cog=enabled_cogs_autocomplete)
    @app_commands.default_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    @app_commands.checks.has_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    async def reload_cog(self, interaction: discord.Interaction, cog:str):
        await interaction.response.defer(ephemeral=True)
        if cog not in BOT_FEATURES:
            return await interaction.followup.send(
                "Ese cog no existe, o no esta registrado. Ver 'core/config.py [BOT_FEATURES]'"
            )
        if cog not in BOT_ENABLED_FEATURES:
            return await interaction.followupend(
                "Ese cog no se encuentra habilitado. (Habilitalo si queres recargarlo no? friki)"
            )
        try:
            await self.bot.reload_extension("cogs.{0}".format(cog))
            await interaction.followup.send("Cog recargado correctamente: `{0}`".format(cog))
        except commands.ExtensionNotLoaded:
            try:
                await self.bot.load_extension("cogs.{0}".format(cog))
                return await interaction.followup.send("Cog cargado correctamente: `{0}`".format(cog))
            except Exception as e:
                return await interaction.followup.send("Error al cargar `0`:\n```{1}```".format(cog,e))
        except Exception as e:
            return await interaction.followup.send("Error al recargar `{0}`:\n```{1}```".format(cog,e))
    
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="dev_reload_all_cogs",
        description="Recarga todas las features del bot."
    )
    @app_commands.default_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    @app_commands.checks.has_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    async def reload_all_cogs(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        ok = []
        failed = []
        for cog in BOT_ENABLED_FEATURES:
            try:
                try:
                    await self.bot.reload_extension(
                        "cogs.{0}".format(cog)
                    )
                except commands.ExtensionNotLoaded:
                    await self.bot.load_extension(
                        "cogs.{0}".format(cog)
                    )
                ok.append(cog)
            except Exception as e:
                failed.append("{0}: {1}".format(cog,e))
                BOT_DISABLED_FEATURES.add(cog)
        msg = ""

        if ok:
            msg += "Recargados:\n"
            msg += "\n".join(
                ["• {0}".format(x) for x in ok]
            )
        if failed:
            msg += "\n\nErrores:\n"
            msg += "\n".join(
                ["• {0}".format(x) for x in failed]
            )
        return await interaction.followup.send(msg)

    #pendiente agregar funciones para agregar y deshabilitar modulos
    
    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command( 
        name="dev_enable_cog",
        description="Habilita una feature específica del bot."
    )
    @app_commands.autocomplete(cog=disabled_cogs_autocomplete)
    @app_commands.default_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    @app_commands.checks.has_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    async def enable_cog(self, interaction: discord.Interaction, cog:str):
        await interaction.response.defer(ephemeral=True)

        if cog not in BOT_FEATURES:
            return await interaction.followup.send(
                "Ese cog no existe, o no esta registrado. Ver 'core/config.py [BOT_FEATURES]'"
            )
        if cog not in BOT_DISABLED_FEATURES:
            return await interaction.followup.send(
                "Ese cog ya se encuentra habiitado.."
            )
        try:
            await self.bot.load_extension(
                "cogs.{0}".format(cog)
            )
            BOT_DISABLED_FEATURES.discard(cog)
            BOT_ENABLED_FEATURES.add(cog)

            return await interaction.followup.send(
                "Cog habilitado correctamente: `{0}`".format(cog)
            )
        except Exception as e:
            return await interaction.followup.send(
                "Error al habilitar `{0}`:\n```{1}```".format(cog,e)
            )

    @app_commands.guilds(int(GUILD_ID))
    @app_commands.command(
        name="dev_disable_cog",
        description="Deshabilita una feature específica del bot."
    )
    @app_commands.autocomplete(cog=enabled_cogs_autocomplete) 
    @app_commands.default_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True) 
    @app_commands.checks.has_permissions(manage_messages=True, kick_members=True, ban_members=True, moderate_members=True)
    async def disable_cog(self, interaction:discord.Interaction, cog:str):
        await interaction.response.defer(ephemeral=True)

        if cog not in BOT_FEATURES:
            return await interaction.followup.send(
                "Ese cog no existe o no esta registrado. Ver 'core/config.py [BOT_FEATURES]'"
            )
        if cog == "dev":
            return await interaction.followup.send(
                "Este modulo no es deshabilitable por comandos."
            )
        if cog not in BOT_ENABLED_FEATURES:
            return await interaction.followup.send(
                "Ese cog ya se encuentra deshabilitado."
            )
        try:
            await self.bot.unload_extension(
                "cogs.{0}".format(cog)
            )
            BOT_ENABLED_FEATURES.discard(cog)
            BOT_DISABLED_FEATURES.add(cog)
            return await interaction.followup.send(
                "Cog habilitado correctamente: `{0}`".format(cog)
            )
        except Exception as e:
            return await interaction.followup.send(
                "Error al deshabilitar `{0}`:\n```{1}```".format(cog,e)
            )


async def setup(bot):
    await bot.add_cog(Dev(bot))
