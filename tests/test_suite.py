import pytest

from regressly.suite import SuiteError, load_suite, parse_suite


def minimal(**overrides):
    raw = {
        "providers": [{"type": "echo"}],
        "prompt": "Hi {{name}}",
        "tests": [{"vars": {"name": "Ada"}, "assert": [{"type": "contains", "value": "Ada"}]}],
    }
    raw.update(overrides)
    return raw


def test_parses_minimal_suite():
    suite = parse_suite(minimal())
    assert suite.providers[0].id == "echo"
    assert suite.tests[0].name == "test 1"
    assert suite.tests[0].render_prompt() == "Hi Ada"


def test_test_level_prompt_and_system_override_suite_level():
    suite = parse_suite(minimal(
        system="Be {{tone}}",
        tests=[{"prompt": "Yo {{name}}", "system": "Be terse", "vars": {"name": "Bo"}}],
    ))
    test = suite.tests[0]
    assert test.render_prompt() == "Yo Bo"
    assert test.render_system() == "Be terse"


def test_provider_options_are_collected():
    suite = parse_suite(minimal(providers=[{"id": "c", "type": "anthropic", "model": "m"}]))
    assert suite.providers[0].options == {"model": "m"}


@pytest.mark.parametrize(
    "overrides, message",
    [
        ({"providers": []}, "'providers' must be a non-empty list"),
        ({"tests": []}, "'tests' must be a non-empty list"),
        ({"prompt": None}, "no prompt"),
        ({"tests": [{"vars": {}}]}, "undefined variable 'name'"),
        ({"tests": [{"vars": {"name": "x"}, "assert": [{"type": "vibes"}]}]}, "unknown assertion"),
        ({"providers": [{"type": "echo"}, {"type": "echo"}]}, "unique"),
    ],
)
def test_invalid_suites_raise(overrides, message):
    with pytest.raises(SuiteError, match=message):
        parse_suite(minimal(**overrides))


def test_load_suite_reports_missing_file(tmp_path):
    with pytest.raises(SuiteError, match="not found"):
        load_suite(tmp_path / "nope.yaml")


def test_example_suites_are_valid():
    load_suite("examples/offline.yaml")
    load_suite("examples/support-bot.yaml")
