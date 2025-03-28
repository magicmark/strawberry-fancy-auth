import pytest

from fancy_auth.all_roles import ALL_ROLES


@pytest.mark.parametrize(
    "role",
    ALL_ROLES,
    ids=[role.__name__ for role in ALL_ROLES],
)
def test_role_is_valid(role):
    # If any of the properties (e.g. role_owner) are not implemented, this will throw.
    assert role(), f"Role '{role.__name__}' is not defined correctly"
    assert (
        type(role.role_owner) is str
    ), f"Role '{role.__name__}' role_owner is not a string"
