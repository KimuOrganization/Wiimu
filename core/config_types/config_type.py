# Tener en cuenta que StrEnum se implemento a partir de python 3.11, para versiones inferiores a esa, hay que instalar una lib de pip, que agrega StrEnum a versiones mas viejas
from enum import StrEnum

class ConfigType(StrEnum):
    STRING = "STRING"
    INTEGER = "INTEGER"
    BOOLEAN = "BOOLEAN"
    FLOAT = "FLOAT"
    COLOR = "COLOR"
    JSON = "JSON"