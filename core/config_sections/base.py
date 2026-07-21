from typing import Any
class ConfigSection:
    PREFIX = ""

    # Autocompletado
    __slots__ = ("_manager",)

    def __init__(self, manager):
        self._manager = manager

    def _get(self, key:str) -> Any:
        return self._manager.get(f"{self.PREFIX}.{key}")