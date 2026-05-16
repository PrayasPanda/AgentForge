"""
Integration tests — verify the full pipeline works end-to-end.
These tests use real files (examples/) but do NOT call the Claude API.
"""

import json
import os
import pytest

EXAMPLES_DIR = os.path.join(os.path.dirname(__file__), "..", "examples")
EXAMPLE_AGENTS = ["security-agent", "react-component-agent", "api-testing-agent"]


@pytest.mark.parametrize("agent", EXAMPLE_AGENTS)
class TestExampleAgentStructure:
    def test_cursorrules_exists(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, ".cursorrules")
        assert os.path.exists(path), f".cursorrules missing for {agent}"

    def test_cursorrules_not_empty(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, ".cursorrules")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert len(content.strip()) > 100, f".cursorrules too short for {agent}"

    def test_cursorrules_has_role(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, ".cursorrules")
        with open(path, encoding="utf-8") as f:
            content = f.read().lower()
        assert "role" in content

    def test_cursorrules_has_examples(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, ".cursorrules")
        with open(path, encoding="utf-8") as f:
            content = f.read().lower()
        assert "example" in content

    def test_benchmarks_json_exists(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "benchmarks.json")
        assert os.path.exists(path), f"benchmarks.json missing for {agent}"

    def test_benchmarks_json_valid(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "benchmarks.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert "performance_score" in data
        assert "custom_accuracy" in data
        assert "default_accuracy" in data
        assert 1 <= data["performance_score"] <= 10000
        assert 0.0 <= data["custom_accuracy"] <= 1.0

    def test_benchmarks_custom_beats_default(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "benchmarks.json")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["custom_accuracy"] > data["default_accuracy"], (
            f"{agent}: custom accuracy {data['custom_accuracy']} should exceed "
            f"default {data['default_accuracy']}"
        )

    def test_test_cases_json_exists(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "tests", "test_cases.json")
        assert os.path.exists(path), f"test_cases.json missing for {agent}"

    def test_test_cases_minimum_count(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "tests", "test_cases.json")
        with open(path, encoding="utf-8") as f:
            cases = json.load(f)
        assert len(cases) >= 10, f"{agent}: need >= 10 test cases, got {len(cases)}"

    def test_test_cases_have_both_pass_and_fail(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "tests", "test_cases.json")
        with open(path, encoding="utf-8") as f:
            cases = json.load(f)
        results = {c["expected_result"] for c in cases}
        assert "pass" in results, f"{agent}: no passing test cases"
        assert "fail" in results, f"{agent}: no failing test cases"

    def test_test_cases_valid_structure(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "tests", "test_cases.json")
        with open(path, encoding="utf-8") as f:
            cases = json.load(f)
        for i, tc in enumerate(cases):
            assert "code" in tc, f"{agent} case {i}: missing 'code'"
            assert "expected_result" in tc, f"{agent} case {i}: missing 'expected_result'"
            assert tc["expected_result"] in ("pass", "fail"), f"{agent} case {i}: bad expected_result"
            assert "reason" in tc, f"{agent} case {i}: missing 'reason'"
            assert len(tc["code"].strip()) > 0, f"{agent} case {i}: empty code"

    def test_readme_exists(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "README.md")
        assert os.path.exists(path), f"README.md missing for {agent}"

    def test_readme_mentions_score(self, agent):
        path = os.path.join(EXAMPLES_DIR, agent, "README.md")
        with open(path, encoding="utf-8") as f:
            content = f.read()
        assert "10,000" in content or "10000" in content, f"{agent} README missing score"


class TestPackagerSlugify:
    def test_slugify_basic(self):
        from src.packager import _slugify
        assert _slugify("Python Security Agent") == "python-security-agent"

    def test_slugify_strips_special_chars(self):
        from src.packager import _slugify
        result = _slugify("API testing agent (v2)!")
        assert "(" not in result
        assert "!" not in result

    def test_slugify_max_length(self):
        from src.packager import _slugify
        long = "a" * 200
        assert len(_slugify(long)) <= 60

    def test_slugify_no_leading_trailing_dash(self):
        from src.packager import _slugify
        result = _slugify("  agent  ")
        assert not result.startswith("-")
        assert not result.endswith("-")


class TestBenchmarkScoringIntegration:
    def test_example_agents_have_score_above_8000(self):
        for agent in EXAMPLE_AGENTS:
            path = os.path.join(EXAMPLES_DIR, agent, "benchmarks.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            assert data["performance_score"] >= 8000, (
                f"{agent} score {data['performance_score']} should be >= 8000"
            )

    def test_component_scores_sum_to_total(self):
        for agent in EXAMPLE_AGENTS:
            path = os.path.join(EXAMPLES_DIR, agent, "benchmarks.json")
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            comp = data["component_scores"]
            expected_total = (
                comp["generation_quality"]
                + comp["benchmark_performance"]
                + comp["time_efficiency"]
                + comp["cursor_integration"]
                + comp["innovation"]
            )
            assert comp["total"] == expected_total, (
                f"{agent}: component scores don't sum to total"
            )
