import dataclasses as dataclasses
from functools import reduce
from textwrap import dedent
from typing import Any


def removeprefix(s: str, prefix: str) -> str:  # pragma: no cover
    """
    TODO: One this library's python requirement is >= 3.9, replace this with str.removeprefix
    See: https://docs.python.org/3/library/stdtypes.html#str.removeprefix
    """
    if s.startswith(prefix):
        # black formatter wants to add a space before ':', but flake8 does not.
        return s[len(prefix):]  # fmt: skip
    return s


def _get_error_string(expected_key: str) -> str:
    return dedent(
        f"""
        Could not find "{expected_key}" as a resolver argument. Tips:
        -  Ensure `input_arg` is the name of an argument to your resolver, and not the overall query/mutation variables
        -  Ensure `input_arg` is snake_case (as it appears in Python) rather than camelCase as it appears in the schema
        -  If this is a mutation using InputMutationExtension, make sure to prefix `input_arg` with "input."
    """.strip(
            "\n"
        )
    )


def _get_nested_dict_value(d: Any, key: str) -> str:
    try:
        return reduce(lambda d, k: d[k], key.split("."), d)
    except KeyError as e:
        # reraising to provide a helpful error message
        raise KeyError(_get_error_string(key)) from e


def get_input_arg_from_field(policy_input_arg: str, inputs: Any) -> str:
    """
    When a policy specifies `input_arg`, this returns the user-supplied argument to the field.

    Examples:

    Supports looking up a field on an input type when using InputMutationExtension
    See: https://strawberry.rocks/docs/general/mutations#the-input-mutation-extension)

        @strawberry.mutation(extensions=[
            InputMutationExtension(),
            FancyAuthExtension(policy={
                "role": "UserIsDog",
                "input_arg": "input.mammal_type"
            })
        ])
        def add_user(self, info: strawberry.Info, user_name: str, mammal_type: str) -> User:
            ...

    Also supports raw field arguments like this:

        @strawberry.mutation(extensions=[
            FancyAuthExtension(policy={
                "role": "UserIsDog",
                "input_arg": "mammal_type"
            })
        ])
        def add_user(self, info: strawberry.Info, user_name: str, mammal_type: str) -> User:
            ...

    Can also be used on query fields like this:

        # This is bad schema -- in real life, you should do `Query.user(id: 123).draftReviews`
        @strawberry.field(
            description="Get draft reviews for a user. A user may only see their own draft reviews.",
            extensions=[FancyAuthExtension(policy={
                "role": "UserMatches",
                "input_arg": "user_id",
            })]
        )
        def draft_reviews_for_user(self, user_id: str) -> Optional[List[DraftReview]]:
            return [DraftReview()]
    """
    assert inputs is not None, "`inputs` is None (did you pass any field arguments?)"

    # When using InputMutationExtension, the name of the input field is always 'input'
    if policy_input_arg.startswith("input."):
        input_dict = dataclasses.asdict(inputs["input"])
        input_field_lookup_key = removeprefix(policy_input_arg, "input.")
        input_arg = _get_nested_dict_value(d=input_dict, key=input_field_lookup_key)
    else:
        assert (
            "." not in policy_input_arg
        ), "nested input_key values are only valid with auto-generated input types"
        input_arg = inputs.get(policy_input_arg)

    assert input_arg is not None, _get_error_string(policy_input_arg)
    return input_arg
