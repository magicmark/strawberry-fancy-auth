from types import SimpleNamespace

import pytest

from fancy_auth.context import Context
from fancy_auth.roles import UserMatches


def test_basic_access():
    assert (
        UserMatches().is_role_valid(
            scopes=None,
            source=SimpleNamespace(fancy_auth_user_owner_id="abc123"),
            context=Context(trace_id="aaa", user_id="abc123"),
            input_arg=None,
        )
        is True
    )


def test_basic_access_with_input_arg():
    assert (
        UserMatches().is_role_valid(
            scopes=None,
            source=SimpleNamespace(),
            context=Context(trace_id="aaa", user_id="abc123"),
            input_arg="abc123",
        )
        is True
    )


def test_different_logged_in_user():
    with pytest.raises(Exception) as err:
        UserMatches().is_role_valid(
            scopes=None,
            source=SimpleNamespace(fancy_auth_user_owner_id="abc123"),
            context=Context(trace_id="aaa", user_id="def456"),
            input_arg=None,
        )

    assert "logged in user does not match" in str(err.value)


def test_no_logged_in_user():
    with pytest.raises(Exception) as err:
        UserMatches().is_role_valid(
            scopes=None,
            source=SimpleNamespace(fancy_auth_user_owner_id="abc123"),
            context=Context(trace_id="aaa", user_id=None),
            input_arg=None,
        )

    assert "user is not logged in" in str(err.value)


def test_missing_comparison_key():
    with pytest.raises(Exception) as err:
        UserMatches().is_role_valid(
            scopes=None,
            source=SimpleNamespace(),
            context=Context(trace_id="aaa", user_id="abc123"),
            input_arg=None,
        )

    assert "no attribute 'fancy_auth_user_owner_id'" in str(err.value)
