import traceback
from collections import namedtuple
from typing import List
from typing import Optional

import pytest
import strawberry

from fancy_auth.context import Context
from fancy_auth import fancy_auth
from fancy_auth.roles import UserMatches


def get_schema_with_input_arg(input_arg: str):
    @strawberry.type
    class DraftReview:
        body: str = strawberry.field(default="the fries were great")

    @strawberry.type
    class Query:
        # This is bad schema -- in real life, you'd probably to do `Query.user(id: 123).draftReviews`
        @fancy_auth(UserMatches(input_arg=input_arg))
        @strawberry.field
        def draft_reviews_for_user(
            self, user_id: str
        ) -> Optional[List[DraftReview]]:
            return [DraftReview()]

    return strawberry.Schema(query=Query)


TestCase = namedtuple(
    "TestCase",
    ["id", "input_arg", "user_id", "expected_result", "expected_error"],
)

TEST_CASES = [
    TestCase(
        id="test_field_input_arg_with_access",
        input_arg="user_id",
        user_id="abc123",  # the logged-in user making the request matches the user object being returned
        expected_result=[{"body": "the fries were great"}],
        expected_error=None,
    ),
    TestCase(
        id="test_field_input_arg_different_viewer",
        input_arg="user_id",
        user_id="bar456",  # represents a different requesting user
        expected_result=None,
        expected_error="Access denied to field",
    ),
    TestCase(
        id="test_field_input_arg_no_viewer",
        input_arg="user_id",
        user_id=None,  # user is not logged in
        expected_result=None,
        expected_error="Access denied to field",
    ),
    TestCase(
        id="test_field_input_arg_bad_input_arg",
        input_arg="oops_i_dont_exist",
        user_id=None,
        expected_result=None,
        expected_error='Could not find "oops_i_dont_exist" as a resolver argument',
    ),
]


@pytest.mark.parametrize(
    ",".join(TestCase._fields[1:]),
    [tuple(test_case)[1:] for test_case in TEST_CASES],
    ids=[test_case.id for test_case in TEST_CASES],
)
def test_field_input_arg(
    input_arg, user_id, expected_result, expected_error
):
    schema = get_schema_with_input_arg(input_arg)
    context = Context(trace_id="aaa", user_id=user_id)

    result = schema.execute_sync(
        "query GetDraftReviews($id: String!) { draftReviewsForUser(userId: $id) { body } }",
        variable_values={"id": "abc123"},
        context_value=context,
    )

    if expected_error:
        assert result.errors
        full_traceback = "".join(
            traceback.TracebackException.from_exception(result.errors[0]).format()
        )
        assert "Access denied to field" in str(result.errors[0])
        assert expected_error in full_traceback
    else:
        assert not result.errors

    assert result.data
    assert result.data["draftReviewsForUser"] == expected_result
