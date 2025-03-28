# flake8: noqa: W293
import strawberry
from strawberry.printer import print_schema

from fancy_auth import fancy_auth
from fancy_auth.roles import UserIsDog
from fancy_auth.roles import UserMatches


@strawberry.type
class Query:
    _: str = "This is a dummy field to make the Query type non-empty"


def test_field():
    @strawberry.type
    class User:
        fancy_auth_user_owner_id: strawberry.Private[str]

        @fancy_auth(UserMatches())
        @strawberry.field
        def password(self) -> str:
            return "hunter2"  # pragma: no cover

    schema = strawberry.Schema(query=Query, types=[User])
    sdl = print_schema(schema)

    assert (
        '''\
type User {
  """
  🔐 fancy_auth applied to field:
  
  @fancyAuthPrivate(role: {name: UserMatches})
  """
  password: String! @fancyAuthPrivate(role: {name: UserMatches})
}'''
        in sdl
    )


def test_field_with_existing_description():
    @strawberry.type
    class User:
        fancy_auth_user_owner_id: strawberry.Private[str]

        @fancy_auth(UserMatches())
        @strawberry.field(description="the user's super secret password")
        def password(self) -> str:
            return "hunter2"  # pragma: no cover

    schema = strawberry.Schema(query=Query, types=[User])
    sdl = print_schema(schema)

    assert (
        '''\
type User {
  """
  the user's super secret password
  
  🔐 fancy_auth applied to field:
  
  @fancyAuthPrivate(role: {name: UserMatches})
  """
  password: String! @fancyAuthPrivate(role: {name: UserMatches})
}'''
        in sdl
    )


def test_field_with_scopes():
    @strawberry.type
    class User:
        fancy_auth_user_mammal_type: strawberry.Private[str]

        @fancy_auth(UserIsDog(scopes=["IS_A_GOOD_BOY", "BARKS_AT_MAILMAN"]))
        @strawberry.field
        def favorite_treat(self) -> str:
            return "kibble"  # pragma: no cover

    schema = strawberry.Schema(query=Query, types=[User])
    sdl = print_schema(schema)

    assert (
        '''\
type User {
  """
  🔐 fancy_auth applied to field:
  
  @fancyAuthPrivate(role: {name: UserIsDog, scopes: ["BARKS_AT_MAILMAN", "IS_A_GOOD_BOY"]})
  """
  favoriteTreat: String! @fancyAuthPrivate(role: {name: UserIsDog, scopes: ["BARKS_AT_MAILMAN", "IS_A_GOOD_BOY"]})
}'''
        in sdl
    )


def test_type():
    @fancy_auth(UserMatches())
    @strawberry.type
    class CreditCard:
        fancy_auth_user_owner_id: strawberry.Private[str]
        long_number: str

    schema = strawberry.Schema(query=Query, types=[CreditCard])
    sdl = print_schema(schema)

    assert (
        '''\
"""
🔐 fancy_auth applied to type:

@fancyAuthPrivate(role: {name: UserMatches})
"""
type CreditCard {
  """
  🔐 fancy_auth applied to field:
  
  @fancyAuthPrivate(role: {name: UserMatches})
  """
  longNumber: String! @fancyAuthPrivate(role: {name: UserMatches})
}'''
        in sdl
    )


def test_type_with_existing_description():
    @fancy_auth(UserMatches())
    @strawberry.type(description="a user's credit card")
    class CreditCard:
        fancy_auth_user_owner_id: strawberry.Private[str]
        long_number: str

    schema = strawberry.Schema(query=Query, types=[CreditCard])
    sdl = print_schema(schema)

    assert (
        '''\
"""
a user's credit card

🔐 fancy_auth applied to type:

@fancyAuthPrivate(role: {name: UserMatches})
"""
type CreditCard {
  """
  🔐 fancy_auth applied to field:
  
  @fancyAuthPrivate(role: {name: UserMatches})
  """
  longNumber: String! @fancyAuthPrivate(role: {name: UserMatches})
}'''
        in sdl
    )
