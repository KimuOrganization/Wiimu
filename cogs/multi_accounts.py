import discord
from discord.ext import commands
from discord import app_commands, Permissions
from core.bot import Bot
from core.config import GUILD_ID
from core.config_manager import ConfigManager

import logging
logger = logging.getLogger(__name__)

MULTI_ACCOUNTS_KEY = "USERS_ID.MULTI_ACCOUNTS.GROUPS"

class MultiAccounts(commands.Cog):
    """Comandos para administrar grupos de multicuentas"""
    def __init__(self, bot: Bot) -> None:
        self.bot = bot

    @property
    def cfg(self) -> ConfigManager:
        return self.bot.config # type: ignore

    def _get_groups(self) -> list[list[int]]:
        """Obtiene los grupos de multicuentas que se encuentran registrados en la DB."""
        groups = self.cfg.get(MULTI_ACCOUNTS_KEY)

        if not isinstance(groups, list):
            raise TypeError(
                f"{MULTI_ACCOUNTS_KEY} no contiene una lista."
            )
        return groups

    @staticmethod
    def _parse_accounts(value: str) -> list[int]:
        """
        Convierte una lista escrita por el usuario en IDs.

        Ejemplo:
            "123,456,789"
        
        También aceptaria:
            "123 567 789"
        """

        value = value.replace(",", " ")
        parts = value.split()

        if not parts:
            raise ValueError(
                "Debes proporcionar al menos una cuenta."
            )

        accounts: list[int] = []

        for part in parts:
            # permitir menciones
            if part.startswith("<@") and part.endswith(">"):
                part = (
                    part.replace("<@", "").replace("!", "").replace(">", "")
                )

            if not part.isdigit():
                raise ValueError(
                    f"`{part}` no es un ID de Discord válido"
                )

            account_id = int(part)

            if account_id <= 0:
                raise ValueError(
                    f"`{part}` no es un ID de Discord válido."
                )

            if account_id not in accounts:
                accounts.append(account_id)

        return accounts

    @staticmethod
    def _find_group(
        groups: list[list[int]],
        account_id: int
    ) -> int | None:
        """
        Devuelve el índice del grupo al que pertenece cada cuenta.

        Devuelve None si no pertenece a ningún grupo.
        """
        for index, group in enumerate(groups):
            if account_id in group:
                return index

        return None

    @staticmethod
    def _format_group(group: list[int]) -> str:
        """Formatea un grupo para mostrarlo en Discord."""
        return "\n".join(
            f"\u2800\u2800`{account_id}`"
            for account_id in group
        )

    @staticmethod
    def _format_groups(groups: list[list[int]]) -> str:
        """Formatea todos los grupos."""

        if not groups:
            return "*No hay grupos registrados.*"

        lines: list[str] = []

        for index,group in enumerate(groups, start=1):
            accounts = ", ".join(
                f"`{account_id}`"
                for account_id in group
            )

            lines.append(
                f"**Grupo {index}:** {accounts}"
            )

        return "\n".join(lines)

    async def _save_groups(self, groups: list[list[int]]) -> None:
        """Guarda los grupos en el ConfigManager."""
        import json
        normalized = json.dumps(
            groups, separators=(",",":")
        )
        await self.cfg.set(
            MULTI_ACCOUNTS_KEY,
            "JSON",
            normalized
        )

    multi_accounts_group = app_commands.Group(
        name="multi_accounts",
        description="Administración de multicuentas.",
        guild_only=True,
        guild_ids=[int(GUILD_ID)],
        default_permissions=Permissions(administrator=True)
    )

    #region Add Group command
    @multi_accounts_group.command(
        name="add_group",
        description="Crea un nuevo grupo de multicuentas"
    )
    @app_commands.describe(
        accounts=(
            "IDs, menciones o usuarios separados por comas. "
            "Ej: 123,456,789"
        )
    )
    async def add_group(self, interaction: discord.Interaction, accounts:str):
        try:
            accounts_list : list[int] = self._parse_accounts(accounts)

            if len(accounts_list) < 2:
                return await interaction.response.send_message(
                    "Un grupo debe contener al menos **2 cuentas**.",
                    ephemeral=True
                )

            groups = self._get_groups()

            # Verificar que ninguna cuenta pertenezca a otro grupo
            existing: list[int] = []

            for account_id in accounts_list:
                group_index = self._find_group(groups, account_id)

                if group_index is not None:
                    existing.append(account_id)

            if existing:
                existing_text = ", ".join(
                    f"`{account_id}`"
                    for account_id in existing
                )

                return await interaction.response.send_message(
                    "Las siguientes cuentas ya pertenecen a un grupo:\n"
                    f"{existing_text}",
                    ephemeral=True
                )

            groups.append(accounts_list)

            await self._save_groups(groups)

            return await interaction.response.send_message(
                "### Grupo de multicuentas creado\n"
                f"{self._format_group(accounts_list)}",
                ephemeral=True
            )
        
        except ValueError as ex:
            return await interaction.response.send_message(
                f"❌ {ex}",
                ephemeral=True
            )

        except Exception:
            logger.exception(
                "Error al crear un grupo de multicuentas."
            )
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    #endregion

    #region Remove Group Command
    @multi_accounts_group.command(
        name="remove_group",
        description="Elimina un grupo completo de multicuentas"
    )
    @app_commands.describe(
        account="Una cuenta perteneciente al grupo que deseas eliminar."
    )
    async def remove_group(self, interaction: discord.Interaction, account:str):
        try:
            accounts = self._parse_accounts(account)

            if len(accounts) != 1:
                return await interaction.response.send_message(
                    "Debes proporcionar **una sola cuenta** "
                    "perteneciente al grupo.",
                    ephemeral=True
                )

            account_id = accounts[0]

            groups = self._get_groups()

            group_index = self._find_group(groups,account_id)

            if group_index is None:
                return await interaction.response.send_message(
                    f"`{account_id}` no pertenece a ningún grupo.",
                    ephemeral=True
                )

            group = groups[group_index]

            # Eliminamos el grupo entero.
            groups.pop(group_index)

            await self._save_groups(groups)

            return await interaction.response.send_message(
                "### Grupo eliminado\n"
                f"{self._format_group(group)}",
                ephemeral=True
            )
        except ValueError as ex:
            return await interaction.response.send_message(
                f"❌ {ex}",
                ephemeral= True
            )
        except Exception:
            logger.exception(
                "Error al eliminar un grupo de multicuentas."
            )
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    #endregion

    #region Add Account to Group Command
    @multi_accounts_group.command(
        name="add",
        description="Agrega una cuenta a un grupo de multicuentas existente."
    )
    @app_commands.describe(
        group="Cuenta que pertenece a un grupo de multicuentas.",
        account="Cuenta que deseas agregar al grupo de multicuentas."
    )
    async def add_account(self, interaction:discord.Interaction, group:str, account:str):
        try:
            group_accounts = self._parse_accounts(group)
            new_accounts = self._parse_accounts(account)

            if len(group_accounts) != 1:
                return await interaction.response.send_message(
                    "El parámetro `group` debe contener una sola cuenta.",
                    ephemeral=True
                )

            if len(new_accounts) != 1:
                return await interaction.response.send_message(
                    "El parámetro `account` debe contener una sola cuenta.",
                    ephemeral=True
                )

            group_account = group_accounts[0]
            new_account = new_accounts[0]

            groups = self._get_groups()

            group_index = self._find_group(groups, group_account)

            if group_index is None:
                return await interaction.response.send_message(
                    f"`{group_account}` no pertenece a ningún grupo.",
                    ephemeral=True
                )

            existing_group = self._find_group(groups, new_account)

            if existing_group is not None:
                return await interaction.response.send_message(
                    f"`{new_account}` ya pertenece al "
                    f"grupo {existing_group + 1}.",
                    ephemeral=True
                )

            groups[group_index].append(new_account)

            await self._save_groups(groups)

            return await interaction.response.send_message(
                f"✅ `{new_account}` fue agregada al grupo.\n\n"
                f"{self._format_group(groups[group_index])}",
                ephemeral=True
            )
        except ValueError as ex:
            return await interaction.response.send_message(
                f"❌ {ex}",
                ephemeral=True
            )
        except Exception:
            logger.exception(
                "Ha ocurrido un error al agregar una cuenta a un grupo."
            )
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    #endregion

    #region Remove Account of Group Command
    @multi_accounts_group.command(
        name="remove",
        description="Elimina una cuenta de su grupo."
    )
    @app_commands.describe(
        account="Cuenta que deseas eliminar de un grupo."
    )
    async def remove_account(self, interaction:discord.Interaction, account:str):
        try:
            accounts = self._parse_accounts(account)

            if len(accounts) != 1:
                return await interaction.response.send_message(
                    "Desbes proporcionar una sola cuenta.",
                    ephemeral=True
                )

            account_id = accounts[0]

            groups = self._get_groups()

            group_index = self._find_group(
                groups, account_id
            )

            if group_index is None:
                return await interaction.response.send_message(
                    f"`{account_id}` no pertenece a ningún grupo.",
                    ephemeral=True
                )

            group = groups[group_index]

            group.remove(account_id)

            # Eliminar grupo si solo queda una cuenta
            if len(group) < 2:
                groups.pop(group_index)

                await self._save_groups(groups)

                return await interaction.response.send_message(
                    f"`{account_id}` fue eliminado.\n"
                    "El grupo tenía solamente dos cuentas, "
                    "por lo que el grupo completo fue eliminado.",
                    ephemeral=True
                )
            
            await self._save_groups(groups)

            return await interaction.response.send_message(
                f"✅ `{account_id}` fue eliminado del grupo.\n\n"
                f"{self._format_group(group)}",
                ephemeral=True
            )
        except ValueError as ex:
            return await interaction.response.send_message(
                f"❌ {ex}",
                ephemeral=True
            )
        except Exception:
            logger.exception(
                "Ha ocurrido un error al eliminar una cuenta de un grupo"
            )
            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    #endregion

    #region List all Groups command
    @multi_accounts_group.command(
        name="list",
        description="Muestra todos los grupos de multicuentas."
    )
    async def list_groups(self, interaction: discord.Interaction):
        try:
            groups = self._get_groups()

            text = self._format_groups(groups)
            
            if len(text) <= 2000:
                return await interaction.response.send_message(
                    text, ephemeral=True
                )

            #TODO: Implementar fragmentación de mensajes, para contenido muy largo
            embed = discord.Embed(
                title="Grupos de multicuentas",
                description=text[:4096],
                color=self.cfg.colors.logs.VOICE_JOIN
            )

            return await interaction.response.send_message(
                embed=embed,
                ephemeral=True
            )
        except Exception:
            logger.exception(
                "Ha ocurrido un error al listar todos los grupos de multicuentas"
            )

            return await interaction.response.send_message(
                "Ha ocurrido un error :( revisar logs.",
                ephemeral=True
            )
    #endregion

async def setup(bot: Bot):
    await bot.add_cog(MultiAccounts(bot))