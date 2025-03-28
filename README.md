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
