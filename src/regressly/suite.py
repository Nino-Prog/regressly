"""Loading and validating YAML test suites."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from regressly.assertions import ASSERTIONS

_VAR = re.compile(r"\{\{\s*(\w+)\s*\}\}")


class SuiteError(ValueError):
    """Raised when a suite file is malformed."""


@dataclass
class ProviderConfig:
    id: str
    type: str
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class AssertionSpec:
    type: str
    value: Any = None
    options: dict[str, Any] = field(default_factory=dict)


@dataclass
class TestCase:
    name: str
    prompt: str
    system: str | None
    vars: dict[str, Any]
    asserts: list[AssertionSpec]

    def render_prompt(self) -> str:
        return render(self.prompt, self.vars)

    def render_system(self) -> str | None:
        return render(self.system, self.vars) if self.system is not None else None


@dataclass
class Suite:
    name: str
    providers: list[ProviderConfig]
    tests: list[TestCase]


def render(template: str, variables: dict[str, Any]) -> str:
    """Replace ``{{name}}`` placeholders. Unknown variables raise SuiteError."""

    def sub(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in variables:
            raise SuiteError(f"undefined variable '{key}' in template")
        return str(variables[key])

    return _VAR.sub(sub, template)


def load_suite(path: str | Path) -> Suite:
    path = Path(path)
    try:
        raw = yaml.safe_load(path.read_text())
    except FileNotFoundError as e:
        raise SuiteError(f"suite file not found: {path}") from e
    except yaml.YAMLError as e:
        raise SuiteError(f"invalid YAML in {path}: {e}") from e
    return parse_suite(raw, default_name=path.stem)


def parse_suite(raw: Any, default_name: str = "suite") -> Suite:
    if not isinstance(raw, dict):
        raise SuiteError("suite must be a YAML mapping")

    providers = [_parse_provider(p, i) for i, p in enumerate(_require_list(raw, "providers"))]
    ids = [p.id for p in providers]
    if len(ids) != len(set(ids)):
        raise SuiteError("provider ids must be unique")

    default_prompt = raw.get("prompt")
    default_system = raw.get("system")
    tests = [
        _parse_test(t, i, default_prompt, default_system)
        for i, t in enumerate(_require_list(raw, "tests"))
    ]

    suite = Suite(name=str(raw.get("name", default_name)), providers=providers, tests=tests)
    # Render every template once so undefined variables surface before any API call.
    for test in suite.tests:
        try:
            test.render_prompt()
            test.render_system()
        except SuiteError as e:
            raise SuiteError(f"test '{test.name}': {e}") from e
    return suite


def _require_list(raw: dict[str, Any], key: str) -> list[Any]:
    value = raw.get(key)
    if not isinstance(value, list) or not value:
        raise SuiteError(f"'{key}' must be a non-empty list")
    return value


def _parse_provider(raw: Any, index: int) -> ProviderConfig:
    if not isinstance(raw, dict) or "type" not in raw:
        raise SuiteError(f"providers[{index}] must be a mapping with a 'type'")
    options = {k: v for k, v in raw.items() if k not in ("id", "type")}
    return ProviderConfig(id=str(raw.get("id", raw["type"])), type=raw["type"], options=options)


def _parse_test(
    raw: Any, index: int, default_prompt: str | None, default_system: str | None
) -> TestCase:
    if not isinstance(raw, dict):
        raise SuiteError(f"tests[{index}] must be a mapping")
    name = str(raw.get("name", f"test {index + 1}"))

    prompt = raw.get("prompt", default_prompt)
    if not isinstance(prompt, str):
        raise SuiteError(f"test '{name}': no prompt (set one on the test or at suite level)")

    variables = raw.get("vars", {})
    if not isinstance(variables, dict):
        raise SuiteError(f"test '{name}': 'vars' must be a mapping")

    asserts = [_parse_assertion(a, name) for a in raw.get("assert", [])]
    return TestCase(
        name=name,
        prompt=prompt,
        system=raw.get("system", default_system),
        vars=variables,
        asserts=asserts,
    )


def _parse_assertion(raw: Any, test_name: str) -> AssertionSpec:
    if not isinstance(raw, dict) or "type" not in raw:
        raise SuiteError(f"test '{test_name}': each assertion needs a 'type'")
    kind = raw["type"]
    if kind not in ASSERTIONS:
        known = ", ".join(sorted(ASSERTIONS))
        raise SuiteError(f"test '{test_name}': unknown assertion '{kind}' (known: {known})")
    options = {k: v for k, v in raw.items() if k not in ("type", "value")}
    return AssertionSpec(type=kind, value=raw.get("value"), options=options)
