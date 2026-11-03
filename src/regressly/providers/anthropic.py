"""Claude via the official Anthropic SDK."""

from __future__ import annotations

from typing import Any

import anthropic

from regressly.providers.base import Completion, Provider, ProviderError

DEFAULT_MODEL = "claude-opus-5-5"
DEFAULT_MAX_TOKENS = 4096


class AnthropicProvider(Provider):
    """Options: ``model``, ``max_tokens``, ``effort`` (low|medium|high|xhigh|max).

    No server-side model fallback is configured on purpose: a test result has to
    come from the model the suite names, or comparisons between runs are meaningless.
    """

    def __init__(self, id: str, options: dict[str, Any]):
        super().__init__(id, options)
        self.model = options.get("model", DEFAULT_MODEL)
        self.max_tokens = int(options.get("max_tokens", DEFAULT_MAX_TOKENS))
        self.effort = options.get("effort")
        self._client = anthropic.AsyncAnthropic()

    async def complete(self, prompt: str, system: str | None = None) -> Completion:
        params: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system:
            params["system"] = system
        if self.effort:
            params["output_config"] = {"effort": self.effort}

        try:
            response = await self._client.messages.create(**params)
        except anthropic.AuthenticationError as e:
            raise ProviderError("authentication failed: set ANTHROPIC_API_KEY") from e
        except anthropic.RateLimitError as e:
            raise ProviderError("rate limited after SDK retries; lower --concurrency") from e
        except anthropic.APIStatusError as e:
            raise ProviderError(f"API error {e.status_code}: {e.message}") from e
        except anthropic.APIConnectionError as e:
            raise ProviderError(f"connection error: {e}") from e
        except TypeError as e:
            # The SDK raises TypeError at request time when no credentials resolve.
            if "authentication" not in str(e):
                raise
            raise ProviderError(
                "no Anthropic credentials found: set ANTHROPIC_API_KEY or run `ant auth login`"
            ) from e

        text = "".join(block.text for block in response.content if block.type == "text")
        return Completion(
            text=text,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            stop_reason=response.stop_reason,
        )

    async def close(self) -> None:
        await self._client.close()
