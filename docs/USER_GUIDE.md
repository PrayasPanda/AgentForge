# User Guide: Cursor Agent Factory

## Prerequisites

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/)
- Cursor editor (to use generated agents)

## Installation

```bash
git clone https://github.com/yourusername/cursor-agent-factory
cd cursor-agent-factory
pip install -r requirements.txt
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

## Usage

### Generate an Agent

```bash
python -m src.main --create "description of the agent you want"
```

Examples:
```bash
python -m src.main --create "Python security agent that finds SQL injection and XSS"
python -m src.main --create "React component builder following Airbnb style guide"
python -m src.main --create "API testing agent for REST endpoints"
python -m src.main --create "Go performance agent that flags goroutine leaks and race conditions"
```

**What happens**:
1. Claude generates `.cursorrules` (15–60 seconds)
2. Claude generates 20 test cases (15–30 seconds)
3. Claude evaluates all test cases (60–120 seconds)
4. Files are packaged into `outputs/<agent-name>/`

**Output**:
```
outputs/python-security-agent/
  .cursorrules          ← Drop this into your project
  tests/
    test_cases.json     ← 20 test cases
    test_runner.py      ← Run with pytest
  benchmarks.json       ← Performance data
  README.md             ← Agent documentation
```

### Benchmark an Existing Agent

```bash
python -m src.main --benchmark outputs/python-security-agent
```

Re-runs the full benchmark suite and updates `benchmarks.json`.

### Self-Improve (Meta!)

```bash
python -m src.main --self-improve
```

The factory uses itself to regenerate its own `.cursorrules`. Review the diff before committing.

## Using Generated Agents in Cursor

1. Copy `.cursorrules` from the generated output to your project root:
   ```bash
   cp outputs/python-security-agent/.cursorrules /your/project/.cursorrules
   ```

2. Open the project in Cursor

3. The agent rules are automatically applied to all AI interactions (Composer, Chat, Inline Edit)

## Running Tests on Generated Agents

```bash
# Test the factory itself
pytest tests/ -v

# Test a specific generated agent
pytest outputs/python-security-agent/tests/test_runner.py -v

# Test example agents
pytest examples/security-agent/tests/ -v
```

## Troubleshooting

**`ANTHROPIC_API_KEY not set`**
- Copy `.env.example` to `.env`
- Add your key: `ANTHROPIC_API_KEY=sk-ant-...`

**`Generated rules are too short`**
- Try a more specific description
- Include domain keywords (e.g., "Python", "React", "REST API")

**`Expected at least 10 test cases`**
- Claude returned malformed JSON — re-run; it's rare but happens
- Check your API key has sufficient credits

**Generated agent scores below 7,000**
- The description may be too vague
- Try adding specifics: language, framework, what to detect

## FAQ

**Does it cost money?**
Yes — each `--create` call makes ~3 Claude API calls. Estimated cost: $0.05–0.15 per agent.

**Can I use GPT-4 instead of Claude?**
Not currently. The prompts are tuned for Claude's instruction-following. PRs welcome.

**How do I update an existing agent?**
Re-run `--create` with the same description. It overwrites the output directory.

**What's the max score possible?**
10,000. The factory itself scores 9,450.
