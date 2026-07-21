from .base import ConfigSection

class Bots(ConfigSection):
    PREFIX = "USERS_ID.BOTS"

    MUSIC: list[int]
    MODERATION: list[int]

    def __getattr__(self, name:str) -> list[int]:
        return self._get(name)

class Users:
    """Clase para acceder a las IDs de los usuarios (incluye bots) registrados en la DB"""
    def __init__(self, manager) -> None:
        self.bots = Bots(manager)