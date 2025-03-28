import asyncio
from typing import Optional

import pytest
import strawberry

from fancy_auth.context import Context
from fancy_auth import FancyAuthExtension
from fancy_auth import fancy_auth
from fancy_auth.roles import UserMatches


@pytest.fixture
def schema():
    async def get_ssn() -> str:
        await asyncio.sleep(0.1)
        return "123-45-6789"

    @strawberry.type
    class User:
        id: str
        fancy_auth_user_owner_id: strawberry.Private[str]

        @fancy_auth(UserMatches())
        @strawberry.field
        async def password(self, info: strawberry.Info) -> Optional[str]:
            await asyncio.sleep(0.1)
            return "hunter2"

        social_security_number: Optional[str] = strawberry.field(
            extensions=[FancyAuthExtension(UserMatches())],
            resolver=get_ssn,
        )

        @fancy_auth(UserMatches())
        @strawberry.field
        def full_name(self, info: strawberry.Info) -> Optional[str]:
            # let's check mixing sync and async reoslvers
            return "Bruce Wayne"

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id="abc123", fancy_auth_user_owner_id="abc123")

    return strawberry.Schema(query=Query)


def test_basic_private_field_with_access(schema):
    context = Context(trace_id="fake-trace-id", user_id="abc123")

    result = asyncio.run(
        schema.execute(
            "{ user { id password socialSecurityNumber fullName } }",
            variable_values=None,
            context_value=context,
        )
    )

    assert not result.errors
    assert result.data["user"] == {
        "id": "abc123",
        "password": "hunter2",
        "socialSecurityNumber": "123-45-6789",
        "fullName": "Bruce Wayne",
    }


def test_basic_private_field_without_access(schema):
    context = Context(trace_id="fake-trace-id", user_id=None)

    result = asyncio.run(
        schema.execute(
            "{ user { id password socialSecurityNumber fullName } }",
            variable_values=None,
            context_value=context,
        )
    )

    assert len(result.errors) == 3
    assert "Access denied to field" in str(result.errors[0])
    assert ["user", "password"] == result.errors[0].path

    assert result.data
    assert result.data["user"] == {
        "id": "abc123",
        "password": None,
        "socialSecurityNumber": None,
        "fullName": None,
    }
