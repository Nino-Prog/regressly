"""Deterministic assertions on model output.

Each assertion takes the output text, the spec's ``value`` and its extra options,
and returns an AssertionResult. Register new ones with ``@assertion("name")``.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


@dataclass
class AssertionResult:
    type: str
    passed: bool
    message: str = ""


AssertionFn = Callable[[str, Any, dict[str, Any]], tuple[bool, str]]
ASSERTIONS: dict[str, AssertionFn] = {}


def assertion(name: str) -> Callable[[AssertionFn], AssertionFn]:
    def register(fn: AssertionFn) -> AssertionFn:
        ASSERTIONS[name] = fn
        return fn

    return register


def evaluate(kind: str, output: str, value: Any, options: dict[str, Any]) -> AssertionResult:
    try:
        passed, message = ASSERTIONS[kind](output, value, options)
    except Exception as e:  # a broken assertion config should fail the test, not the run
        return AssertionResult(kind, False, f"error: {e}")
    return AssertionResult(kind, passed, message)


def _fold(text: str, options: dict[str, Any]) -> str:
    return text if options.get("case_sensitive", False) else text.casefold()


def _preview(text: str, limit: int = 80) -> str:
    text = " ".join(text.split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


@assertion("contains")
def _contains(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    if _fold(str(value), options) in _fold(output, options):
        return True, ""
    return False, f"expected output to contain {value!r}; got {_preview(output)!r}"


@assertion("not-contains")
def _not_contains(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    if _fold(str(value), options) not in _fold(output, options):
        return True, ""
    return False, f"expected output not to contain {value!r}"


@assertion("equals")
def _equals(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    if _fold(output.strip(), options) == _fold(str(value).strip(), options):
        return True, ""
    return False, f"expected {value!r}; got {_preview(output)!r}"


@assertion("regex")
def _regex(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    flags = 0 if options.get("case_sensitive", True) else re.IGNORECASE
    if re.search(str(value), output, flags):
        return True, ""
    return False, f"pattern {value!r} not found"


@assertion("max-length")
def _max_length(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    if len(output) <= int(value):
        return True, ""
    return False, f"output is {len(output)} chars; max is {value}"


@assertion("min-length")
def _min_length(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    if len(output) >= int(value):
        return True, ""
    return False, f"output is {len(output)} chars; min is {value}"


_FENCE = re.compile(r"^\s*```(?:json)?\s*\n(.*?)\n\s*```\s*$", re.DOTALL)


def strip_code_fence(text: str) -> str:
    match = _FENCE.match(text)
    return match.group(1) if match else text


@assertion("json-valid")
def _json_valid(output: str, value: Any, options: dict[str, Any]) -> tuple[bool, str]:
    try:
        json.loads(strip_code_fence(output))
    except json.JSONDecodeError as e:
        return False, f"output is not valid JSON ({e})"
    return True, ""
