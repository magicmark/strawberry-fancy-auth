from __future__ import annotations

import json
from enum import Enum
from typing import Callable

import strawberry
from strawberry.schema_directive import (  # noqa: F403 - (why is flake8 complaining about this??)
    Location,
)

from fancy_auth.base_role import BaseRole
from fancy_auth.policy import FancyAuthPolicy


@strawberry.enum
class RoleName(Enum):
    UserIsDog = "UserIsDog"
    UserMatches = "UserMatches"


@strawberry.input
class FancyAuthDirectiveRoleInput:
    name: RoleName
    scopes: list[str] | None = strawberry.UNSET
    input_arg: str | None = strawberry.UNSET


@strawberry.schema_directive(
    locations=[Location.OBJECT, Location.FIELD_DEFINITION],
    repeatable=True,
    description="Applies access control to fields and types at runtime.",
    name="FancyAuthPrivate",
)
class FancyAuthDirective:
    match_all: list[FancyAuthDirectiveRoleInput] | None = strawberry.UNSET
    match_any: list[FancyAuthDirectiveRoleInput] | None = strawberry.UNSET
    role: FancyAuthDirectiveRoleInput | None = strawberry.UNSET


def _serialize_role_sdl(role: BaseRole) -> str:
    """stringify the policy arguments as they would appear if written in SDL by hand"""
    serialized = f"name: {role.__class__.__name__}"

    if role._scopes_applied:
        serialized += f", scopes: {json.dumps(sorted(role._scopes_applied))}"

    if role._input_arg:
        serialized += f", inputArg: {json.dumps(role._input_arg)}"  # json.dumps surrounds with quotes if necessary

    return f"{{{serialized}}}"


def get_directive_description_from_policy(
    policy: FancyAuthPolicy,
) -> str:
    serialized_roles = ", ".join([_serialize_role_sdl(role) for role in policy.roles])

    if len(policy.roles) == 1:
        policy_string = f"role: {serialized_roles}"
    elif policy.evaluation_logic == "any":
        policy_string = f"match_any: {serialized_roles}"
    else:
        assert policy.evaluation_logic == "all"
        policy_string = f"match_all={serialized_roles}"

    return "\n".join(
        [
            f"🔐 fancy_auth applied to {policy.applied_to}:",
            "",
            f"@fancyAuthPrivate({policy_string})",
        ]
    )


def get_fancy_auth_directive_from_policy(
    policy: FancyAuthPolicy,
) -> FancyAuthDirective:
    """Translates a `FancyAuthPolicy` dict to a `FancyAuthDirective` Strawberry directive."""

    # Translate a fancy_auth role (i.e. inhereted from BaseRole) into a FancyAuthDirectiveRoleInput
    get_role_input: Callable[[BaseRole], FancyAuthDirectiveRoleInput] = (
        lambda role: FancyAuthDirectiveRoleInput(
            name=RoleName[role.__class__.__name__],
            scopes=(
                sorted(role._scopes_applied)
                if role._scopes_applied
                else strawberry.UNSET
            ),
            input_arg=role._input_arg if role._input_arg else strawberry.UNSET,
        )
    )

    if len(policy.roles) == 1:
        return FancyAuthDirective(role=get_role_input(policy.roles[0]))

    if policy.evaluation_logic == "any":
        return FancyAuthDirective(
            match_any=[get_role_input(role) for role in policy.roles]
        )

    assert policy.evaluation_logic == "all"  # sanity check
    return FancyAuthDirective(match_all=[get_role_input(role) for role in policy.roles])
