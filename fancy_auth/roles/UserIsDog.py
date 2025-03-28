from __future__ import annotations

from typing import Any

from fancy_auth.context import Context
from fancy_auth.base_role import BaseRole

POSSIBLE_SCOPES = {
    "BARKS_AT_MAILMAN",
    "CAN_EAT_BONES",
    "CAN_SLEEP_ON_BED",
    "CHASES_SQUIRRELS",
    "CHEWS_CABLES",
    "IS_A_GOOD_BOY",
    "LIKES_TUMMY_RUBS",
}


class UserIsDog(BaseRole):
    """
    Tests if the user is a dog. Woof.
    (This is a fancy_auth role used for testing, illustrative and documentation purposes.)
    """

    role_owner = "MyTeamName"
    comparison_key = "fancy_auth_user_mammal_type"
    possible_scopes = POSSIBLE_SCOPES

    def is_role_valid(
        self, scopes: set[str] | None, source: Any, context: Context, input_arg: Any
    ) -> bool:
        if not scopes:
            raise ValueError(
                "UserIsDog requires at least one scope to be defined"
            )

        # recieve the mammal_type of the user object being returned either as:
        # - a property of the object being returned, or;
        # - a dynamic input argument (e.g. in the case of mutations)
        mammal_type = input_arg or source.__getattribute__(self.comparison_key)

        # we're only interested in dog users
        assert mammal_type == "dog", "user must be a dog"

        # (for real roles, you might want need to make a request to some external identity provider)
        dog_scopes_from_context = context.dog_scopes

        # e.g. we expect something like {'IS_A_GOOD_BOY', 'CHEWS_CABLES'}
        assert (
            type(dog_scopes_from_context) is set
        ), "context.dog_scopes must be a set of strings"

        # check if the access paths contain any of the required scopes.
        # multiple defined `scopes` are evaluated with OR logic.
        if any(scope in dog_scopes_from_context for scope in scopes):
            return True
        else:
            raise Exception("no matching scopes")
