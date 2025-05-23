from abc import ABC, abstractmethod
from pydantic import BaseModel


class ToolCall(BaseModel):
    name: str
    result: list | dict | str | float | int | None = None
    args: list | dict | str | float | int | None = None


class ToolLogBase(ABC):
    """Abstract base class for tool logging."""

    @abstractmethod
    def log(self, toolCall: ToolCall, save: bool = True):
        """Log a tool call. Must be implemented by subclasses."""
        pass
