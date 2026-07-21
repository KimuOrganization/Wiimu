import os
from dotenv import load_dotenv
import discord
from typing import Set

# Funcionalidades del bot a habilitar
BOT_FEATURES = ("dev","settings","welcome","moderation","logs","automatic_threads","message_filter","utils","honeypot","community", "word_blacklist")
BOT_ENABLED_FEATURES : Set[str] = set(BOT_FEATURES)
BOT_DISABLED_FEATURES : Set[str] = set()

# Función para cargar las variables de entorno y evitar variables nulas
def get_env(name: str) -> str:
    value = os.getenv(name)
    if (value is None or not value.strip()):
        raise RuntimeError(f"ERROR(ENV): Falta la variable de entorno {name}.")
    return value

# Defino un intents vacio para solo traer lo necesario
INTENTS = discord.Intents.none()
# Gestionar servidor
INTENTS.guilds = True
# Gestionar miembros
INTENTS.members = True
# Gestionar mensajes
INTENTS.messages = True
# Ver el contenido de los mensajes (logging)
INTENTS.message_content = True
# Observar estados de voice chats
INTENTS.voice_states = True
# Observar baneos/desbaneos
INTENTS.moderation = True

load_dotenv()
BOT_TOKEN = get_env("BOT_TOKEN")
APP_ID = get_env("APPLICATION_ID")
GUILD_ID = get_env("GUILD_ID")
DATABASE_PATH = get_env("DATABASE_PATH")
WELCOME_IMAGE_PATH = "assets/welcome.jpg"
WELCOME_CANVAS = {"width":700, "height":247}
