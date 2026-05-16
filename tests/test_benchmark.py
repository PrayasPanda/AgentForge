"""
Unit tests for benchmark_engine.py — validates scoring logic without API calls.
"""

import pytest
from src.benchmark_engine import calculate_performance_score, results_to_dict, BenchmarkResults, RunResult


SAMPLE_CURSORRULES = """## ROLE
You are a security expert agent.

## MANDATORY CHECKS
You MUST always check for SQL injection.
You MUST NEVER allow hardcoded secrets.

## EXAMPLES
Good example: parameterized query
Bad example: f-string in SQL

## OUTPUT FORMAT
Return STATUS: PASS or FAIL with EXPLANATION.
"""


class TestCalculatePerformanceScore:
    def test_score_in_valid_range(self):
        score, _ = calculate_performance_score(0.94, 0.65, 300, SAMPLE_CURSORRULES)
        assert 1 <= score <= 10000

    def test_high_accuracy_gives_high_score(self):
        score_high, _ = calculate_performance_score(0.95, 0.65, 300, SAMPLE_CURSORRULES)
        score_low, _ = calculate_performance_score(0.70, 0.65, 300, SAMPLE_CURSORRULES)
        assert score_high > score_low

    def test_faster_time_gives_higher_time_score(self):
        _, comp_fast = calculate_performance_score(0.90, 0.65, 60, SAMPLE_CURSORRULES)
        _, comp_slow = calculate_performance_score(0.90, 0.65, 7200, SAMPLE_CURSORRULES)
        assert comp_fast["time_efficiency"] > comp_slow["time_efficiency"]

    def test_components_sum_to_total(self):
        score, components = calculate_performance_score(0.90, 0.65, 300, SAMPLE_CURSORRULES)
        expected = (
            components["generation_quality"]
            + components["benchmark_performance"]
            + components["time_efficiency"]
            + components["cursor_integration"]
            + components["innovation"]
        )
        assert components["total"] == expected

    def test_score_never_exceeds_10000(self):
        score, _ = calculate_performance_score(1.0, 0.01, 1, SAMPLE_CURSORRULES)
        assert score <= 10000

    def test_score_never_below_1(self):
        score, _ = calculate_performance_score(0.0, 0.99, 86400, "")
        assert score >= 1

    def test_improvement_ratio_zero_when_no_improvement(self):
        _, comp = calculate_performance_score(0.65, 0.65, 300, SAMPLE_CURSORRULES)
        assert comp["benchmark_performance"] == 0

    def test_component_keys_present(self):
        _, comp = calculate_performance_score(0.90, 0.65, 300, SAMPLE_CURSORRULES)
        expected_keys = {
            "generation_quality", "benchmark_performance",
            "time_efficiency", "cursor_integration", "innovation", "total"
        }
        assert expected_keys == set(comp.keys())


class TestResultsToDict:
    def _make_results(self):
        custom = RunResult(
            total=20, correct=18, true_positives=9,
            false_positives=1, false_negatives=1, elapsed_seconds=45.2
        )
        return BenchmarkResults(
            custom=custom,
            default_accuracy=0.65,
            improvement_ratio=0.35,
            performance_score=8500,
            component_scores={
                "generation_quality": 2700,
                "benchmark_performance": 2200,
                "time_efficiency": 1950,
                "cursor_integration": 1350,
                "innovation": 300,
                "total": 8500,
            },
        )

    def test_dict_has_all_required_keys(self):
        results = self._make_results()
        d = results_to_dict(results)
        required = {
            "custom_accuracy", "custom_precision", "custom_recall",
            "default_accuracy", "improvement_ratio", "improvement_percent",
            "performance_score", "component_scores", "test_cases_run",
            "correct", "true_positives", "false_positives", "false_negatives",
            "elapsed_seconds",
        }
        assert required.issubset(set(d.keys()))

    def test_accuracy_computed_correctly(self):
        results = self._make_results()
        d = results_to_dict(results)
        assert d["custom_accuracy"] == pytest.approx(18 / 20, abs=0.001)

    def test_improvement_percent_is_ratio_times_100(self):
        results = self._make_results()
        d = results_to_dict(results)
        assert d["improvement_percent"] == pytest.approx(35.0, abs=0.01)

    def test_performance_score_matches(self):
        results = self._make_results()
        d = results_to_dict(results)
        assert d["performance_score"] == 8500


class TestRunResult:
    def test_accuracy_calculation(self):
        r = RunResult(total=10, correct=8, true_positives=4,
                      false_positives=0, false_negatives=1, elapsed_seconds=5.0)
        assert r.accuracy == pytest.approx(0.8)

    def test_precision_calculation(self):
        r = RunResult(total=10, correct=8, true_positives=4,
                      false_positives=1, false_negatives=0, elapsed_seconds=5.0)
        assert r.precision == pytest.approx(4 / 5)

    def test_recall_calculation(self):
        r = RunResult(total=10, correct=8, true_positives=4,
                      false_positives=0, false_negatives=2, elapsed_seconds=5.0)
        assert r.recall == pytest.approx(4 / 6)

    def test_zero_total_does_not_raise(self):
        r = RunResult(total=0, correct=0, true_positives=0,
                      false_positives=0, false_negatives=0, elapsed_seconds=0.0)
        assert r.accuracy == 0.0
