import pytest

from regressly.assertions import evaluate, strip_code_fence


@pytest.mark.parametrize(
    "kind, output, value, options, expected",
    [
        ("contains", "Refunds within 30 Days.", "30 days", {}, True),
        ("contains", "Refunds within 30 Days.", "30 days", {"case_sensitive": True}, False),
        ("not-contains", "hello", "bye", {}, True),
        ("not-contains", "hello bye", "BYE", {}, False),
        ("equals", "  Paris\n", "paris", {}, True),
        ("equals", "Paris, France", "Paris", {}, False),
        ("regex", "order #1234", r"#\d{4}", {}, True),
        ("regex", "SORRY", "sorry", {}, False),
        ("regex", "SORRY", "sorry", {"case_sensitive": False}, True),
        ("max-length", "abc", 3, {}, True),
        ("max-length", "abcd", 3, {}, False),
        ("min-length", "abc", 4, {}, False),
        ("json-valid", '{"a": 1}', None, {}, True),
        ("json-valid", '```json\n{"a": 1}\n```', None, {}, True),
        ("json-valid", "Sure! {\"a\": 1}", None, {}, False),
    ],
)
def test_assertions(kind, output, value, options, expected):
    assert evaluate(kind, output, value, options).passed is expected


def test_failure_message_shows_output_preview():
    result = evaluate("contains", "the quick brown fox", "dog", {})
    assert not result.passed
    assert "the quick brown fox" in result.message


def test_bad_config_fails_instead_of_crashing():
    result = evaluate("regex", "text", "(unclosed", {})
    assert not result.passed
    assert result.message.startswith("error:")


def test_strip_code_fence_leaves_plain_text_alone():
    assert strip_code_fence('{"a": 1}') == '{"a": 1}'
