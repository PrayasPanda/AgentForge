"""
Test runner template for generated agents.
Populated by packager.py — run with: pytest tests/
"""

import json
import os
import pytest

TEST_CASES_PATH = os.path.join(os.path.dirname(__file__), "test_cases.json")


def load_test_cases():
    with open(TEST_CASES_PATH) as f:
        return json.load(f)


@pytest.mark.parametrize("tc", load_test_cases())
def test_case_structure(tc):
    """Every test case must have required fields with valid values."""
    assert "code" in tc
    assert "expected_result" in tc
    assert tc["expected_result"] in ("pass", "fail")
    assert "reason" in tc
    assert len(tc["code"].strip()) >= 10


@pytest.mark.parametrize("tc", load_test_cases())
def test_case_has_reason(tc):
    """Every test case must explain why it passes or fails."""
    assert len(tc["reason"].strip()) >= 10, f"Reason too short: {tc['reason']!r}"


def test_suite_has_both_pass_and_fail():
    """Suite must contain both pass and fail cases."""
    cases = load_test_cases()
    results = {tc["expected_result"] for tc in cases}
    assert "pass" in results, "No passing test cases found"
    assert "fail" in results, "No failing test cases found"


def test_suite_minimum_size():
    """Suite must have at least 10 test cases."""
    cases = load_test_cases()
    assert len(cases) >= 10, f"Expected >= 10 test cases, got {len(cases)}"
