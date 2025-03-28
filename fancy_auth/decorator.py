from __future__ import annotations

from typing import Any
from typing import Callable
from typing import TypeVar

from strawberry.types.field import StrawberryField

from fancy_auth.base_role import BaseRole
from fancy_auth.directives import (
    get_directive_description_from_policy,
)
from fancy_auth.field_extension import FancyAuthExtension
from fancy_auth.policy import get_policy_from_role_args

T = TypeVar(
    "T", StrawberryField, Any
)  # TODO: swap Any for WithStrawberryObjectDefinition. Currently this doesn't work :think:

USAGE_MESSAGE = """\
@fancy_auth must be applied before the @strawberry.type/@strawberry.field decorator

Example:

@fancy_auth(UserMatches())
@strawberry.type
class CreditCardDetails:
    ...
"""


def fancy_auth(
    role: BaseRole | None = None,
    *,
    match_all: list[BaseRole] | None = None,
    match_any: list[BaseRole] | None = None,
) -> Callable[[T], T]:
    """
    Apply this as a decorator to a Strawberry type to protect all fields with fancy_auth:

        @fancy_auth(UserMatches())
        @strawberry.type
        class CreditCardDetails:
            # All fields below will have fancy_auth automatically applied.
            long_number: str
            expiry: str

    Can also be applied to individual fields:

        @strawberry.type
        class User:
            @fancy_auth(UserMatches())
            @strawberry.field
            def password(self) -> User:
                return 'hunter2'

    (Reminder: we reccomend applying to whole types where possible!)
    """

    def wrapper(strawberry_type_or_field: T) -> T:
        if isinstance(strawberry_type_or_field, StrawberryField):
            # apply the extension to the field.
            strawberry_type_or_field.extensions.append(
                FancyAuthExtension(
                    role=role,
                    match_all=match_all,
                    match_any=match_any,
                )
            )
        else:
            policy = get_policy_from_role_args(
                applied_to="type",
                role=role,
                match_all=match_all,
                match_any=match_any,
            )

            strawberry_type = strawberry_type_or_field

            # @fancy_auth must be applied before @strawberry.type.
            if "__strawberry_definition__" not in strawberry_type.__dict__.keys():
                raise Exception(USAGE_MESSAGE)

            for field in strawberry_type.__strawberry_definition__.fields:
                # It's possible that a field already has fancy_auth applied to it.
                #
                # This might make sense if a field has a different permission level than the rest of the type.
                # ...or maybe it's duplicated by mistake.
                #
                # Either way, it's ok - if this happens, we'll evaluate all instances of fancy_auth on the field.
                field.extensions.append(
                    FancyAuthExtension(
                        role=role,
                        match_all=match_all,
                        match_any=match_any,
                    )
                )

            description = get_directive_description_from_policy(policy)
            existing_description = strawberry_type.__strawberry_definition__.description

            if existing_description is None:
                strawberry_type.__strawberry_definition__.description = description
            else:
                strawberry_type.__strawberry_definition__.description = (
                    existing_description + "\n\n" + description
                )

        return strawberry_type_or_field

    return wrapper
