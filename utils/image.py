from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from pathlib import Path
from aiohttp import ClientSession
from typing import Tuple

BASE_DIR = Path(__file__).resolve().parent.parent
FONT_PATH = BASE_DIR / "assets" / "fonts" / "ProFontWindows.ttf"
font_big = ImageFont.truetype(str(FONT_PATH), 53)
font_small = ImageFont.truetype(str(FONT_PATH), 24)

async def create_welcome_image(
    session: ClientSession,
    background_path : str,
    avatar_url: str,
    display_name: str,
    username: str,
    size: Tuple[int,int]
) -> BytesIO:
    base = Image.open(background_path).convert("RGBA")
    base = base.resize(size)

    async with session.get(avatar_url) as resp:
        avatar_bytes = await resp.read()

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGBA")
    avatar = avatar.resize((186,186))

    base.paste(avatar, (20,40), avatar)

    draw = ImageDraw.Draw(base)

    draw.text((224,42), display_name, font=font_big, fill=(0,0,0))
    bbox = draw.textbbox((224,42), username, font=font_big)
    text_height = bbox[3] - bbox[1]
    draw.text((224,42 + text_height + 8), username, font=font_small, fill=(0,0,0))

    buffer = BytesIO()
    base.save(buffer, format="PNG")
    buffer.seek(0)

    return buffer