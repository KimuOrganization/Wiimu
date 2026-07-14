from datetime import timedelta
import re
from typing import List

def format_duration(delta: timedelta) -> str:
    seconds = int(delta.total_seconds())

    months, seconds = divmod(seconds, 30 * 24 * 3600)
    days, seconds = divmod(seconds, 24 * 3600)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)

    parts: List[str] = []

    if months:
        parts.append(f"{months} mes{'es' if months != 1 else ''}")
    if days:
        parts.append(f"{days} día{'s' if days != 1 else ''}")
    if hours:
        parts.append(f"{hours} hora{'s' if hours != 1 else ''}")
    if minutes:
        parts.append(f"{minutes} minuto{'s' if minutes != 1 else ''}")
    if seconds or not parts:
        parts.append(f"{seconds} segundo{'s' if seconds != 1 else ''}")
    
    text = ", ".join(parts)
    if (", ") in text:
        text = " y ".join(text.rsplit(", ", 1))

    return text


DURATION_REGEX = re.compile(
    r"(?:(\d+)w)?"
    r"(?:(\d+)d)?"
    r"(?:(\d+)h)?"
    r"(?:(\d+)m)?"
    r"(?:(\d+)s)?"
)

# Función utilizada para parsear la duración de las
def parse_duration(text: str) -> int:
    match = DURATION_REGEX.fullmatch(text.lower())
    if not match:
        raise ValueError("Formato inválido")

    weeks, days, hours, minutes, seconds = match.groups(default="0")

    total_seconds = (
        int(weeks) * 604800 +
        int(days) * 86400 +
        int(hours) * 3600 +
        int(minutes) * 60 +
        int(seconds)
    )

    if total_seconds <= 0:
        raise ValueError("Duración inválida")

    return total_seconds