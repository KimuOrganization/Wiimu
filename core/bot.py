import aiohttp
from discord.ext import commands
from core.config import BOT_FEATURES, GUILD_ID
import discord
from typing import Union

class Bot(commands.Bot):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.http_session: Union[aiohttp.ClientSession,None] = None

    async def setup_hook(self):
        if not self.http_session:
            self.http_session = aiohttp.ClientSession()

        # Carga de features del bot
        for cog in BOT_FEATURES:
            await self.load_extension(f"cogs.{cog}")
        
        server = discord.Object(id=int(GUILD_ID))
        await self.tree.sync(guild=server)

    async def close(self):
        if self.http_session:
            await self.http_session.close()
        await super().close()
