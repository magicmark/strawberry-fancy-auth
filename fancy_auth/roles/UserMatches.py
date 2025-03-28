from __future__ import annotations

from typing import Any

from fancy_auth.context import Context
from fancy_auth.base_role import BaseRole


class UserMatches(BaseRole):
    """
    Validates that the logged-in user making the query matches the user who owns the protected type/field.
    """

    role_owner = "My Team Name"
    comparison_key = "fancy_auth_user_owner_id"
    possible_scopes = None  # this role does not accept any scopes

    def is_role_valid(
        self, scopes: set[str] | None, source: Any, context: Context, input_arg: Any
    ) -> bool:
        if not context.user_id:
            raise Exception("user is not logged in")

        # recieve the user_id of the user object being returned either as:
        # - a property of the object being returned, or;
        # - a dynamic input argument (e.g. in the case of mutations or top level queries)
        user_id = input_arg or source.__getattribute__(self.comparison_key)

        if user_id != context.user_id:
            raise Exception("logged in user does not match")

        return True
