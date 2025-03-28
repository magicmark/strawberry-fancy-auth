import traceback
from collections import namedtuple
from typing import Optional

import pytest
import strawberry

from fancy_auth.context import Context
from fancy_auth import FancyAuthExtension
from fancy_auth.roles import UserIsDog


def get_schema(mammal_type, scopes):
    @strawberry.type
    class User:
        fancy_auth_user_mammal_type: strawberry.Private[str]

        @strawberry.field(
            description="What breed is the user? (Oh yeah we accept doggy users now)",
            extensions=[FancyAuthExtension(UserIsDog(scopes=scopes))],
        )
        def dog_breed(self, info: strawberry.Info) -> Optional[str]:
            return "golden retriever"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> Optional[User]:
            return User(fancy_auth_user_mammal_type=mammal_type)

    return strawberry.Schema(query=Query)


TestCase = namedtuple(
    "TestCase",
    [
        "id",
        "mammal_type",
        "scopes_applied",
        "scopes_from_context",
        "expected_error",
    ],
)


TEST_CASES = [
    TestCase(
        id="test_scopes_with_access",
        mammal_type="dog",
        scopes_applied={"IS_A_GOOD_BOY", "BARKS_AT_MAILMAN"},
        scopes_from_context={"IS_A_GOOD_BOY"},
        expected_error=None,
    ),
    TestCase(
        id="test_scopes_without_access",
        mammal_type="dog",
        scopes_applied={"IS_A_GOOD_BOY", "BARKS_AT_MAILMAN"},
        scopes_from_context={"LIKES_TUMMY_RUBS"},
        expected_error="no matching scopes",
    ),
    TestCase(
        id="test_scopes_empty_scope_set",
        mammal_type="dog",
        scopes_applied=set(),
        scopes_from_context={"LIKES_TUMMY_RUBS"},
        expected_error="UserIsDog requires at least one scope to be defined",
    ),
    TestCase(
        id="test_scopes_no_scope_set",
        mammal_type="dog",
        scopes_applied=None,
        scopes_from_context={"LIKES_TUMMY_RUBS"},
        expected_error="UserIsDog requires at least one scope to be defined",
    ),
]


@pytest.mark.parametrize(
    ",".join(TestCase._fields[1:]),
    [tuple(test_case)[1:] for test_case in TEST_CASES],
    ids=[test_case.id for test_case in TEST_CASES],
)
def test_scopes(mammal_type, scopes_applied, scopes_from_context, expected_error):
    schema = get_schema(mammal_type, scopes_applied)
    context = Context(trace_id="aaa", dog_scopes=scopes_from_context)

    result = schema.execute_sync(
        "{ user { dogBreed } }",
        variable_values=None,
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
        assert result.data["user"] == {"dogBreed": "golden retriever"}
