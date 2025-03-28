# fancy_auth

`@fancy_auth` is a Python decorator to declare the viewing user's authentication and authorization requirements for access to be granted.

## Roles

A 'Role' defines what auth permissions a user must have. e.g. `UserMatches` checks that the user is logged in, and that their id matches that of the User object being returned. All roles inherit from `BaseRole`.

## Usage

`fancy_auth` can be applied in the following ways

- `@fancy_auth(role=...)` (to check a single role)
- `@fancy_auth(match_any=[..., ...])` (**any** role may match for access to be granted)
- `@fancy_auth(match_all=[..., ...])` (**all** roles must match for access to be granted)

### Example

`@fancy_auth` may be applied to individual fields on a type:

```python
@strawberry.type
class User:
    id: str
    fancy_auth_user_owner_id: strawberry.Private[str]

    @strawberry.field
    def name(self, info: strawberry.Info) -> Optional[str]:
        # this is public
        return "Mark L."

    @fancy_auth(UserMatches())
    @strawberry.field
    def password(self, info: strawberry.Info) -> Optional[str]:
        # this is private!!
        return "hunter2"
```

`@fancy_auth` may also be applied to whole types (which should be favored where possible):

```python
# all fields in CreditCardDetails are protected by FancyAuth.
@fancy_auth(UserMatches())
@strawberry.type
class CreditCardDetails:
    fancy_auth_user_owner_id: strawberry.Private[str]
    long_number: Optional[str]
    expiry: Optional[str]
    ccv: Optional[str]
```

## Comparison key

Each role defines a `comparison_key`. This must exist as an attribute on objects that want to be protected by that role. This tells FancyAuth who "owns" that type, and does the role have access to it or not.

For example, `UserMatches` above sets its `comparison_key` as follows:

```python
class UserMatches(BaseRole):
    comparison_key = "fancy_auth_user_owner_id"
```

All types that use `UserMatches` must provide `fancy_auth_user_owner_id` as a `strawberry.Private[...]` attribute:

```python
@strawberry.type
class User:
    # The ID of the user
    fancy_auth_user_owner_id: strawberry.Private[str]

    @fancy_auth(UserMatches())
    @strawberry.field
    def password(self, info: strawberry.Info) -> Optional[str]: ...


@fancy_auth(UserMatches())
@strawberry.type
class UserAddress:
    # The ID of the user whose address this is
    fancy_auth_user_owner_id: strawberry.Private[str]
    address_line_1: str
    zip_code: str
    country: str


@strawberry.type
class Event:
    # The ID of the user who created this event
    fancy_auth_user_owner_id: strawberry.Private[str]

    @fancy_auth(UserMatches())
    @strawberry.field
    def invitations(self, info: strawberry.Info) -> list[EventInvites]: ...
```

## Policy vs Role

- A "Role" represents a single permission the user may have (e.g. `UserIsDog`).
- A "Policy" is the declared set of roles, and evaluation logic applied to a field or type:

```python
@dataclass
class FancyAuthPolicy:
    roles: list[BaseRole]
    evaluation_logic: Literal["any", "all"]
    applied_to: Literal["field", "type"]
```
