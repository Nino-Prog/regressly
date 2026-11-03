# Roadmap

A four-month plan. Each month ends with a tagged release and a short write-up
(blog post or README section) on what was learned.

## Month 1: Core runner (v0.1 → v0.2)

Goal: a tool you can point at a YAML file and trust.

- [x] YAML suite format with variables and per-test prompt/system overrides
- [x] Provider interface + Anthropic provider + offline `echo` provider
- [x] Deterministic assertions: contains, not-contains, equals, regex, length, json-valid
- [x] Concurrent async runner with per-test timing and token usage
- [x] CLI (`run`, `validate`), terminal report, JSON output, CI-friendly exit codes
- [x] Unit tests + GitHub Actions CI
- [ ] `json-schema` assertion
- [ ] OpenAI-compatible provider (OpenAI, Ollama, vLLM, LM Studio)
- [ ] Response cache on disk, keyed by (provider, model, prompt), so re-runs are free
- [ ] Retries with backoff and a clear error state, separate from "failed"
- [ ] Publish v0.2 to PyPI

## Month 2: Smarter assertions (v0.3 → v0.4)

Goal: test behavior that string matching can't express.

- [ ] `llm-judge`: grade the output against a rubric with a grader model, returning a score and reasoning
- [ ] `similar`: embedding similarity to a reference answer, with a threshold
- [ ] Custom Python assertions (`type: python`, `path: checks.py:is_polite`)
- [ ] Multiple providers per suite with a side-by-side comparison table
- [ ] Cost tracking per run, using token usage × model pricing
- [ ] Repeat each test N times and report pass *rates* (LLMs are nondeterministic)

## Month 3: Regression detection & CI (v0.5 → v0.6)

Goal: the reason the project is called regressly.

- [ ] `regressly snapshot`: save a run as the baseline
- [ ] `regressly diff`: compare a run to the baseline (newly failing, newly passing, score drift)
- [ ] Statistical check for flaky tests, so a single unlucky sample isn't treated as a regression
- [ ] GitHub Action: run suites on PRs that touch prompts and post a results comment
- [ ] JUnit XML output for other CI systems

## Month 4: Polish & launch (v1.0)

Goal: something other people adopt.

- [ ] Static HTML report (one file, shareable) with per-test drill-down and history charts
- [ ] Generate test cases from a few examples with an LLM, then review them by hand
- [ ] Plugin entry points for third-party providers and assertions
- [ ] Docs site (MkDocs), three real-world example suites, and a demo GIF
- [ ] v1.0 release, launch post, and submissions to newsletters and Hacker News

## Stretch ideas

- Agent/tool-use testing: assert on which tools were called and with what arguments
- Red-team pack: prompt-injection and jailbreak test suites you can drop in
- VS Code extension that runs the suite for the open YAML file
