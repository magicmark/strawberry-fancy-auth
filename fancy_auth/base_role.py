from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Collection
from typing import Any, TypeVar

from fancy_auth.context import Context

class BaseRole(ABC):
    """Base class that all FancyAuth roles must inherit from."""

    _scopes_applied: set[str] | None
    _input_arg: str | None

    role_owner: str
    comparison_key: str | None
    possible_scopes: set[str] | None

    def __init__(
        self,
        *,
        scopes: Collection[str] | None = None,
        input_arg: str | None = None,
    ):
        if scopes is not None and self.possible_scopes is None:
            raise ValueError(f"{self.__class__.__name__} does not accept scopes")

        if scopes is not None and self.possible_scopes is not None:
            for scope in scopes:
                if scope not in self.possible_scopes:
                    raise ValueError(
                        f"{scope} is not a valid scope allowed for {self.__class__.__name__}"
                    )

        self._input_arg = input_arg
        self._scopes_applied = set(scopes) if scopes is not None else None

    @abstractmethod
    def is_role_valid(
        self, scopes: set[str] | None, source: Any, context: Context, input_arg: Any
    ) -> bool: ...
