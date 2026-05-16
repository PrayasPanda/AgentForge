#!/bin/bash
# Quick demo for Loom recording
# Run from project root: bash scripts/demo.sh

set -e

echo "🚀 Cursor Agent Factory Demo"
echo "================================"
echo ""

# Clear previous demo output
if [ -d "outputs/demo-python-security-agent" ]; then
    rm -rf outputs/demo-python-security-agent
    echo "🧹 Cleared previous demo output"
fi

echo ""
echo "📝 Creating Python security agent..."
echo "   Command: python -m src.main --create \"Python security agent - SQL injection, XSS, secrets\""
echo ""

python -m src.main --create "Python security agent - SQL injection, XSS, secrets"

echo ""
echo "📂 Generated files:"
find outputs/ -maxdepth 3 -type f | sort

echo ""
echo "📊 Benchmark results:"
cat outputs/python-security-agent-sql-injection-xss-secrets/benchmarks.json 2>/dev/null \
  || find outputs/ -name benchmarks.json -exec cat {} \; 2>/dev/null \
  || echo "(benchmarks.json location varies by slug)"

echo ""
echo "✅ Demo complete!"
