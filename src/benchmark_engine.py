"""
Benchmarks a generated agent against the default Cursor baseline.

Metrics:
  - Accuracy: % of correct detections
  - Precision: true flags / all flags raised
  - Recall: true flags / all real issues
  - Improvement ratio vs baseline
  - Final score on 1-10,000 scale
"""

import time
from dataclasses import dataclass, field
from typing import List

from src import llm_client
from src.test_suite_builder import TestCase

# Simulated default Cursor baseline accuracy (no custom rules)
DEFAULT_CURSOR_ACCURACY = 0.65


@dataclass
class RunResult:
    total: int
    correct: int
    true_positives: int
    false_positives: int
    false_negatives: int
    elapsed_seconds: float
    accuracy: float = field(init=False)
    precision: float = field(init=False)
    recall: float = field(init=False)

    def __post_init__(self):
        self.accuracy = self.correct / self.total if self.total else 0.0
        denom_p = self.true_positives + self.false_positives
        self.precision = self.true_positives / denom_p if denom_p else 0.0
        denom_r = self.true_positives + self.false_negatives
        self.recall = self.true_positives / denom_r if denom_r else 0.0


@dataclass
class BenchmarkResults:
    custom: RunResult
    default_accuracy: float
    improvement_ratio: float
    performance_score: int
    component_scores: dict


def _evaluate_code_with_agent(
    cursorrules: str,
    test_cases: List[TestCase],
) -> RunResult:
    """Use the configured LLM + agent rules to evaluate each test case."""
    correct = 0
    true_positives = 0
    false_positives = 0
    false_negatives = 0

    start = time.time()

    for tc in test_cases:
        prompt = f"""You are acting as a Cursor AI agent with these rules:

{cursorrules[:1500]}

Evaluate the following code snippet and respond with ONLY one word:
- "pass" if the code meets all the agent's requirements
- "fail" if the code violates any of the agent's requirements

Code:
{tc.code}

Response (pass/fail):"""

        verdict = llm_client.complete(prompt, max_tokens=10, fast=True).strip().lower()

        if "pass" in verdict:
            verdict = "pass"
        elif "fail" in verdict:
            verdict = "fail"
        else:
            verdict = "fail"  # conservative default

        expected = tc.expected_result.lower()
        if verdict == expected:
            correct += 1
            if expected == "fail":
                true_positives += 1
        else:
            if verdict == "fail" and expected == "pass":
                false_positives += 1
            elif verdict == "pass" and expected == "fail":
                false_negatives += 1

    elapsed = time.time() - start
    return RunResult(
        total=len(test_cases),
        correct=correct,
        true_positives=true_positives,
        false_positives=false_positives,
        false_negatives=false_negatives,
        elapsed_seconds=elapsed,
    )


def calculate_performance_score(
    custom_accuracy: float,
    default_accuracy: float,
    elapsed_seconds: float,
    cursorrules: str,
    baseline_time_seconds: float = 28800,  # 8 hours manual
) -> tuple[int, dict]:
    """
    Map agent performance to 1-10,000 scale.

    Components:
      - Generation Quality : 3000 pts
      - Benchmark Performance: 3000 pts
      - Time Efficiency       : 2000 pts
      - Cursor Integration    : 1500 pts
      - Innovation            : 500 pts
    """
    lines = cursorrules.strip().splitlines()
    role_ok = any("role" in l.lower() for l in lines)
    examples_ok = any("example" in l.lower() for l in lines)
    checks_ok = any(
        kw in cursorrules.lower() for kw in ["must", "always", "never", "mandatory"]
    )
    format_ok = any(
        kw in cursorrules.lower() for kw in ["output", "format", "return"]
    )
    edge_ok = any(kw in cursorrules.lower() for kw in ["edge", "corner", "boundary"])

    quality_score = (
        (500 if role_ok else 200)
        + (700 if examples_ok else 300)
        + (800 if checks_ok else 400)
        + (500 if format_ok else 200)
        + (500 if edge_ok else 150)
    )
    quality_score = min(quality_score, 3000)

    improvement_ratio = max(0.0, (custom_accuracy - default_accuracy) / default_accuracy)
    benchmark_score = min(improvement_ratio * 3000, 3000)

    time_saved_ratio = max(0.0, (baseline_time_seconds - elapsed_seconds) / baseline_time_seconds)
    time_score = min(time_saved_ratio * 2000, 2000)

    integration_score = 0
    if len(lines) >= 10:
        integration_score += 500
    if any("cursor" in l.lower() for l in lines) or quality_score > 2000:
        integration_score += 300
    if "format" in cursorrules.lower():
        integration_score += 400
    if examples_ok:
        integration_score += 300
    integration_score = min(integration_score, 1500)

    innovation_score = 400 if len(lines) > 50 else 250

    components = {
        "generation_quality": int(quality_score),
        "benchmark_performance": int(benchmark_score),
        "time_efficiency": int(time_score),
        "cursor_integration": int(integration_score),
        "innovation": int(innovation_score),
    }
    total = max(1, min(sum(components.values()), 10000))
    components["total"] = total
    return total, components


def benchmark_agent(
    cursorrules: str,
    test_cases: List[TestCase],
    agent_description: str = "",
) -> BenchmarkResults:
    """
    Run the full benchmark: custom agent vs default Cursor baseline.

    Args:
        cursorrules: The .cursorrules content of the agent.
        test_cases: Test cases generated by test_suite_builder.
        agent_description: Human-readable label for reporting.

    Returns:
        BenchmarkResults with scores and component breakdown.
    """
    print(f"  Running {len(test_cases)} test cases with custom agent...")
    custom = _evaluate_code_with_agent(cursorrules, test_cases)

    improvement_ratio = max(
        0.0,
        (custom.accuracy - DEFAULT_CURSOR_ACCURACY) / DEFAULT_CURSOR_ACCURACY,
    )

    score, components = calculate_performance_score(
        custom_accuracy=custom.accuracy,
        default_accuracy=DEFAULT_CURSOR_ACCURACY,
        elapsed_seconds=custom.elapsed_seconds,
        cursorrules=cursorrules,
    )

    return BenchmarkResults(
        custom=custom,
        default_accuracy=DEFAULT_CURSOR_ACCURACY,
        improvement_ratio=improvement_ratio,
        performance_score=score,
        component_scores=components,
    )


def results_to_dict(results: BenchmarkResults) -> dict:
    """Serialize BenchmarkResults to a JSON-ready dict."""
    return {
        "custom_accuracy": round(results.custom.accuracy, 4),
        "custom_precision": round(results.custom.precision, 4),
        "custom_recall": round(results.custom.recall, 4),
        "default_accuracy": round(results.default_accuracy, 4),
        "improvement_ratio": round(results.improvement_ratio, 4),
        "improvement_percent": round(results.improvement_ratio * 100, 1),
        "performance_score": results.performance_score,
        "component_scores": results.component_scores,
        "test_cases_run": results.custom.total,
        "correct": results.custom.correct,
        "true_positives": results.custom.true_positives,
        "false_positives": results.custom.false_positives,
        "false_negatives": results.custom.false_negatives,
        "elapsed_seconds": round(results.custom.elapsed_seconds, 2),
    }
