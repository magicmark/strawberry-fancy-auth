from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from fancy_auth.base_role import BaseRole

FieldOrType = Literal["field", "type"]


@dataclass
class FancyAuthPolicy:
    roles: list[BaseRole]
    evaluation_logic: Literal["any", "all"]
    applied_to: FieldOrType


def get_policy_from_role_args(
    *,  # kwargs only
    applied_to: FieldOrType,
    role: BaseRole | None = None,
    match_all: list[BaseRole] | None = None,
    match_any: list[BaseRole] | None = None,
) -> FancyAuthPolicy:
    mutually_exclusive_args = (role, match_all, match_any)
    if sum(arg is not None for arg in mutually_exclusive_args) != 1:
        raise ValueError("must provide exactly one of role, match_all, or match_any")

    policy = None

    if match_any:
        policy = FancyAuthPolicy(match_any, "any", applied_to)

    if match_all:
        policy = FancyAuthPolicy(match_all, "all", applied_to)

    if role:
        policy = FancyAuthPolicy([role], "all", applied_to)

    assert (
        policy is not None
    )  # hint for typechecking that the above cases are exhaustive

    # check that the user passed `[Role(), ...]` (instead of `[Role, ...]`)
    for _role in policy.roles:
        # sanity check (in case typing is disabled)
        assert isinstance(
            _role, BaseRole
        ), "all roles must be instantiated (`Foo()` instead of `Foo`)"

    return policy
