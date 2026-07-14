from discord.ext import commands
from core.config import BOT_TOKEN,INTENTS,APP_ID
from core.bot import Bot

bot = Bot(
    command_prefix=commands.when_mentioned,
    intents=INTENTS,
    application_id=int(APP_ID)
)

if __name__ == '__main__':
    bot.run(BOT_TOKEN)