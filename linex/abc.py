from abc import ABC, abstractmethod
from typing import Any


class AbstractLineMessage(ABC):
    """Represents an abstract illustration of a valid Linex LINE message."""

    @abstractmethod
    def to_json(self) -> dict:
        """Converts the object to a valid JSON."""

class AbstractLineAction(ABC):
    """Represents an abstract illustration of a valid Linex LINE action."""
    json: dict[str, Any]

    @abstractmethod
    def to_json(self) -> dict:
        """Converts the object to a valid JSON."""
