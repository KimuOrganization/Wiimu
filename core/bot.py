import logging
import aiohttp
from discord.ext import commands
from core.cache import Cache
from core.config import BOT_FEATURES, GUILD_ID
import discord
from typing import Union

from core.config_manager import ConfigManager
from core.database import Database

logger = logging.getLogger(__name__)

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_session: Union[aiohttp.ClientSession,None] = None
        self.database: Database = Database()
        self.config : Union[ConfigManager, None] = None
        self.cache : Union[Cache, None] = None

    async def load_config(self):
        await self.database.connect()
        self.config = ConfigManager(
            self.database
        )
        await self.config.load()

    async def setup_hook(self):
        # Conexión a DB y carga de configs
        await self.load_config()

        # Inicialición del cache
        self.cache = Cache()


        if not self.http_session:
            self.http_session = aiohttp.ClientSession()
            logger.info("Sesión HTTP creada correctamente.")

        # Carga de features del bot
        for cog in BOT_FEATURES:
            try:
                await self.load_extension(f"cogs.{cog}")
                logger.info("Cog '%s' cargado correctamente.", cog)
            except Exception:
                logger.exception("Error cargando el cog '%s'.", cog)
        
        server = discord.Object(id=int(GUILD_ID))
        try:
            commands = await self.tree.sync(guild=server)
            logger.info(
                "Se sincronizaron %d comandos para el servidor %s.",
                len(commands),
                GUILD_ID
            )
        except Exception:
            logger.exception("No se pudieron sincronizar los comandos.")
            raise

    async def close(self):
        logger.info("Apagando bot...")

        if self.http_session:
            await self.http_session.close()
            logger.info("Sesión HTTP cerrada.")

        await super().close()
        logger.info("Bot apagado correctamente.")

