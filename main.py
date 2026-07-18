from discord.ext import commands
from core.config import BOT_TOKEN,INTENTS,APP_ID
from core.bot import Bot
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

bot = Bot(
    command_prefix=commands.when_mentioned,
    intents=INTENTS,
    application_id=int(APP_ID)
)

if __name__ == '__main__':
    bot.run(BOT_TOKEN)