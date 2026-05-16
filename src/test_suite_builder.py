"""
Auto-generates test suites for a given agent.

Generates:
  - Positive cases (agent should approve/pass)
  - Negative cases (agent should flag/fail)
  - Edge cases (boundary conditions)
"""

import json
import re
from dataclasses import dataclass
from typing import List

from src import llm_client


@dataclass
class TestCase:
    code: str
    expected_result: str  # "pass" or "fail"
    reason: str
    category: str  # "positive", "negative", "edge"


def _build_test_prompt(agent_type: str, cursorrules: str) -> str:
    return f"""You are a QA engineer creating test cases for a Cursor AI agent.

Agent description: {agent_type}

Agent rules:
{cursorrules[:2000]}

Generate exactly 20 test cases in this JSON format:
{{
  "test_cases": [
    {{
      "code": "...",
      "expected_result": "pass",
      "reason": "...",
      "category": "positive"
    }},
    ...
  ]
}}

Requirements:
- 8 positive cases: code that SHOULD pass the agent's checks (well-written, safe, correct)
- 8 negative cases: code that SHOULD fail the agent's checks (has issues the agent targets)
- 4 edge cases: boundary conditions, ambiguous situations

Keep code snippets short (5-20 lines). Make reasons specific and actionable.
Return ONLY valid JSON, no markdown, no explanation."""


def _parse_test_cases(raw_json: str) -> List[TestCase]:
    """Extract and parse test cases from LLM response."""
    raw_json = re.sub(r"^```[a-z]*\n?", "", raw_json.strip(), flags=re.MULTILINE)
    raw_json = re.sub(r"\n?```$", "", raw_json.strip(), flags=re.MULTILINE)

    data = json.loads(raw_json)
    cases = []
    for item in data.get("test_cases", []):
        cases.append(
            TestCase(
                code=item.get("code", ""),
                expected_result=item.get("expected_result", "pass"),
                reason=item.get("reason", ""),
                category=item.get("category", "positive"),
            )
        )
    return cases


def build_test_suite(agent_type: str, cursorrules: str) -> List[TestCase]:
    """
    Generate 20 test cases for the given agent.

    Args:
        agent_type: Natural language description of the agent.
        cursorrules: The generated .cursorrules content.

    Returns:
        List of TestCase objects (8 positive, 8 negative, 4 edge).
    """
    prompt = _build_test_prompt(agent_type, cursorrules)
    raw = llm_client.complete(prompt, max_tokens=4096)
    cases = _parse_test_cases(raw)

    if len(cases) < 10:
        raise ValueError(
            f"Expected at least 10 test cases, got {len(cases)}. "
            "LLM may have returned malformed JSON."
        )

    return cases


def test_cases_to_dict(cases: List[TestCase]) -> list:
    """Serialize test cases to a list of dicts for JSON output."""
    return [
        {
            "code": tc.code,
            "expected_result": tc.expected_result,
            "reason": tc.reason,
            "category": tc.category,
        }
        for tc in cases
    ]
