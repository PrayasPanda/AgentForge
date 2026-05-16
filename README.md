# Cursor Agent Factory

> Automate the creation of production-ready Cursor AI agents — from idea to fully benchmarked agent in under 5 minutes.

---

## What Is This?

**Cursor Agent Factory** is a Python-based automation tool that generates, tests, benchmarks, and packages custom AI agents for the [Cursor](https://cursor.sh) code editor.

Instead of manually spending 7–10 hours writing `.cursorrules` files, designing test cases, and measuring performance, this tool does all of it automatically — you just describe what you want in plain English.

---

## The Problem It Solves

Building a high-quality Cursor agent manually requires:

| Task | Time |
| ---- | ---- |
| Research domain best practices | 2–3 hours |
| Write `.cursorrules` by hand | 3–4 hours |
| Design test cases | 1–2 hours |
| Benchmark against baseline | 1 hour |
| **Total** | **7–10 hours per agent** |

For teams building multiple specialized agents, this becomes a serious bottleneck.

---

## How It Works

One command does everything:

```bash
python -m src.main --create "security agent for Python"
```

```text
🔍 Analyzing requirements: 'security agent for Python'
🤖 Generating .cursorrules...
✅ Rules generated (52 lines)
🧪 Creating test suite...
✅ 20 test cases created
📊 Benchmarking vs default Cursor...
   Default accuracy : 65%
   Custom accuracy  : 94%
   Improvement      : +44.6%
   Score            : 9300/10,000
📦 Packaging agent...
✅ Agent ready at: outputs/security-agent-for-python/
⏱️  Total time: 4m 37s
```

### Under the Hood

1. **Requirement Analysis** — Parses your natural language description to understand the agent's domain and goals
2. **Rule Generation** — Calls an LLM to write an optimized `.cursorrules` file with roles, mandatory checks, heuristics, and examples
3. **Test Suite Builder** — Auto-generates 20 test cases across positive, negative, and edge case scenarios
4. **Benchmark Engine** — Scores the custom agent against the default Cursor baseline on a 1–10,000 scale
5. **Packager** — Bundles `.cursorrules`, tests, benchmark data, and documentation into one ready-to-use directory

---

## Architecture

The factory is a modular pipeline — each stage is independent and can be run separately.

```text
User Input (plain English description)
         │
         ▼
┌─────────────────┐
│   src/main.py   │  ← CLI + orchestrator
└────────┬────────┘
         │
    ┌────┴──────────────────────────────────┐
    │                                       │
    ▼                                       ▼
┌──────────────────┐           ┌───────────────────────┐
│ agent_generator  │           │  test_suite_builder   │
│                  │           │                       │
│ LLM call         │           │ LLM call              │
│ → .cursorrules   │           │ → 20 test cases       │
└────────┬─────────┘           └──────────┬────────────┘
         │                                │
         └──────────────┬─────────────────┘
                        │
                        ▼
           ┌────────────────────┐
           │  benchmark_engine  │
           │                    │
           │ Runs each test case│
           │ through the agent  │
           │ → accuracy score   │
           └──────────┬─────────┘
                      │
                      ▼
           ┌────────────────────┐
           │     packager       │
           │                    │
           │ Bundles all output │
           │ → outputs/<name>/  │
           └────────────────────┘
```

### Module Breakdown

| Module | Responsibility |
| ------ | -------------- |
| `main.py` | CLI entry point, orchestrates the full pipeline |
| `agent_generator.py` | Builds a domain-aware prompt and calls the LLM to produce `.cursorrules` |
| `test_suite_builder.py` | Generates 20 typed test cases (8 positive, 8 negative, 4 edge) |
| `benchmark_engine.py` | Evaluates each test case and scores on a 1–10,000 scale |
| `llm_client.py` | Unified client supporting Anthropic, Gemini, and Ollama |
| `packager.py` | Writes `.cursorrules`, test cases, benchmark JSON, and README to disk |

---

## Performance

### Factory Self-Score: 9,450 / 10,000

| Metric | Manual Process | Cursor Agent Factory | Default Cursor |
| ------ | -------------- | -------------------- | -------------- |
| Creation time | 7 hours | **5 minutes** | N/A |
| Accuracy | 79% | **94%** | 65% |
| Consistency | Variable | **Standardized** | Variable |
| Speed improvement | 1× | **89×** | N/A |

---

## Tech Stack

- **Language**: Python 3.12
- **LLM Providers**: Anthropic Claude, Google Gemini, Ollama (local & cloud)
- **Testing**: pytest
- **Key Libraries**: `anthropic`, `openai`, `python-dotenv`
- **Architecture**: Modular pipeline — generator → test builder → benchmark engine → packager

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/yourusername/cursor-agent-factory
cd cursor-agent-factory
pip install -r requirements.txt
```

### 2. Configure Your LLM Provider

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

#### Option A — Google Gemini (recommended, free tier available)

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-3.1-flash-lite
```

#### Option B — Anthropic Claude

```env
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
```

#### Option C — Ollama (fully local, no API key needed)

```env
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=llama3.2
```

### 3. Generate Your First Agent

```bash
# Create a new agent from a description
python -m src.main --create "React component builder following Airbnb style guide"

# Benchmark an existing agent
python -m src.main --benchmark outputs/react-component-builder

# Run the factory's self-improvement loop
python -m src.main --self-improve
```

---

## Example Agents

Three pre-built agents are included in `examples/` to demonstrate output quality:

| Agent | What It Does |
| ----- | ------------ |
| `security-agent` | Detects SQL injection, XSS, and hardcoded secrets in Python |
| `react-component-agent` | Enforces Airbnb React/JSX coding standards |
| `api-testing-agent` | Generates comprehensive API test suites |

Each comes with `.cursorrules`, test cases, benchmark results, and a README.

---

## Project Structure

```text
cursor-agent-factory/
├── src/
│   ├── main.py                 # CLI entry point
│   ├── agent_generator.py      # LLM-powered .cursorrules generation
│   ├── test_suite_builder.py   # Automated test case generation
│   ├── benchmark_engine.py     # Performance scoring (1–10,000 scale)
│   ├── llm_client.py           # Unified multi-provider LLM client
│   ├── packager.py             # Output bundler
│   └── templates/              # Base file templates
├── examples/                   # 3 pre-generated sample agents
├── tests/                      # Unit + integration test suite
├── benchmarks/                 # Baseline & comparison data
├── docs/                       # Architecture, scoring methodology, proof
├── .env.example                # Environment variable template
└── .cursorrules                # Meta: rules the factory uses on itself
```

---

## Running Tests

```bash
# Full test suite (no API key required)
pytest tests/ -v

# Core unit tests only
pytest tests/test_generator.py tests/test_benchmark.py -v

# Integration tests — verifies example agents are valid
pytest tests/integration_test.py -v
```

---

## The Meta Twist

This factory built itself through recursive self-improvement:

- **v0** — Hand-coded from scratch (8 hours)
- **v1** — Generated by v0, added the test builder and benchmark engine
- **v2** — Generated by v1, added self-improvement loop and packaging system (current)

Full write-up: [`docs/RECURSIVE_PROOF.md`](docs/RECURSIVE_PROOF.md)

---

## Documentation

| Document | Description |
| -------- | ----------- |
| [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) | System design and component overview |
| [`docs/SCORING_METHODOLOGY.md`](docs/SCORING_METHODOLOGY.md) | How the 1–10,000 benchmark score is calculated |
| [`docs/BENCHMARK_RESULTS.md`](docs/BENCHMARK_RESULTS.md) | Detailed performance comparison data |
| [`docs/USER_GUIDE.md`](docs/USER_GUIDE.md) | End-to-end usage walkthrough |
| [`docs/RECURSIVE_PROOF.md`](docs/RECURSIVE_PROOF.md) | Story of the self-improvement process |

---

## License

MIT
