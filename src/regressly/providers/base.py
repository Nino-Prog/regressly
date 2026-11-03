"""The provider interface every model backend implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Completion:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    # Why generation stopped, when the provider reports it (e.g. "end_turn", "refusal").
    stop_reason: str | None = None


class ProviderError(RuntimeError):
    """A provider call failed (network, auth, rate limit...). Distinct from a failed assertion."""


class Provider(ABC):
    def __init__(self, id: str, options: dict[str, Any]):
        self.id = id
        self.options = options

    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> Completion: ...

    async def close(self) -> None:  # noqa: B027 - optional hook
        """Release network resources. Called once after a run."""
