import os
from dotenv import load_dotenv
import discord
from typing import Set

# Funcionalidades del bot a habilitar
BOT_FEATURES = ("dev","welcome","moderation","logs","automatic_threads","message_filter","utils","honeypot","community", "word_blacklist")
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

ART_CHANNEL_ID = get_env("ART_CHANNEL_ID")
PROJECTS_CHANNEL_ID = get_env("PROJECTS_CHANNEL_ID")
DESKTOPS_CHANNEL_ID = get_env("DESKTOPS_CHANNEL_ID")

WELCOME_CHANNEL_ID = get_env("WELCOME_CHANNEL_ID")
WELCOME_ROLE_ID = get_env("WELCOME_ROLE_ID")
WELCOME_IMAGE_PATH = get_env("WELCOME_IMAGE_PATH")
WELCOME_CANVAS = {"width":700, "height":247}

LOG_CHANNEL_ID = get_env("LOG_CHANNEL_ID")
STAFF_ROLE_ID = get_env("STAFF_ROLE_ID")
COMMAND_CHANNEL_ID = get_env("COMMAND_CHANNEL_ID")

HONEYPOT_CHANNEL_ID = get_env("HONEYPOT_CHANNEL_ID")

# Opcionales para la lista de canales especiales (pero recomendados)
TTS_LOGS_CHANNEL_ID = 1451176427062820995
MODERATOR_ONLY_CHANNEL_ID = 1084829832950579220

# Canales especiales donde no se van a poder utilizar comandos para purgar mensajes.
SPECIAL_CHANNELS : Set[int] = {
    int(LOG_CHANNEL_ID),int(COMMAND_CHANNEL_ID),
    int(TTS_LOGS_CHANNEL_ID),int(MODERATOR_ONLY_CHANNEL_ID)
}

LOG_BLACKLISTED_BOTS : Set[int] = {945683386100514827}
