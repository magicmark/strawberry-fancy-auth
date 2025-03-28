from __future__ import annotations

import dataclasses as dataclasses
import inspect
import sys
from typing import Any
from typing import Awaitable
from typing import Callable
from typing import Literal

import strawberry
from strawberry.extensions import FieldExtension
from strawberry.types.base import has_object_definition
from strawberry.types.field import StrawberryField

from fancy_auth.base_role import BaseRole
from fancy_auth.directives import (
    get_directive_description_from_policy,
)
from fancy_auth.directives import get_fancy_auth_directive_from_policy
from fancy_auth.get_input_arg import get_input_arg_from_field
from fancy_auth.policy import FancyAuthPolicy
from fancy_auth.policy import get_policy_from_role_args

if sys.version_info < (3, 11):  # pragma: no cover
    from exceptiongroup import ExceptionGroup


class FancyAuthAccessDeniedError(Exception):
    """If a type/field is protected with FancyAuth and access is denied, this error will be thrown."""

    pass


class FancyAuthExtension(FieldExtension):
    # this object stores all roles declared on the field and the associated evaluation logic (and/or)
    policy: FancyAuthPolicy

    def __init__(
        self,
        role: BaseRole | None = None,
        *,
        match_all: list[BaseRole] | None = None,
        match_any: list[BaseRole] | None = None,
    ):
        self.policy = get_policy_from_role_args(
            applied_to="field",
            role=role,
            match_all=match_all,
            match_any=match_any,
        )

        self.directive = get_fancy_auth_directive_from_policy(self.policy)
        self.description = get_directive_description_from_policy(self.policy)

    def apply(self, field: StrawberryField) -> None:
        field.directives.append(self.directive)

        if field.description is None:
            field.description = self.description
        else:
            field.description = field.description + "\n\n" + self.description

        for role in self.policy.roles:
            if role.comparison_key is not None and role._input_arg is None:
                # Let's assert that the parent type has defined a field that matches the role's `comparison_key`.
                # (The role will expect this field to be return a value, so it can compare the viewing user with the
                # user who owns the type being returned.)
                #
                # Specficially, we're looking for something like this:
                #
                #     `fancy_auth_user_owner_id: strawberry.Private[str]`
                #
                # ...or it could also be defined like this:
                #
                #     @property
                #     def fancy_auth_user_owner_id(self) -> str:
                #         ....
                #
                # TODO: we're using a bit of a sneaky way to sniff for this field on the dataclass. Is there a better
                # way to access this?
                #
                # TODO: Also assert that the field is annotated as Private.
                # This should be possible when we upgrade to the latest strawberry version and can use this helper:
                # https://github.com/strawberry-graphql/strawberry/blob/7ba5928a418/strawberry/types/private.py#L28
                comparison_field = next(
                    (
                        field
                        for field in dataclasses.fields(
                            field.origin  # type:ignore[arg-type]
                        )
                        if field.name == role.comparison_key
                    ),
                    None,
                )

                # The comparison key might also be defined as a class property method (i.e. a method using `@property`)
                has_comparison_property_method = isinstance(
                    getattr(field.origin, role.comparison_key, None), property
                )

                if not comparison_field and not has_comparison_property_method:
                    # Get the parent type name (so we can print it in the error message)
                    # TODO: bit yucky, is there a better way?
                    if field.origin is None:
                        type_name = "UnknownType"  # pragma: no cover
                    elif has_object_definition(field.origin):
                        type_name = field.origin.__strawberry_definition__.name
                    else:
                        type_name = getattr(
                            field.origin, "__name__", "UnknownType"
                        )  # pragma: no cover

                    raise TypeError(
                        f"Error applying {role.__class__.__name__} on {type_name}: "
                        f"{role.comparison_key} was not found as an attribute on the type."
                    )

    def evaluate_role(
        self, role: BaseRole, source: Any, info: strawberry.Info, inputs: Any
    ) -> bool:
        input_arg = (
            get_input_arg_from_field(role._input_arg, inputs)
            if role._input_arg is not None
            else None
        )

        return role.is_role_valid(
            scopes=role._scopes_applied,
            source=source,
            context=info.context,
            input_arg=input_arg,
        )

    def evaluate_roles(
        self, source: Any, info: strawberry.Info, inputs: Any
    ) -> list[tuple[str, Exception]]:
        """
        Evaluates the set of policies provided to @fancy_auth(...)

        Returns a list of tuples of evaluate_policy failures: [[role_name, reason], ...]
        """
        failures: list[tuple[str, Exception]] = []

        for role in self.policy.roles:
            try:
                result = self.evaluate_role(role, source, info, inputs)
            except Exception as e:
                failures.append((role.__class__.__name__, e))
                continue

            if (
                result is False
            ):  # pragma: no cover (sanity check -- roles shouldn't ever return False)
                failures.append(
                    (
                        role.__class__.__name__,
                        Exception(
                            f"{role.__class__.__name__}.is_role_valid(...) returned False. (You should raise an error instead!)"
                        ),
                    )
                )

        return failures

    def log_access_decision(
        self,
        source: Any,
        info: strawberry.Info,
        did_pass: bool,
        exceptions: list[tuple[str, Exception]],
    ) -> None:
        schema_coordinate = f"{info.path.typename}.{info.path.key}"
        roles = [
            (role.__class__.__name__, role._scopes_applied)
            for role in self.policy.roles
        ]
        policy_eval_logic = self.policy.evaluation_logic
        decision: Literal["granted", "denied"] = (
            "granted" if did_pass is True else "denied"
        )

        # Note: in the case of an `any` policy, there might be exceptions present within this array.
        # ...but overall, access was granted! therefore these don't count as a "reasons denied" and so we null this out.
        reasons_denied = exceptions if did_pass is False else None

        trace_id = info.context.trace_id

        log_line = {
            'trace_id': trace_id,
            'schema_coordinate': schema_coordinate,
            'roles': roles,
            'policy_eval_logic': policy_eval_logic,
            'decision': decision,
            'reasons_denied': reasons_denied,
        }

        print(log_line) # or write to some real logging system

    def check_policy(
        self,
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        """
        Reads the policy supplied in the schema and evaluates them against the user's context.
        Raises an error if the user does not have access to the field.
        """
        # Any arguments to the resolver are passed as kwargs. Rename to clarify.
        # We need to pass this along in order to crunch the policy's `input_arg` parameter.
        inputs = kwargs

        exceptions = self.evaluate_roles(source, info, inputs)

        if self.policy.evaluation_logic == "all":
            # ALL roles must pass
            did_pass = len(exceptions) == 0
        else:
            assert self.policy.evaluation_logic == "any"  # sanity check
            # ANY role may pass
            # i.e. some (but not all!) policies are allowed to error
            did_pass = len(self.policy.roles) - len(exceptions) > 0

        self.log_access_decision(
            source=source,
            info=info,
            did_pass=did_pass,
            exceptions=exceptions,
        )

        if not did_pass:
            raise FancyAuthAccessDeniedError(
                "Access denied to field"
            ) from ExceptionGroup("Role failures", [e for [_, e] in exceptions])

    async def resolve_async(
        self,
        next_: Callable[..., Awaitable[Any]],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        self.check_policy(source, info, **kwargs)
        retval = next_(source, info, **kwargs)
        # If the resolve_nodes method is not async, retval will not actually
        # be awaitable. We still need the `resolve_async` in here because
        # otherwise this extension can't be used together with other
        # async extensions.
        # See: https://github.com/strawberry-graphql/strawberry/blob/1edd9bb7ebestrawberry/relay/fields.py#L72-L80
        return await retval if inspect.isawaitable(retval) else retval

    def resolve(
        self,
        next_: Callable[..., Any],
        source: Any,
        info: strawberry.Info,
        **kwargs: Any,
    ) -> Any:
        self.check_policy(source, info, **kwargs)
        return next_(source, info, **kwargs)
