# Architecture: Cursor Agent Factory

## System Overview

Cursor Agent Factory is a CLI tool that generates production-ready Cursor AI agents from natural language descriptions. It orchestrates four independent modules through a single entry point.

```
User Input (description)
        │
        ▼
┌─────────────────┐
│   src/main.py   │  CLI + orchestrator
└────────┬────────┘
         │
    ┌────┴────────────────────────────────┐
    │                                     │
    ▼                                     ▼
┌──────────────────┐         ┌───────────────────────┐
│ agent_generator  │         │  test_suite_builder   │
│                  │         │                       │
│ Claude API call  │         │ Claude API call       │
│ → .cursorrules   │         │ → 20 TestCase objects │
└────────┬─────────┘         └──────────┬────────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌──────────────────┐
         │ benchmark_engine │
         │                  │
         │ Runs test cases  │
         │ with Claude as   │
         │ agent evaluator  │
         │ → BenchmarkResult│
         └────────┬─────────┘
                  │
                  ▼
         ┌──────────────────┐
         │    packager      │
         │                  │
         │ Writes all files │
         │ to outputs/<slug>│
         └──────────────────┘
```

## Module Responsibilities

### `src/main.py`
- Parses CLI arguments (`--create`, `--benchmark`, `--self-improve`)
- Orchestrates the pipeline: generator → test builder → benchmark → packager
- Prints progress and timing to stdout

### `src/agent_generator.py`
- Wraps the Anthropic Claude API (`claude-sonnet-4-6`)
- Constructs a domain-aware prompt that produces structured `.cursorrules`
- Validates: minimum length, required sections (role, checks, examples), strips markdown fences

### `src/test_suite_builder.py`
- Uses Claude to generate 20 test cases from the agent's rules
- Produces 8 positive, 8 negative, 4 edge cases in JSON format
- Deserializes into typed `TestCase` dataclasses

### `src/benchmark_engine.py`
- Uses Claude Haiku (fast, cheap) as an agent evaluator
- Sends each test case to Claude with the `.cursorrules` as context
- Records correct/incorrect, TP/FP/FN counts
- Computes 5-component performance score (1–10,000 scale)

### `src/packager.py`
- Creates `outputs/<slug>/` directory
- Writes `.cursorrules`, `tests/test_cases.json`, `tests/test_runner.py`, `benchmarks.json`, `README.md`
- Generates agent-specific README from benchmark data

## Data Flow

```
str (description)
  → generate_cursorrules() → str (.cursorrules content)
  → build_test_suite()     → List[TestCase]
  → benchmark_agent()      → BenchmarkResults
  → package_agent()        → str (output directory path)
```

## External Dependencies

| Dependency | Purpose |
|-----------|---------|
| `anthropic` | Claude API client |
| `python-dotenv` | Load ANTHROPIC_API_KEY from .env |
| `pytest` | Run test suites |

## Models Used

| Task | Model | Reason |
|------|-------|--------|
| `.cursorrules` generation | `claude-sonnet-4-6` | High quality, nuanced rules |
| Test case generation | `claude-sonnet-4-6` | Creative, domain-aware cases |
| Test case evaluation | `claude-haiku-4-5-20251001` | Fast, cheap for 20 binary decisions |

## Security Design

- API key loaded exclusively from `.env` (never in source)
- `.gitignore` excludes `.env` and `outputs/`
- No secrets logged or written to disk
- `outputs/` excluded from git to prevent accidental agent data commits
