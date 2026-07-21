from .base import ConfigSection


class ModerationColors(ConfigSection):
    PREFIX = "COLORS.MODERATION"

    # Exponer atributos para que el IDE los pueda mostrar
    BAN: int
    KICK: int
    SOFT_BAN: int
    MUTE: int
    UNBAN: int
    MESSAGE_PURGE: int
    FILTER_MUTE: int
    PRIVATE_MESSAGE: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)
    
class LogColors(ConfigSection):
    PREFIX = "COLORS.LOG"

    # Profile events section
    PROFILE_AVATAR: int
    PROFILE_NAME: int
    PROFILE_DATA: int

    # Server events section
    SERVER_JOIN: int
    SERVER_LEAVE: int

    # Voice channel events section
    VOICE_JON: int
    VOICE_LEAVE: int
    VOICE_CHANGE: int

    # Channel events section
    CHANNEL_CREATE: int
    CHANNEL_EDIT: int
    CHANNEL_DELETE: int

    # Message events section
    MESSAGE_EDIT: int
    MESSAGE_DELETE: int

    # Role events section
    ROLE_EDIT: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class Colors:
    """Clase para acceder a los valores de los colores en la DB"""
    def __init__(self, manager) -> None:
        self.moderation = ModerationColors(manager)
        self.logs = LogColors(manager)