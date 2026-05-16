"""
Generates .cursorrules files using the configured LLM provider.

Process:
  1. Parse user's agent description
  2. Query LLM for optimal rules
  3. Validate generated rules
  4. Format according to Cursor spec
"""

import re

from src import llm_client


def _build_prompt(description: str) -> str:
    return f"""You are an expert at creating .cursorrules files for Cursor AI editor.

User wants to create: {description}

Generate a production-ready .cursorrules file that:
- Starts with a clear ROLE definition (who this agent is)
- Lists MANDATORY CHECKS (what MUST always happen)
- Lists HEURISTICS (what SHOULD happen when applicable)
- Includes EXAMPLES section with 3 good patterns and 3 bad patterns
- Ends with OUTPUT FORMAT specification
- Uses clear, actionable imperative language
- Covers edge cases specific to this domain

Return ONLY the raw .cursorrules content. No markdown fences, no explanation, no preamble."""


def validate_rules(rules: str) -> str:
    """Ensure generated rules meet minimum structural requirements."""
    rules = rules.strip()
    if len(rules) < 100:
        raise ValueError("Generated rules are too short to be valid.")

    required_sections = ["role", "check", "example"]
    lower = rules.lower()
    missing = [s for s in required_sections if s not in lower]
    if missing:
        raise ValueError(
            f"Generated rules missing required sections: {missing}"
        )

    # Strip any accidental markdown fences
    rules = re.sub(r"^```[a-z]*\n?", "", rules, flags=re.MULTILINE)
    rules = re.sub(r"\n?```$", "", rules, flags=re.MULTILINE)
    return rules.strip()


def generate_cursorrules(description: str) -> str:
    """
    Generate a .cursorrules file for the given agent description.

    Args:
        description: Natural language description of the agent to create.

    Returns:
        Validated .cursorrules content as a string.
    """
    prompt = _build_prompt(description)
    raw = llm_client.complete(prompt, max_tokens=4096)
    return validate_rules(raw)
