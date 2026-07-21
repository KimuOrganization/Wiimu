import re
import unicodedata

BANNED_WORDS = {
    "niger",
    "nigger",
    "niga",
    "nigga",
    "femboy",
    "retard"
}

# Palabras que si son encontradas, no van a interferir con el patron de palabras baneadas
BORDER_WORDS = {
    "nigeria",
    "nigeriana",
    "nigeriano",
    "nigerianas",
    "nigerianos"
}

LEET_MAP = str.maketrans({
    "0":"o",
    "1":"i",
    "2":"z",
    "3":"e",
    "4":"a",
    "5":"s",
    "6":"g",
    "7":"t",
    "8":"b",
    "9":"g",
    "@":"a",
    "$":"s",
    "!":"i",
    "|":"i"
})

def normalize_text(text:str) -> str:
    text = text.lower()

    # Elimina acentos
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))

    text = text.translate(LEET_MAP)

    text = re.sub(r"[^a-z]", "", text)

    return text

def collapse_repeated(text:str) -> str:
    return re.sub(r"(.)\1+", r"\1", text)

def contains_banned_word(text: str) -> bool:
    normalized = collapse_repeated(normalize_text(text))
    cleaned = normalized

    # Quito las palabras que son edge case para evitar detecciones erroneas
    for border in BORDER_WORDS:
        cleaned = cleaned.replace(border,"")

    return any(word in cleaned for word in BANNED_WORDS)
        
