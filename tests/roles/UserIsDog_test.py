from types import SimpleNamespace

import pytest

from fancy_auth.context import Context
from fancy_auth.roles import UserIsDog


def test_basic_access():
    assert (
        UserIsDog().is_role_valid(
            scopes=["LIKES_TUMMY_RUBS"],
            source=SimpleNamespace(fancy_auth_user_mammal_type="dog"),
            context=Context(trace_id="aaa", dog_scopes={"BARKS_AT_MAILMAN", "LIKES_TUMMY_RUBS"}),
            input_arg=None,
        )
        is True
    )


def test_basic_access_with_input_arg():
    assert (
        UserIsDog().is_role_valid(
            scopes=["LIKES_TUMMY_RUBS"],
            source=SimpleNamespace(),
            context=Context(trace_id="aaa", dog_scopes={"BARKS_AT_MAILMAN", "LIKES_TUMMY_RUBS"}),
            input_arg="dog",
        )
        is True
    )


def test_different_mammal():
    with pytest.raises(Exception) as err:
        UserIsDog().is_role_valid(
            scopes=["LIKES_TUMMY_RUBS"],
            source=SimpleNamespace(fancy_auth_user_mammal_type="cat"),
            context=Context(trace_id="aaa", dog_scopes={"BARKS_AT_MAILMAN", "LIKES_TUMMY_RUBS"}),
            input_arg=None,
        )

    assert "user must be a dog" in str(err.value)


def test_no_matching_scopes():
    with pytest.raises(Exception) as err:
        UserIsDog().is_role_valid(
            scopes=["LIKES_TUMMY_RUBS"],
            source=SimpleNamespace(fancy_auth_user_mammal_type="dog"),
            context=Context(trace_id="aaa", dog_scopes={"BARKS_AT_MAILMAN"}),
            input_arg=None,
        )

    assert "no matching scopes" in str(err.value)
