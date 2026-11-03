"""A provider that returns the prompt it was given. No network, no cost."""

from __future__ import annotations

from regressly.providers.base import Completion, Provider


class EchoProvider(Provider):
    """Options: ``prefix`` (prepended to the output), ``response`` (fixed output)."""

    async def complete(self, prompt: str, system: str | None = None) -> Completion:
        if "response" in self.options:
            return Completion(text=str(self.options["response"]), stop_reason="end_turn")
        return Completion(text=self.options.get("prefix", "") + prompt, stop_reason="end_turn")
