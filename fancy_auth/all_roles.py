from __future__ import annotations

from fancy_auth.base_role import BaseRole
from fancy_auth.roles import UserIsDog
from fancy_auth.roles import UserMatches

ALL_ROLES: list[type[BaseRole]] = [
    UserIsDog,
    UserMatches,
]
