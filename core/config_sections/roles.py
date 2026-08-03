from .base import ConfigSection

class StaffRoles(ConfigSection):
    """IDs de los roles que pertenecen al staff o tienen permisos de moderación"""
    PREFIX = "ROLES_ID"

    MODERATORS: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class CommonRoles(ConfigSection):
    """IDs de los roles 'varios' que no tienen una categoría en si (el de bienvenida por ejemplo)"""
    PREFIX = "ROLES_ID"

    WELCOME: int

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class IntegrationRoles(ConfigSection):
    """IDs de los roles de integración (ej: miembros yt, miembros kofi, boosters, etc). Tener en cuenta que generalmente van a ser listas de IDs por el hecho de que una integración puede tener mas de un rol."""
    PREFIX = "ROLES_ID.INTEGRATION"

    KOFI_MEMBER: list[int]
    SERVER_BOOSTER: list[int]
    YOUTUBE_MEMBER: list[int]

    def __getattr__(self, name:str) -> int:
        return self._get(name)

class Roles:
    """Clase para acceder a las IDs de los roles registrados en la DB"""
    def __init__(self, manager) -> None:
        self.staff = StaffRoles(manager)
        self.common = CommonRoles(manager)
        self.integration = IntegrationRoles(manager)