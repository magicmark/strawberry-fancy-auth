from typing import Optional

import pytest
import strawberry

from fancy_auth import fancy_auth
from fancy_auth.roles import UserIsDog
from fancy_auth.roles import UserMatches


def test_bad_type_decorator_order():
    with pytest.raises(Exception) as e:

        @strawberry.type
        @fancy_auth(UserMatches())
        class CreditCardDetails:
            long_number: str

    assert (
        "@fancy_auth must be applied before the @strawberry.type/@strawberry.field decorator"
        in str(e)
    )


def test_bad_field_decorator_order():
    with pytest.raises(Exception) as e:

        @strawberry.type
        class User:
            @strawberry.field
            @fancy_auth(UserMatches())
            def password(
                self, info: strawberry.Info
            ) -> Optional[str]: ...  # pragma: no cover

    assert (
        "@fancy_auth must be applied before the @strawberry.type/@strawberry.field decorator"
        in str(e)
    )


def test_no_comparison_key_on_type():
    with pytest.raises(Exception) as e:

        @fancy_auth(UserMatches())
        @strawberry.type
        class CreditCardDetails:
            long_number: str

        @strawberry.type
        class Query:
            _: str = "This is a dummy field to make the Query type non-empty"

        strawberry.Schema(query=Query, types=[CreditCardDetails])

    assert (
        "Error applying UserMatches on CreditCardDetails: "
        "fancy_auth_user_owner_id was not found as an attribute on the type."
    ) in str(e)


def test_and_and_or_policy():
    with pytest.raises(Exception) as e:

        @fancy_auth(
            match_all=[UserMatches()],
            match_any=[UserMatches()],
        )
        @strawberry.type
        class CreditCardDetails:
            fancy_auth_user_owner_id: strawberry.Private[str]
            long_number: str

    assert "must provide exactly one of role, match_all, or match_any" in str(e)


def test_no_scopes_allowed():
    with pytest.raises(Exception) as e:

        @fancy_auth(UserMatches(scopes=["FOO"]))
        @strawberry.type
        class CreditCardDetails:  # pragma: no cover
            fancy_auth_user_owner_id: strawberry.Private[str]
            long_number: str

    assert "UserMatches does not accept scopes" in str(e)


def test_invalid_scope():
    with pytest.raises(Exception) as e:

        @fancy_auth(UserIsDog(scopes=["MEOW_HISS"]))
        @strawberry.type
        class CreditCardDetails:  # pragma: no cover
            long_number: str

    assert "MEOW_HISS is not a valid scope allowed for UserIsDog" in str(e)
