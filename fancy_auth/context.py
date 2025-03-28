from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Context:
    """
    In real life, this would be defined in the application
    This is defined here as an example.
    """
    # distributed tracing ID
    trace_id: str

    # If the user is logged in, this will be set to their id.
    user_id: Optional[str] = None

    # If the user is logged in as a dog, this will be set to their allowed scopes.
    dog_scopes: Optional[set[str]] = None