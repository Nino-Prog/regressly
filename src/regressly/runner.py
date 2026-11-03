"""Runs every test against every provider, concurrently."""

from __future__ import annotations

import asyncio
import time
from dataclasses import asdict, dataclass, field
from enum import Enum

from regressly.assertions import AssertionResult, evaluate
from regressly.providers import Provider, ProviderError, create_provider
from regressly.suite import Suite, TestCase


class Status(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"  # the model call itself failed; no assertions ran


@dataclass
class TestResult:
    test: str
    provider: str
    status: Status
    output: str = ""
    latency_ms: float = 0.0
    input_tokens: int | None = None
    output_tokens: int | None = None
    stop_reason: str | None = None
    error: str | None = None
    assertions: list[AssertionResult] = field(default_factory=list)


@dataclass
class RunResult:
    suite: str
    results: list[TestResult]
    duration_ms: float

    def count(self, status: Status) -> int:
        return sum(1 for r in self.results if r.status is status)

    @property
    def ok(self) -> bool:
        return all(r.status is Status.PASSED for r in self.results)

    def to_dict(self) -> dict:
        return {
            "suite": self.suite,
            "duration_ms": round(self.duration_ms, 1),
            "summary": {s.value: self.count(s) for s in Status},
            "results": [asdict(r) for r in self.results],
        }


async def run_suite(
    suite: Suite,
    concurrency: int = 8,
    only_provider: str | None = None,
    providers: list[Provider] | None = None,
) -> RunResult:
    """Run ``suite``. Pass ``providers`` to inject instances (useful in tests)."""
    if providers is None:
        configs = [p for p in suite.providers if only_provider in (None, p.id)]
        providers = [create_provider(c) for c in configs]
    if not providers:
        raise ValueError(f"no provider with id '{only_provider}'")

    semaphore = asyncio.Semaphore(concurrency)
    start = time.perf_counter()

    async def one(test: TestCase, provider: Provider) -> TestResult:
        async with semaphore:
            return await run_test(test, provider)

    try:
        results = await asyncio.gather(*(one(t, p) for p in providers for t in suite.tests))
    finally:
        await asyncio.gather(*(p.close() for p in providers))

    return RunResult(suite.name, list(results), (time.perf_counter() - start) * 1000)


async def run_test(test: TestCase, provider: Provider) -> TestResult:
    start = time.perf_counter()
    try:
        completion = await provider.complete(test.render_prompt(), test.render_system())
    except ProviderError as e:
        return TestResult(
            test.name, provider.id, Status.ERROR,
            latency_ms=(time.perf_counter() - start) * 1000, error=str(e),
        )
    latency = (time.perf_counter() - start) * 1000

    checks = [evaluate(a.type, completion.text, a.value, a.options) for a in test.asserts]
    if completion.stop_reason == "refusal":
        checks.insert(0, AssertionResult("refusal", False, "model declined to answer"))
    status = Status.PASSED if all(c.passed for c in checks) else Status.FAILED

    return TestResult(
        test=test.name,
        provider=provider.id,
        status=status,
        output=completion.text,
        latency_ms=latency,
        input_tokens=completion.input_tokens,
        output_tokens=completion.output_tokens,
        stop_reason=completion.stop_reason,
        assertions=checks,
    )
