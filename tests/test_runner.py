import json

from regressly.cli import main
from regressly.providers import Completion, Provider, ProviderError
from regressly.providers.echo import EchoProvider
from regressly.runner import Status, run_suite
from regressly.suite import parse_suite

SUITE = {
    "name": "demo",
    "providers": [{"type": "echo"}],
    "prompt": "{{q}}",
    "tests": [
        {"name": "pass", "vars": {"q": "hi"}, "assert": [{"type": "contains", "value": "hi"}]},
        {"name": "fail", "vars": {"q": "hi"}, "assert": [{"type": "contains", "value": "bye"}]},
    ],
}


class Broken(Provider):
    async def complete(self, prompt, system=None):
        raise ProviderError("boom")


class Refuses(Provider):
    async def complete(self, prompt, system=None):
        return Completion(text="", stop_reason="refusal")


async def test_passes_and_fails_are_reported():
    run = await run_suite(parse_suite(SUITE))
    statuses = {r.test: r.status for r in run.results}
    assert statuses == {"pass": Status.PASSED, "fail": Status.FAILED}
    assert not run.ok


async def test_provider_errors_are_errors_not_failures():
    run = await run_suite(parse_suite(SUITE), providers=[Broken("b", {})])
    assert all(r.status is Status.ERROR and r.error == "boom" for r in run.results)


async def test_refusal_fails_even_without_assertions():
    suite = parse_suite({**SUITE, "tests": [{"vars": {"q": "x"}}]})
    run = await run_suite(suite, providers=[Refuses("r", {})])
    assert run.results[0].status is Status.FAILED
    assert run.results[0].assertions[0].type == "refusal"


async def test_every_provider_runs_every_test():
    providers = [EchoProvider("a", {}), EchoProvider("b", {})]
    run = await run_suite(parse_suite(SUITE), providers=providers)
    assert len(run.results) == 4
    assert {r.provider for r in run.results} == {"a", "b"}


def test_cli_exit_codes_and_json(tmp_path):
    out = tmp_path / "results.json"
    assert main(["run", "examples/offline.yaml", "--json", str(out)]) == 0
    data = json.loads(out.read_text())
    assert data["summary"] == {"passed": 2, "failed": 0, "error": 0}

    bad = tmp_path / "bad.yaml"
    bad.write_text("tests: []")
    assert main(["validate", str(bad)]) == 2


def test_cli_returns_1_on_failure(tmp_path):
    suite = tmp_path / "s.yaml"
    suite.write_text(json.dumps(SUITE))  # JSON is valid YAML
    assert main(["run", str(suite)]) == 1


def test_report_escapes_markup_in_output(capsys):
    from rich.console import Console

    from regressly.report import print_run
    from regressly.runner import RunResult, TestResult

    result = TestResult("t [x]", "p", Status.FAILED, output="[red]not markup[/]")
    print_run(RunResult("s", [result], 1.0), Console(force_terminal=False))
    assert "[red]not markup[/]" in capsys.readouterr().out


async def test_missing_credentials_is_a_clean_error(monkeypatch):
    from regressly.providers.anthropic import AnthropicProvider

    provider = AnthropicProvider("c", {})

    async def no_credentials(**params):
        raise TypeError('"Could not resolve authentication method. Expected one of api_key"')

    monkeypatch.setattr(provider._client.messages, "create", no_credentials)
    run = await run_suite(parse_suite(SUITE), providers=[provider])
    assert all(r.status is Status.ERROR for r in run.results)
    assert "credentials" in run.results[0].error
