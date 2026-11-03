# regressly

**Regression tests for LLM prompts.** Write test cases in YAML, run them against
real models, and fail CI when a prompt or model change breaks behavior you care about.

```bash
regressly run examples/support-bot.yaml
```

```
 support-bot · claude
 ✓ refund window is mentioned          812 ms
 ✓ stays polite when user is rude      1.1 s
 ✗ answers in JSON when asked          640 ms
     json-valid: output is not valid JSON (Expecting value: line 1 column 1)
 2 passed · 1 failed · 2.6 s
```

## Why

Prompts are code, but most teams "test" them by eyeballing a few outputs. Change a
system prompt, swap a model version, or tweak temperature, and something three features
away quietly breaks. regressly treats prompts like any other code under test:

- **Declarative suites.** Prompts, variables and assertions live in version-controlled YAML.
- **Real assertions.** Contains, regex, JSON validity, length limits, and more on the way
  (LLM-as-judge, semantic similarity, JSON Schema).
- **CI-native.** Non-zero exit code on failure and machine-readable JSON results.
- **Fast.** Test cases run concurrently.

## Install

```bash
pip install -e ".[dev]"     # from a clone, until the first PyPI release
export ANTHROPIC_API_KEY=... # or `ant auth login`
```

## Writing a suite

```yaml
name: support-bot

providers:
  - id: claude
    type: anthropic
    model: claude-opus-5-5
    max_tokens: 1024

system: |
  You are a friendly support agent for Acme. Refunds are accepted within 30 days.

prompt: "{{question}}"

tests:
  - name: refund window is mentioned
    vars:
      question: Can I return my order from last week?
    assert:
      - type: contains
        value: 30 days
      - type: max-length
        value: 800

  - name: answers in JSON when asked
    prompt: 'Reply ONLY with JSON {"answer": ...}: {{question}}'
    vars:
      question: What is your refund window?
    assert:
      - type: json-valid
```

A test can override `prompt` and `system`. `{{var}}` placeholders are filled from `vars`.

### Assertions (v0.1)

| type             | passes when                                     |
|------------------|-------------------------------------------------|
| `contains`       | output contains `value` (`case_sensitive: false` by default) |
| `not-contains`   | output does not contain `value`                 |
| `equals`         | output (trimmed) equals `value`                 |
| `regex`          | `value` matches somewhere in the output          |
| `max-length`     | output is at most `value` characters long        |
| `min-length`     | output is at least `value` characters long       |
| `json-valid`     | output parses as JSON (code fences are stripped) |

### Providers (v0.1)

| type        | notes                                                   |
|-------------|---------------------------------------------------------|
| `anthropic` | Claude via the official SDK. Options: `model`, `max_tokens`, `effort` |
| `echo`      | Returns the rendered prompt. Useful for offline tests and demos |

## CLI

```bash
regressly run SUITE.yaml [--concurrency 8] [--json results.json] [--provider claude]
regressly validate SUITE.yaml   # check a suite without calling any model
```

Exit codes: `0` all passed, `1` at least one test failed, `2` invalid suite or usage error.

## Roadmap

See [ROADMAP.md](ROADMAP.md). The short version: deterministic assertions first, then
LLM-graded assertions, then regression detection against baselines with a GitHub Action
that comments on PRs.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```

## License

MIT
