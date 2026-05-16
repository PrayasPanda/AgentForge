"""
Cursor Agent Factory — CLI entry point.

Usage:
  python -m src.main --create "security agent for Python"
  python -m src.main --benchmark outputs/python-security-agent
  python -m src.main --self-improve
"""

import argparse
import json
import os
import sys
import time


def generate_agent(description: str) -> None:
    from src.agent_generator import generate_cursorrules
    from src.test_suite_builder import build_test_suite
    from src.benchmark_engine import benchmark_agent
    from src.packager import package_agent
    from src import llm_client

    print(f"\n🔍 Analyzing requirements: {description!r}")
    print(f"   Provider: {llm_client.provider_label()}")
    start = time.time()

    print("🤖 Generating .cursorrules with Claude...")
    cursorrules = generate_cursorrules(description)
    print(f"✅ Rules generated ({len(cursorrules.splitlines())} lines)")

    print("🧪 Creating test suite...")
    test_cases = build_test_suite(description, cursorrules)
    print(f"✅ {len(test_cases)} test cases created")

    print("📊 Benchmarking vs default Cursor...")
    results = benchmark_agent(cursorrules, test_cases, description)
    print(
        f"   Default accuracy : {results.default_accuracy:.0%}\n"
        f"   Custom accuracy  : {results.custom.accuracy:.0%}\n"
        f"   Improvement      : +{results.improvement_ratio * 100:.1f}%\n"
        f"   Score            : {results.performance_score}/10,000"
    )

    print("📦 Packaging agent...")
    output_dir = package_agent(description, cursorrules, test_cases, results)

    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print(f"\n✅ Agent ready at: {output_dir}/")
    print(f"   .cursorrules, tests/, benchmarks.json, README.md")
    print(f"⏱️  Total time: {mins}m {secs}s")


def run_benchmark(agent_path: str) -> None:
    from src.test_suite_builder import TestCase
    from src.benchmark_engine import benchmark_agent, results_to_dict

    cursorrules_path = os.path.join(agent_path, ".cursorrules")
    test_cases_path = os.path.join(agent_path, "tests", "test_cases.json")

    if not os.path.exists(cursorrules_path):
        print(f"❌ No .cursorrules found at {cursorrules_path}")
        sys.exit(1)

    with open(cursorrules_path, encoding="utf-8") as f:
        cursorrules = f.read()

    test_cases = []
    if os.path.exists(test_cases_path):
        with open(test_cases_path, encoding="utf-8") as f:
            raw = json.load(f)
        test_cases = [
            TestCase(
                code=tc["code"],
                expected_result=tc["expected_result"],
                reason=tc["reason"],
                category=tc.get("category", "positive"),
            )
            for tc in raw
        ]
    else:
        print("⚠️  No test_cases.json found; generating minimal test suite...")
        from src.test_suite_builder import build_test_suite
        description = os.path.basename(agent_path).replace("-", " ")
        test_cases = build_test_suite(description, cursorrules)

    print(f"\n📊 Benchmarking agent at: {agent_path}")
    results = benchmark_agent(cursorrules, test_cases)
    report = results_to_dict(results)

    print(f"\nResults:")
    print(f"  Custom accuracy : {report['custom_accuracy']:.0%}")
    print(f"  Default accuracy: {report['default_accuracy']:.0%}")
    print(f"  Improvement     : +{report['improvement_percent']:.1f}%")
    print(f"  Score           : {report['performance_score']}/10,000")

    out_path = os.path.join(agent_path, "benchmarks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"\n✅ Results saved to {out_path}")


def recursive_improvement() -> None:
    """Use the factory to improve its own .cursorrules."""
    print("\n🔄 Starting recursive self-improvement...")

    own_rules_path = os.path.join(os.path.dirname(__file__), "..", ".cursorrules")
    if os.path.exists(own_rules_path):
        with open(own_rules_path, encoding="utf-8") as f:
            current_rules = f.read()
        print(f"📖 Loaded current .cursorrules ({len(current_rules.splitlines())} lines)")
    else:
        current_rules = ""
        print("⚠️  No existing .cursorrules found; generating from scratch")

    description = (
        "meta-agent architect for Cursor that generates production-ready .cursorrules files "
        "for any domain, with domain analysis, rule synthesis, validation, and documentation"
    )

    from src.agent_generator import generate_cursorrules
    new_rules = generate_cursorrules(description)

    with open(own_rules_path, "w", encoding="utf-8") as f:
        f.write(new_rules)

    print(f"✅ .cursorrules improved ({len(new_rules.splitlines())} lines)")
    print("🔄 Self-improvement complete. Review changes before committing.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Cursor Agent Factory — generate production-ready Cursor agents"
    )
    parser.add_argument("--create", metavar="DESCRIPTION", help="Agent description")
    parser.add_argument("--benchmark", metavar="PATH", help="Path to agent directory")
    parser.add_argument(
        "--self-improve", action="store_true", help="Improve the factory's own rules"
    )

    args = parser.parse_args()

    if args.create:
        generate_agent(args.create)
    elif args.benchmark:
        run_benchmark(args.benchmark)
    elif args.self_improve:
        recursive_improvement()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
