"""
Unit tests for agent_generator.py.
These tests do not call the Claude API — they test validation and prompt logic.
"""

import pytest
from src.agent_generator import validate_rules, _build_prompt


class TestValidateRules:
    def test_valid_rules_pass(self):
        rules = (
            "## ROLE\nYou are a security expert.\n\n"
            "## MANDATORY CHECKS\n1. Check for SQL injection\n\n"
            "## EXAMPLES\nGood: parameterized query\nBad: f-string query\n\n"
            "## OUTPUT FORMAT\nReturn STATUS: PASS or FAIL"
        )
        result = validate_rules(rules)
        assert "ROLE" in result
        assert "CHECKS" in result

    def test_strips_markdown_fences(self):
        rules = (
            "```\n"
            "## ROLE\nYou are a security expert.\n"
            "## MANDATORY CHECKS\n1. Always check for issues.\n"
            "## EXAMPLES\nGood: safe code\nBad: unsafe code\n"
            "```"
        )
        result = validate_rules(rules)
        assert "```" not in result

    def test_too_short_raises(self):
        with pytest.raises(ValueError, match="too short"):
            validate_rules("short")

    def test_missing_role_raises(self):
        rules = (
            "## MANDATORY CHECKS\n1. Always validate.\n\n"
            "## EXAMPLES\nGood: x\nBad: y\n\n"
            "## OUTPUT FORMAT\nReturn PASS or FAIL"
        ) * 3
        with pytest.raises(ValueError, match="missing required sections"):
            validate_rules(rules)

    def test_missing_check_raises(self):
        rules = (
            "## ROLE\nYou are an expert.\n\n"
            "## EXAMPLES\nGood example here.\nBad example there.\n\n"
            "## OUTPUT FORMAT\nReturn PASS or FAIL"
        ) * 3
        with pytest.raises(ValueError, match="missing required sections"):
            validate_rules(rules)

    def test_missing_examples_raises(self):
        rules = (
            "## ROLE\nYou are an expert.\n\n"
            "## MANDATORY CHECKS\n1. Must always check.\n\n"
            "## OUTPUT FORMAT\nReturn PASS or FAIL"
        ) * 3
        with pytest.raises(ValueError, match="missing required sections"):
            validate_rules(rules)

    def test_strips_leading_trailing_whitespace(self):
        rules = (
            "\n\n## ROLE\nYou are an expert agent for Cursor AI.\n\n"
            "## MANDATORY CHECKS\n1. You MUST always check for issues.\n"
            "2. You MUST never skip validation.\n\n"
            "## EXAMPLES\n"
            "Good: parameterized query prevents injection.\n"
            "Bad: f-string interpolation in SQL allows injection.\n\n"
        )
        result = validate_rules(rules)
        assert not result.startswith("\n")
        assert not result.endswith("\n")


class TestBuildPrompt:
    def test_prompt_contains_description(self):
        desc = "Python security specialist agent"
        prompt = _build_prompt(desc)
        assert desc in prompt

    def test_prompt_asks_for_raw_content(self):
        prompt = _build_prompt("any agent")
        assert "ONLY" in prompt
        assert "markdown" in prompt.lower()

    def test_prompt_specifies_required_sections(self):
        prompt = _build_prompt("test agent")
        assert "role" in prompt.lower()
        assert "example" in prompt.lower()
