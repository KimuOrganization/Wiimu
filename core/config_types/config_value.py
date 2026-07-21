from dataclasses import dataclass

from core.config_types.config_type import ConfigType

@dataclass(slots=True)
class ConfigValue:
    key: str
    type: ConfigType
    value: object