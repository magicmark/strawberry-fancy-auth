from typing import Optional

import pytest
import strawberry

from fancy_auth.context import Context
from fancy_auth import FancyAuthExtension
from fancy_auth import fancy_auth
from fancy_auth.roles import UserMatches


@pytest.fixture
def schema():
    def get_ssn() -> str:
        return "123-45-6789"

    @strawberry.type
    class User:
        id: str
        fancy_auth_user_owner_id: strawberry.Private[str]

        @fancy_auth(UserMatches())
        @strawberry.field
        def password(self, info: strawberry.Info) -> Optional[str]:
            return "hunter2"

        social_security_number: Optional[str] = strawberry.field(
            extensions=[FancyAuthExtension(UserMatches())],
            resolver=get_ssn,
        )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id="abc123", fancy_auth_user_owner_id="abc123")

    return strawberry.Schema(query=Query)


def test_basic_private_field_with_access(schema):
    context = Context(trace_id="fake-trace-id", user_id="abc123")

    result = schema.execute_sync(
        "{ user { id password socialSecurityNumber } }",
        variable_values=None,
        context_value=context,
    )

    assert not result.errors
    assert result.data["user"] == {
        "id": "abc123",
        "password": "hunter2",
        "socialSecurityNumber": "123-45-6789",
    }


def test_basic_private_field_different_viewer(schema):
    # represents a different requesting user
    context = Context(trace_id="fake-trace-id", user_id="bar456")

    result = schema.execute_sync(
        "{ user { id password socialSecurityNumber } }",
        variable_values=None,
        context_value=context,
    )

    assert len(result.errors) == 2
    assert "Access denied to field" in str(result.errors[0])
    assert "Access denied to field" in str(result.errors[1])
    assert ["user", "password"] == result.errors[0].path
    assert ["user", "socialSecurityNumber"] == result.errors[1].path

    assert result.data["user"] == {
        "id": "abc123",
        "password": None,
        "socialSecurityNumber": None,
    }
