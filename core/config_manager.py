import json
from sys import exception
import discord
from core.config_sections.channels import Channels
from core.config_sections.roles import Roles
from core.config_sections.users import Users
from core.database import Database
from typing import Dict
from core.config_sections.colors import Colors
from core.config_types.config_value import ConfigValue
from core.config_types.config_type import ConfigType
from core.config_types.exceptions import InvalidConfigurationError
from core.config_types.config_schema import get_validator_for_key
import logging

logger = logging.getLogger(__name__)

class ConfigManager:
    def __init__(self, database : Database) -> None:
        self.db = database
        self._configs: Dict[str, ConfigValue] = {}
        self.colors = Colors(self)
        self.users = Users(self)
        self.channels = Channels(self)
        self.roles = Roles(self)
    
    def _validate_schema(self, key:str, value: object) -> None:
        validator = get_validator_for_key(key)
        if validator is None:
            return
        if not validator(value):
            raise TypeError(
                f"El valor de '{key}' no cumple con el schema esperado."
            )

    async def load(self):
        rows = await self.db.fetch_all(
            """
            SELECT key,type,value
            FROM configs
            ORDER BY key
            """
        )

        # Variables axiliares
        configs: Dict[str, ConfigValue] = {}
        errors: list[str] = []

        self._configs.clear()

        for row in rows:
            key = row["key"]
            try:
                config_type = ConfigType(row["type"])

                value = self._deserialize(
                    config_type,
                    row["value"]
                )

                self._validate_schema(key, value)

                configs[key] = ConfigValue(
                    key=key,
                    type=config_type,
                    value=value
                )
            except Exception as ex:
                errors.append(
                    f"{key} ({row['type']}) -> {ex}"
                )

        if errors:
            logger.critical(
                "Se encontraron %d configuraciones inválidas:\n%s",
                len(errors),
                "\n".join(errors)
            )
            raise InvalidConfigurationError(
                "\n".join(errors)
            )

        self._configs = configs

        # DEBUG PURPOSES
        #for conf in configs:
        #    logger.info("Se cargo: %s", conf)
        
        logger.info("Se cargaron %d configuraciones correctamente.", len(configs))

    async def reload(self, key=None):
        # Recarga todas las configuracione
        if not key:
            await self.load()
            logger.info("Configuración recargada correctamente.")
            return
        
        # Recarga la configuración especifica
        row = await self.db.fetch_one(
            """
            SELECT key,type,value
            FROM configs
            WHERE key = ?
            """,
            (key,)
        )
        if row is None:
            raise KeyError(key)
        
        try:
            config_type = ConfigType(row["type"])

            value = self._deserialize(
                config_type,
                row["value"]
            )

            self._validate_schema(key, value)

            self._configs[key] = ConfigValue(
                key=key,
                type=config_type,
                value=value
            )
        except exception as ex:
            logger.error(
                "No se pudo recargar '%s': %s",
                key, ex
            )
            raise InvalidConfigurationError(
                f"{key}: {ex}"
            )

        logger.info("Se recargo la configuración '%s'", key)
        
        return

    async def set(self,key,type,value):
        await self.db.execute(
            """
            INSERT INTO configs(key,type,value)
            VALUES (?,?,?)
            ON CONFLICT(key)
            DO UPDATE SET value=excluded.value
            """,
            (
                key,
                type,
                value
            )
        )
        logger.info("Se actualizo el valor de la configuración '%s'", key)
        await self.reload(key)
    
    def get(self, key:str):
        config = self._configs.get(key)
        if config is None:
            available = ", ".join(sorted(self._configs.keys())[:10])
            raise KeyError(
                f"Configuración '{key}' no encontrada."
                f"Configs cargadas: {len(self._configs)}"
                f"Ejemplos: {available}"
            )

        return config.value

    @staticmethod
    def _deserialize(config_type: ConfigType, value:str):
        match config_type:
            case ConfigType.STRING:
                return value
            case ConfigType.INTEGER:
                return int(value)
            case ConfigType.FLOAT:
                return float(value)
            case ConfigType.BOOLEAN:
                if value.lower() not in ("true", "false", "1", "0"):
                    raise ValueError(
                        "Se esperaba un booleano ('true' o 'false' o '1' o '0')"
                    )
                return value.lower() == "true" or value == "1"
            case ConfigType.COLOR:
                return discord.Color(int(value))
            case ConfigType.JSON:
                return json.loads(value)
        
        raise ValueError(f"Tipo de configuración no soportado: {config_type}")