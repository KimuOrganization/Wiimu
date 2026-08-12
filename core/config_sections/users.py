from .base import ConfigSection

class MultiAccounts(ConfigSection):
    PREFIX = "USERS_ID.MULTI_ACCOUNTS"

    GROUPS: list[list[int]]

    def __getattr__(self, name:str)-> list[list[int]]:
        return self._get(name)

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
        self.multi_accounts = MultiAccounts(manager)