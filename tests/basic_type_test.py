from typing import Optional

import pytest
import strawberry

from fancy_auth.context import Context
from fancy_auth import fancy_auth
from fancy_auth.roles import UserMatches


@pytest.fixture
def schema():
    @fancy_auth(UserMatches())
    @strawberry.type
    class CreditCardDetails:
        fancy_auth_user_owner_id: strawberry.Private[str]
        long_number: Optional[str]
        expiry: Optional[str]
        ccv: Optional[str]

    @strawberry.type
    class User:
        id: str

        @strawberry.field
        def saved_credit_card(
            self, info: strawberry.Info
        ) -> Optional[CreditCardDetails]:
            return CreditCardDetails(
                fancy_auth_user_owner_id=self.id,
                long_number="4111 1111 1111 1111",
                expiry="12/24",
                ccv="123",
            )

    @strawberry.type
    class Query:
        @strawberry.field
        def user(self) -> User:
            return User(id="abc123")

    return strawberry.Schema(query=Query)


def test_basic_type_with_access(schema):
    context = Context(trace_id="aaa", user_id="abc123")

    result = schema.execute_sync(
        """
        query {
            user {
                id
                savedCreditCard {
                    longNumber
                    expiry
                    ccv
                }
            }
        }
        """,
        variable_values=None,
        context_value=context,
    )

    assert not result.errors
    assert result.data["user"] == {
        "id": "abc123",
        "savedCreditCard": {
            "longNumber": "4111 1111 1111 1111",
            "expiry": "12/24",
            "ccv": "123",
        },
    }


def test_basic_type_different_viewer(schema):
    # represents a different requesting user
    context = Context(trace_id="aaa", user_id="bar456")

    result = schema.execute_sync(
        """
        query {
            user {
                id
                savedCreditCard {
                    longNumber
                    expiry
                    ccv
                }
            }
        }
        """,
        variable_values=None,
        context_value=context,
    )

    # Each field will error individually.
    assert "Access denied to field" in str(result.errors[0])
    assert "Access denied to field" in str(result.errors[1])
    assert "Access denied to field" in str(result.errors[2])

    assert result.data["user"] == {
        "id": "abc123",
        "savedCreditCard": {
            "longNumber": None,
            "expiry": None,
            "ccv": None,
        },
    }
