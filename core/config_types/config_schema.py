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

def is_multi_account_groups(value: object) -> bool:
    if not isinstance(value,list):
        return False

    seen: set[int] = set()

    for group in value:
        if not isinstance(group, list) or len(group) < 2:
            return False

        if not group:
            return False

        for user_id in group:
            if not isinstance(user_id,int):
                return False
            if user_id in seen:
                return False

            seen.add(user_id)
        
    return True

@dataclass(slots=True)
class SchemaRule:
    pattern:str
    validator: Validator

"""Esquemas especificos primero, despues genericos, para evitar coincidencias erroneas."""
CONFIG_SCHEMA_RULES : list[SchemaRule] = [
    # Users
    SchemaRule("USERS_ID.BOTS.MUSIC", is_list_of_int),
    SchemaRule("USERS_ID.MULTI_ACCOUNTS", is_multi_account_groups),

    # Roles
    SchemaRule("ROLES_ID.INTEGRATION.*", is_list_of_int),
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