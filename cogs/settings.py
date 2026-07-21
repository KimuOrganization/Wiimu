from __future__ import annotations
import json
from typing import Any, Union
from enum import StrEnum

import discord
from discord.ext import commands
from discord import Forbidden, HTTPException, Permissions, app_commands

from core.bot import Bot
from core.database import Database
from core.config import GUILD_ID
from core.config_manager import ConfigManager
from core.config_types.config_type import ConfigType

import logging
logger = logging.getLogger(__name__)


class JsonListOperation(StrEnum):
    ADD = "ADD"
    REMOVE = "REMOVE"



class Settings(commands.Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    #region Properties
    @property
    def database(self) -> Database:
        return self.bot.database
    
    @property
    def cfg(self) -> ConfigManager | None:
        return self.bot.config

    #region Utility funcs
    async def _log_config_manager_not_exists(self, interaction: discord.Interaction) -> discord.InteractionCallbackResponse[discord.Client]:
        logger.critical("No se pudo obtener el objeto ConfigManager.")
        return await interaction.response.send_message(
            "Ha ocurrido un error :( revisar logs.",
            ephemeral=True
        )
        
    async def _log_config_not_exists(self, interaction: discord.Interaction):
        return await interaction.response.send_message(
            "La configuración no existe.",
            ephemeral=True,
        )
    
    async def _log_config_type_not_json(self, interaction: discord.Interaction):
        return await interaction.response.send_message(
                "Esta configuración no es de tipo JSON.",
                ephemeral=True
            )

    def _all_keys(self) -> list[str]:
        """Devuelve todas las keys de configuración de la DB"""
        return sorted(self.cfg._configs.keys()) # type: ignore
    
    def _list_keys(self) -> list[str]:
        """Devuelve solo las keys de configuración de tipo JSON/Lista de la db"""
        return sorted(
            key
            for key, value in self.cfg._configs.items() # type: ignore
            if value.type == ConfigType.JSON
        )
    
    def _get_config_type(self, key:str) -> ConfigType:
        return self.cfg._configs[key].type # type: ignore

    def _parse_list_item(self, value: str) -> Any:
        value = value.strip()

        # IDs de discord
        if value.isdigit():
            return int(value)

        return value

    def _parse_input(self, config_type: ConfigType, raw_value: str) -> str:
        raw_value = raw_value.strip()

        match config_type:
            case ConfigType.COLOR:
                # #FFFFFF -> FFFFFF
                if raw_value.startswith("#"):
                    raw_value = raw_value[1:]

                # 0xFFFFFF -> FFFFFF
                if raw_value.lower().startswith("0x"):
                    raw_value = raw_value[2:]

                try:
                    value = int(raw_value, 16)
                except ValueError:
                    raise ValueError(
                        "Color inválido. Utiliza #RRGGBB, 0xRRGGBB o RRGGBB."
                    )
                
                return str(value)
            
            case ConfigType.BOOLEAN:
                value = raw_value.lower()
                if value in ("true","1"):
                    return "true"
                if value in ("false", "0"):
                    return "false"
                
                raise ValueError("Booleano inválido. Utiliza true/false.")
            
            case _:
                return raw_value
            
    async def _modify_json_list(
        self, interaction: discord.Interaction, key: str, value: str, operation: JsonListOperation
        ):
        if self.cfg is None:
            return await self._log_config_manager_not_exists(interaction)

        if key not in self.cfg._configs:
            return await self._log_config_not_exists(interaction)
        
        if self._get_config_type(key) != ConfigType.JSON:
            return await self._log_config_type_not_json(interaction)
        
        try:
            current = self.cfg.get(key)
            if not isinstance(current, list):
                return await interaction.response.send_message(
                    "La configuración no es una lista JSON",ephemeral=True
                )
            
            item = self._parse_list_item(value)

            # Trabajar sobre una copia para no mutar el cache directamente
            new_list = list(current)

            match operation:
                case JsonListOperation.ADD:
                    if item in new_list:
                        return await interaction.response.send_message(
                            "El elemento ya existe en la lista.",
                            ephemeral=True
                        )
                    new_list.append(item)
                    success_message = (
                        f"Elemento agregado a `{key}`: `{item}`"
                    )

                case JsonListOperation.REMOVE:
                    if item not in new_list:
                        return await interaction.response.send_message(
                            "El elemento no existe en la lista.",
                            ephemeral=True
                        )
                    new_list.remove(item)
                    success_message = (
                        f"Elemento eliminado de `{key}`: `{item}`"
                    )
                
                case _:
                    raise ValueError(operation)
                
            self.cfg._validate_schema(key, new_list)

            normalized = json.dumps(new_list, separators=(",", ":"))

            await self.cfg.set(key, ConfigType.JSON, normalized)
            return await interaction.response.send_message(
                success_message, ephemeral=True
            )
        except Exception:
            logger.exception(
                "Excepción no controlada al modificar la configuración JSON '%s' (%s)",
                key, operation.value
            )
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )


        
        
            
    #region Autocomplete funcs
    async def autocomplete_all_keys(
            self, interaction:discord.Interaction, current:str
        ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=key, value=key)
            for key in self._all_keys()
            if current.lower() in key.lower()
        ][:25]
    
    async def autocomplete_list_keys(
        self, interaction:discord.Interaction, current:str
        ) -> list[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=key, value=key)
            for key in self._list_keys()
            if current.lower() in key.lower()
        ][:25]
    
    async def autocomplete_list_values(
        self, interaction: discord.Interaction, current:str
        ) -> list[app_commands.Choice[str]]:
        if self.cfg is None:
            logger.critical("No se pudo obtener el objeto ConfigManager.")
            return []

        # Referencia al argumento key del comando que implementa este autocomplete
        key = getattr(interaction.namespace, "key", None)
        if not key:
            return []
        
        # Verificar que la key sea valida
        if key not in self.cfg._configs:
            return []
        
        # Obtener el valor actual desde el cache del ConfigManager
        values = self.cfg.get(key)

        # Solo listas
        if not isinstance(values, list):
            return []
        
        choices: list[app_commands.Choice[str]] = []

        for item in values:
            item_str = str(item)

            # Filtrado continuo
            if current.lower() in item_str.lower():
                choices.append(
                    app_commands.Choice(
                        name=item_str,
                        value=item_str
                    )
                )

        return choices [:25]    
    
    #region Command group
    config_group = app_commands.Group(
        name="config",
        description="Administra la configuración del bot",
        guild_only=True,
        guild_ids=[int(GUILD_ID)],
        default_permissions=Permissions(administrator=True)
    )   

    #region List configs command
    @config_group.command(name="list", description="Muestra todas las configuraciones disponibles")
    async def cmd_config_list(self, interaction:discord.Interaction, drop_in_dm: bool = False):
        keys = self._all_keys()
        content = "\n".join(f"* `{key}`" for key in keys)

        if len(content) > 1900:
            chunks = [
                content[i:i + 1900]
                for i in range(0, len(content), 1900)
            ]

            if drop_in_dm:
                try:
                    await interaction.user.send(
                        chunks[0]
                    )
                    for chunk in chunks[1:]:
                        await interaction.user.send(
                            chunk
                        )
                except Forbidden:
                    return await interaction.response.send_message("Parece que no tengo los permisos adecuados para enviar este mensaje :(",ephemeral=True)
                except HTTPException:
                    return await interaction.response.send_message("Ocurrio un error al enviar el mensaje :(",ephemeral=True)
            else:
                await interaction.response.send_message(chunks[0], ephemeral=True)
                for chunk in chunks[1:]:
                    await interaction.followup.send(chunk, ephemeral=True)

            return

        if drop_in_dm:
            try:
                return await interaction.user.send(content)
            except Forbidden:
                return await interaction.response.send_message("Parece que no tengo los permisos adecuados para enviar este mensaje :(",ephemeral=True)
            except HTTPException:
                return await interaction.response.send_message("Ocurrio un error al enviar el mensaje :(",ephemeral=True)
            

        return await interaction.response.send_message(content, ephemeral=True)

    #region Edit config command
    @config_group.command(name="edit", description="Edita una configuración existente")
    @app_commands.autocomplete(key=autocomplete_all_keys)
    async def cmd_config_edit(self, interaction: discord.Interaction, key:str, value:str) -> discord.InteractionCallbackResponse[discord.Client]:
        if self.cfg is None:
            return await self._log_config_manager_not_exists(interaction)

        if key not in self.cfg._configs:
            return await self._log_config_not_exists(interaction)
        
        config_type = self._get_config_type(key)

        # Evitar que se configuren JSONs con este comando
        if config_type == ConfigType.JSON:
            return await interaction.response.send_message(
                "Las configuraciones JSON deben editarse con `/config json`.",
                ephemeral=True
            )
        
        try:
            parsed_value = self._parse_input(config_type, value)

            # Validación del valor
            deserialized = self.cfg._deserialize(config_type, parsed_value)
            self.cfg._validate_schema(key, deserialized)

            await self.cfg.set(key,config_type,parsed_value)
            return await interaction.response.send_message(
                f"Configuración actualizada.\n\n`{key}` = `{value}`",
                ephemeral=True
            )
        except ValueError as vex:
            return await interaction.response.send_message(vex, ephemeral=True)
        except Exception:
            logger.exception("Excepción no controlada al actualizar una configuración de tipo %s", config_type)
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    
    #region JSON config command
    @config_group.command(name="json", description="Reemplaza completamente un valor JSON")
    @app_commands.autocomplete(key=autocomplete_list_keys)
    async def cmd_config_json(
        self, interaction: discord.Interaction, key: str, value: str
        ) -> discord.InteractionCallbackResponse[discord.Client]:
        if self.cfg is None:
            return await self._log_config_manager_not_exists(interaction)

        if key not in self.cfg._configs:
            return await self._log_config_not_exists(interaction)
        
        if self._get_config_type(key) != ConfigType.JSON:
            return await self._log_config_type_not_json(interaction)
        
        try:
            parsed = json.loads(value)

            # Validar schema
            self.cfg._validate_schema(key,parsed)

            normalized = json.dumps(parsed, separators=(",", ":"))

            await self.cfg.set(key, ConfigType.JSON, normalized)
            return await interaction.response.send_message(
                f"JSON actualizado para `{key}`.",
                ephemeral=True
            )
        except json.JSONDecodeError as ex:
            return await interaction.response.send_message(
                f"JSON invalido: `{ex}`",
                ephemeral=True
            )
        except Exception:
            logger.exception("Excepción no controlada al actualizar una configuración de tipo JSON.")
            return await interaction.response.send_message(
                f"Ha ocurrido un error :( revisar logs."
            )
        
    #region Add Item config command
    @config_group.command(name="add_item", description="Agrega un elemento a una configuración del tipo Lista/JSON")
    @app_commands.autocomplete(key=autocomplete_list_keys)
    async def cmd_config_add(
        self, interaction: discord.Interaction, key: str, value: str
        ) -> discord.InteractionCallbackResponse[discord.Client]:
        return await self._modify_json_list(
            interaction,
            key,
            value,
            JsonListOperation.ADD
        )
    
    #region Remove Item config command
    @config_group.command(name="remove_item", description="Elimina un elemento a una configuración del tipo Lista/JSON")
    @app_commands.autocomplete(key=autocomplete_list_keys, value=autocomplete_list_values)
    async def cmd_config_remove_item(
        self, interaction: discord.Interaction, key:str, value:str
        ) -> discord.InteractionCallbackResponse[discord.Client]:
        return await self._modify_json_list(
            interaction,
            key,
            value,
            JsonListOperation.REMOVE
        )
        
async def setup(bot: Bot):
    await bot.add_cog(Settings(bot))



        
        


            
        






                



    

