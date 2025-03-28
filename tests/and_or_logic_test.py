from typing import Optional

import strawberry

from fancy_auth.context import Context
from fancy_auth import fancy_auth
from fancy_auth.roles import UserIsDog
from fancy_auth.roles import UserMatches


def test_and_logic():
    @strawberry.type
    class Foo:
        fancy_auth_user_owner_id: strawberry.Private[str]
        fancy_auth_user_mammal_type: strawberry.Private[str]

        @fancy_auth(match_all=[UserMatches(), UserIsDog(scopes=["IS_A_GOOD_BOY"])])
        @strawberry.field
        def foo(self, info: strawberry.Info) -> Optional[str]:
            return "access granted"

    @strawberry.type
    class Query:
        @strawberry.field
        def foo(self) -> Optional[Foo]:
            return Foo(
                fancy_auth_user_owner_id="abc123",
                fancy_auth_user_mammal_type="dog",
            )

    schema = strawberry.Schema(query=Query)

    # test with access
    result = schema.execute_sync(
        "{ foo { foo } }",
        variable_values=None,
        context_value=Context(trace_id="aaa", user_id="abc123", dog_scopes={"IS_A_GOOD_BOY"}),
    )
    assert result.data
    assert result.data["foo"] == {"foo": "access granted"}

    # test with only one valid policy
    result = schema.execute_sync(
        "{ foo { foo } }",
        variable_values=None,
        context_value=Context(trace_id="aaa", user_id="abc123", dog_scopes=None),
    )
    assert result.data
    assert result.data["foo"] == {"foo": None}


def test_or_logic():
    @strawberry.type
    class Foo:
        fancy_auth_user_owner_id: strawberry.Private[str]
        fancy_auth_user_mammal_type: strawberry.Private[str]

        @fancy_auth(match_any=[UserMatches(), UserIsDog(scopes=["IS_A_GOOD_BOY"])])
        @strawberry.field
        def foo(self, info: strawberry.Info) -> Optional[str]:
            return "access granted"

    @strawberry.type
    class Query:
        @strawberry.field
        def foo(self) -> Optional[Foo]:
            return Foo(
                fancy_auth_user_owner_id="abc123",
                fancy_auth_user_mammal_type="dog",
            )

    schema = strawberry.Schema(query=Query)

    # test with access
    result = schema.execute_sync(
        "{ foo { foo } }",
        variable_values=None,
        context_value=Context(trace_id="aaa", user_id="abc123", dog_scopes={"IS_A_GOOD_BOY"}),
    )
    assert result.data
    assert result.data["foo"] == {"foo": "access granted"}

    # test with only one valid policy
    result = schema.execute_sync(
        "{ foo { foo } }",
        variable_values=None,
        context_value=Context(trace_id="aaa", user_id="abc123", dog_scopes=None),
    )
    assert result.data
    assert result.data["foo"] == {"foo": "access granted"}
