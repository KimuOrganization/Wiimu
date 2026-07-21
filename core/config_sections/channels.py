from .base import ConfigSection

class AutoThreadableChannels(ConfigSection):
    """IDs de los canales donde se crean los hilos automáticamente"""
    PREFIX = "CHANNELS_ID.SPECIAL"

    ART: int
    DESKTOPS: int
    PROJECTS: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class StaffChannels(ConfigSection):
    """IDs de los canales de moderación (logs, commandos, etc)"""
    PREFIX = "CHANNELS_ID.STAFF"

    LOGS: int
    COMMAND_LOGS: int

    # Opcionales para el funcionamiento del bot
    TTS_LOGS: int
    MODERATOR_ONLY: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class CommonChannels(ConfigSection):
    """IDs de los canales 'varios' que no tienen una categoría en si (el de bienvenida por ejemplo)"""
    PREFIX = "CHANNELS_ID.COMMON"

    WELCOME: int
    HONEYPOT: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)
    
class Channels:
    """Clase para acceder a las IDs de los canales registrados en la DB"""
    def __init__(self, manager) -> None:
        self.auto_threadable = AutoThreadableChannels(manager)
        self.staff = StaffChannels(manager)
        self.common = CommonChannels(manager)