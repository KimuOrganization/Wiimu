import discord
import re
from urllib.parse import urlparse
from typing import Set

BANNED_PHRASES : Set[str] = {
    "check my bio", "onlyfans leaked"
}

INVITE_REGEX = re.compile(
        r"(?:https?://)?(?:www\.)?(?:discord\.gg|discord(?:app)?\.com/invite)/([a-zA-Z0-9-]+)",
    re.IGNORECASE
)

URL_REGEX = re.compile(
    r"https?://[^\s]+",
    re.IGNORECASE
)

BLACKLIST_HOSTS = (
    "twitter.com",
    "x.com",
    "tiktok.com",
    "instagram.com",
    "facebook.com",
    "fb.watch",
    "reddit.com",
    "redd.it",
    "twitch.tv",
    "discord.com",
    "discord.gg",
)

def has_attachments(message: discord.Message) -> bool:
    return len(message.attachments) > 0

def has_threadable_link(content: str) -> bool:
    urls = URL_REGEX.findall(content)
    if not urls:
        return False

    for url in urls:
        parsed = urlparse(url)
        host = parsed.netloc.lower()

        # Eliminar subdominio www
        if host.startswith("www."):
            host = host[4:]

        # Bloquear redes sociales
        if host in BLACKLIST_HOSTS:
            return False

    return True

def has_threadable_embed(message: discord.Message) -> bool:
    # Actualmente la LIB no permite ver el contenido de mensajes re-enviados
    # Asi que se va a asumir que un mensaje re-enviado es valido para crear un hilo
    if (message.flags.forwarded):
        return True
    
    return False
