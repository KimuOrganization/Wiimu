from dataclasses import dataclass
from typing import List, Union, Dict

@dataclass
class CommandHelp:
    name: str
    description: str
    usage: str
    examples: List[str]
    notes: Union[str,None] = None

OPTIONAL_ARGUMENTS_INFO = "\n\nLos argumentos **opcionales** tienen valores por defecto. Cada comando tiene valores diferentes."

HELP_COMMANDS: Dict[str, CommandHelp] = {
    "ban": CommandHelp(
        name="ban",
        description="Banea a un usuario del servidor.",
        usage="/ban *usuario *razón borrar_mensajes dias_de_purga mandar_dm",
        examples=[
            "/ban @Usuario Spam",
            "/ban 123456789012345678 Gore true 7 true"
        ],
        notes="Los argumentos **opcionales** tienen valores por defecto. Cada comando tiene valores diferentes."
    ),
    "kick": CommandHelp(
        name="kick",
        description="Expulsa a un usuario del servidor.",
        usage="/kick *usuario *razón mandar_dm",
        examples=[
            "/kick @Usuario Xenofobia",
            "/kick 123456789012345678 Piensa que discord es tinder false"
        ],
        notes="Los argumentos **opcionales** tienen valores por defecto. Cada comando tiene valores diferentes."
    ),
    "mute": CommandHelp(
        name="mute",
        description="Aísla temporalmente a un usuario.",
        usage="/mute *usuario *duración razón mandar_dm",
        examples=[
            "/mute @Usuario 6h30m",
            "/mute 123456789012345678 Insultos false"
        ],
        notes="Formato de duración: 1w2d3h4m5s"
    ),
    "softban": CommandHelp(
        name="softban",
        description="Expulsa a un usuario del servidor.",
        usage="/softban *usuario *razón borrar_mensajes dias_de_purga mandar_dm",
        examples=[
            "/softban @Usuario spamear nword",
            "/softban 123456789012345678 dijo que cherry no es una marca (desinformo) true 1 true"
        ],
        notes="Este comando es util cuando queres echar a un usuario sin negarle la entrada al servidor, ademas de borrar sus mensajes enviados (argumento `dias_de_purga`)"
    ),
    "purgar_mensajes": CommandHelp(
        name="purgar_mensajes",
        description="Cantidad de mensajes a eliminar desde el ultimo enviado en el canal actual.",
        usage="/purgar_mensajes cantidad* razón usuario canal",
        examples=[
            "/purgar_mensajes 75",
            "/purgar_mensajes 3 la razon es treeees",
            "/purgar_mensajes 69 @usuario #arte",
            "/purgar_mensajes 69 12345678912345678",
            "/purgar_mensajes 100 #coding"
        ]
    ),
    "wiimu_mensaje": CommandHelp(
        name="wiimu_mensaje",
        description="Enviar un mensaje desde wiimu al canal actual.",
        usage="/wiimu_mensaje *mensaje",
        examples=[
            "/wiimu_mensaje los voy a banear a todos"
        ]
    )
}
