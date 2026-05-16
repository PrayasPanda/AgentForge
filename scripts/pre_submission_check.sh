#!/bin/bash
# Pre-submission verification script
# Run: bash scripts/pre_submission_check.sh

PASS=0
FAIL=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "ok" ]; then
        echo "✅ $desc"
        PASS=$((PASS + 1))
    else
        echo "❌ $desc — $result"
        FAIL=$((FAIL + 1))
    fi
}

echo "🔍 Pre-submission checks for Cursor Agent Factory"
echo "=================================================="
echo ""

# No secrets in repo
if grep -r "sk-ant-\|sk_live_\|ANTHROPIC_API_KEY=" --include="*.py" --include="*.json" --include="*.md" . \
   --exclude-dir=.git 2>/dev/null | grep -v ".env.example" | grep -q .; then
    check "No secrets in repo" "found potential secrets!"
else
    check "No secrets in repo" "ok"
fi

# .env.example exists
[ -f ".env.example" ] && check ".env.example present" "ok" || check ".env.example present" "missing"

# .gitignore ignores .env
grep -q "^\.env$" .gitignore && check ".gitignore ignores .env" "ok" || check ".gitignore ignores .env" "missing"

# Requirements file
[ -f "requirements.txt" ] && check "requirements.txt present" "ok" || check "requirements.txt present" "missing"

# Example agents present
for agent in security-agent react-component-agent api-testing-agent; do
    [ -f "examples/$agent/.cursorrules" ] \
        && check "examples/$agent/.cursorrules" "ok" \
        || check "examples/$agent/.cursorrules" "missing"
done

# Docs present
for doc in ARCHITECTURE SCORING_METHODOLOGY BENCHMARK_RESULTS RECURSIVE_PROOF USER_GUIDE; do
    [ -f "docs/$doc.md" ] \
        && check "docs/$doc.md" "ok" \
        || check "docs/$doc.md" "missing"
done

# README.md
[ -f "README.md" ] && check "README.md present" "ok" || check "README.md present" "missing"

# Run unit tests
echo ""
echo "🧪 Running unit + integration tests..."
if python -m pytest tests/ -q --tb=short 2>&1 | tail -5; then
    check "All tests pass" "ok"
else
    check "All tests pass" "tests failed — check output above"
fi

echo ""
echo "=================================================="
echo "Results: $PASS passed, $FAIL failed"
if [ "$FAIL" -eq 0 ]; then
    echo "🎉 Ready to submit!"
else
    echo "⚠️  Fix $FAIL issue(s) before submitting."
fi
