from typing import Any, Callable
from dataclasses import dataclass
import fnmatch

Validator = Callable[[Any], bool]

def is_list_of_int(value: Any) -> bool:
    return(
        isinstance(value, list) and
        all(isinstance(x, int) for x in value)
    )

def is_list_of_str(value: Any) -> bool:
    return(
        isinstance(value, list) and
        all(isinstance(x,str) for x in value)
    )

def is_discord_id(value: Any) -> bool:
    return(
        isinstance(value, int)
        and value > 0
        and len(str(value)) >= 17
    )

@dataclass(slots=True)
class SchemaRule:
    pattern:str
    validator: Validator

"""Esquemas especificos primero, despues genericos, para evitar coincidencias erroneas."""
CONFIG_SCHEMA_RULES : list[SchemaRule] = [
    # Users
    SchemaRule("USERS_ID.BOTS.MUSIC", is_list_of_int),

    # Roles
    SchemaRule("ROLES_ID.*", is_discord_id),

    # Channels
    SchemaRule("CHANNELS_ID.STAFF.*", is_discord_id),
    SchemaRule("CHANNELS_ID.SPECIAL.*", is_discord_id),
    SchemaRule("CHANNELS_ID.COMMON.*", is_discord_id),
]

def get_validator_for_key(key:str) -> Validator | None:
    for rule in CONFIG_SCHEMA_RULES:
        if fnmatch.fnmatch(key, rule.pattern):
            return rule.validator
    return None