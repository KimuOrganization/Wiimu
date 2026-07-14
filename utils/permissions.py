import discord
from typing import NamedTuple, List

def diff_overwrites(before:dict, after:dict) -> List[str]:
    changes = []

    all_targets = set(before.keys()) | set(after.keys())

    for target in all_targets:
        before_ow = before.get(target)
        after_ow = after.get(target)

        target_name = (
            f"@{target.name}" if isinstance(target, discord.Role) else f"{target.name}"
        )

        if before_ow is None and after_ow is not None:
            changes.append(f"➕ **{target_name}**")
            for perm,value in after_ow:
                if value is not None:
                    icon = "✅" if value else "❌"
                    changes.append(f" {icon} `{repr(perm)}`")
            continue

        if before_ow is not None and after_ow is None:
            changes.append(f"➖ **{target_name}**")
            continue

        for perm in discord.Permissions.VALID_FLAGS:
            before_attr = getattr(before_ow, perm)
            after_attr = getattr(after_ow, perm)

            if (before_attr != after_attr):
                b_txt = "✅" if before_attr else "❌" if before_attr is False else "➖"
                a_txt = "✅" if after_attr else "❌" if after_attr is False else "➖"

                changes.append(
                    f"🔁 **{target_name}** `{perm}`: {b_txt} → {a_txt}"
                )
    
    return changes

class PermissionChange(NamedTuple):
    name: str
    before:bool
    after:bool

def diff_permission(before: discord.Permissions, after: discord.Permissions) -> List[PermissionChange]:
    changes: list[PermissionChange] = []

    for perm, before_value in before:
        after_value = getattr(after, perm)

        if before_value != after_value:
            changes.append(
                PermissionChange(
                    name=perm.replace('_', ' ').title(),
                    before=bool(before_value),
                    after=bool(after_value)
                )
            )
    
    return changes
