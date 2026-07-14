import discord
from datetime import datetime, timedelta, timezone
from typing import Union

async def resolve_user(
        interaction: discord.Interaction,
        user: Union[discord.User,discord.Member,None],
        user_id: Union[str,None] = None
) -> Union[discord.User,discord.Member,None]:
    if (user):
        return user
    
    if user_id:
        try:
            return await interaction.client.fetch_user(int(user_id))
        except:
            return None
    
    return None

async def purge_user_messages(
        guild: discord.Guild,
        user: Union[discord.User,discord.Member],
        days: int
    ):
    if (days <= 0):
        return
    
    after = datetime.now(timezone.utc) - timedelta(days=days)

    for channel in guild.text_channels:
        try:
            await channel.purge(
                limit=None,
                after=after,
                check=lambda m: m.author.id == user.id
            )
        except (discord.Forbidden, discord.HTTPException):
            continue