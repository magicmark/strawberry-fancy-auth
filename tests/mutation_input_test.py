import traceback
from collections import namedtuple
from typing import Optional

import pytest
import strawberry
from strawberry.field_extensions import InputMutationExtension

from fancy_auth.context import Context
from fancy_auth import FancyAuthExtension
from fancy_auth.roles import UserMatches


def get_schema_with_input_arg(input_arg: str):
    @strawberry.type
    class User:
        id: str
        favorite_food: str

    @strawberry.type
    class Query:
        _: str = "This is a dummy field to make the Query type non-empty"

    @strawberry.type
    class Mutation:
        @strawberry.mutation(
            extensions=[
                InputMutationExtension(),
                FancyAuthExtension(UserMatches(input_arg=input_arg)),
            ]
        )
        def update_favorite_food(
            self, info: strawberry.Info, user_id: str, new_favorite_food: str
        ) -> Optional[User]:
            return User(id=user_id, favorite_food=new_favorite_food)

    return strawberry.Schema(query=Query, mutation=Mutation)


TestCase = namedtuple(
    "TestCase",
    ["id", "input_arg", "user_id", "expected_result", "expected_error"],
)


TEST_CASES = [
    TestCase(
        id="test_mutation_input_with_access",
        input_arg="input.user_id",
        user_id="abc123",  # the logged-in user making the request matches the user object being returned
        expected_result={"id": "abc123", "favoriteFood": "pizza"},
        expected_error=None,
    ),
    TestCase(
        id="test_mutation_input_different_viewer",
        input_arg="input.user_id",
        user_id="bar456",  # represents a different requesting user
        expected_result=None,
        expected_error="Access denied to field",
    ),
    TestCase(
        id="test_mutation_input_no_viewer",
        input_arg="input.user_id",
        user_id=None,  # user is not logged in
        expected_result=None,
        expected_error="Access denied to field",
    ),
    TestCase(
        id="test_mutation_input_bad_input_arg_1",
        input_arg="input.oops_i_dont_exist",
        user_id="abc123",
        expected_result=None,
        expected_error='Could not find "oops_i_dont_exist" as a resolver argument.',
    ),
    TestCase(
        id="test_mutation_input_bad_input_arg_2",
        input_arg="i_also_dont_exist",
        user_id="abc123",
        expected_result=None,
        expected_error="make sure to prefix `input_arg`",
    ),
]


@pytest.mark.parametrize(
    ",".join(TestCase._fields[1:]),
    [tuple(test_case)[1:] for test_case in TEST_CASES],
    ids=[test_case.id for test_case in TEST_CASES],
)
def test_mutation_input(
    input_arg, user_id, expected_result, expected_error
):
    schema = get_schema_with_input_arg(input_arg)
    context = Context(trace_id="fake-trace-id", user_id=user_id)

    result = schema.execute_sync(
        """
        mutation UpdateFavoriteFood($updated_user_food_input: UpdateFavoriteFoodInput!) {
            updateFavoriteFood(input: $updated_user_food_input) {
                id
                favoriteFood
            }
        }
        """,
        variable_values={
            "updated_user_food_input": {
                "userId": "abc123",
                "newFavoriteFood": "pizza",
            }
        },
        context_value=context,
    )

    if expected_error:
        full_traceback = "".join(
            traceback.TracebackException.from_exception(result.errors[0]).format()
        )
        assert "Access denied to field" in str(result.errors[0])
        assert expected_error in full_traceback
    else:
        assert not result.errors

    assert result.data["updateFavoriteFood"] == expected_result
