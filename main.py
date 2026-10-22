from discord.ext import commands
from core.config import BOT_TOKEN,INTENTS,APP_ID
from core.bot import Bot
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

class ArgentinaFormatter(logging.Formatter):
    def formatTime(self, record, datefmt=None):
        dt = datetime.fromtimestamp(
            record.created,
            tz=ZoneInfo("America/Argentina/Buenos_Aires"),
        )
        return dt.strftime(datefmt) if datefmt else dt.isoformat()



handler = logging.StreamHandler()
handler.setFormatter(
    ArgentinaFormatter(
        fmt="ARG(GMT-3) %(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%d-%m-%Y %H:%M:%S",
    )
)

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.handlers.clear()
root_logger.addHandler(handler)


bot = Bot(
    command_prefix=commands.when_mentioned,
    intents=INTENTS,
    application_id=int(APP_ID)
)

if __name__ == '__main__':
    bot.run(BOT_TOKEN)