"""Model providers, looked up by the ``type`` field in a suite."""

from __future__ import annotations

from regressly.providers.base import Completion, Provider, ProviderError
from regressly.providers.echo import EchoProvider
from regressly.suite import ProviderConfig, SuiteError

__all__ = ["Completion", "Provider", "ProviderError", "create_provider"]


def create_provider(config: ProviderConfig) -> Provider:
    if config.type == "echo":
        return EchoProvider(config.id, config.options)
    if config.type == "anthropic":
        # Imported lazily so offline suites don't need the SDK configured.
        from regressly.providers.anthropic import AnthropicProvider

        return AnthropicProvider(config.id, config.options)
    raise SuiteError(f"unknown provider type '{config.type}' (known: anthropic, echo)")
