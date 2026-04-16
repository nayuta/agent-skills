#!/bin/bash
# Test: Grype migration validation
# Verifies trivy->grype migration in security-scan skill

set -uo pipefail

unset CDPATH
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FAILURES=0

assert_match() {
    local desc="$1"
    local pattern="$2"
    local file="$3"
    if grep -q "${pattern}" "${file}"; then
        echo "PASS: ${desc}"
    else
        echo "FAIL: ${desc} (pattern '${pattern}' not found in ${file##*/})"
        FAILURES=$((FAILURES + 1))
    fi
}

assert_no_match() {
    local desc="$1"
    local pattern="$2"
    local file="$3"
    if grep -qi "${pattern}" "${file}"; then
        echo "FAIL: ${desc} (found '${pattern}' in ${file##*/})"
        FAILURES=$((FAILURES + 1))
    else
        echo "PASS: ${desc}"
    fi
}

assert_test() {
    local desc="$1"
    shift
    if "$@"; then
        echo "PASS: ${desc}"
    else
        echo "FAIL: ${desc}"
        FAILURES=$((FAILURES + 1))
    fi
}

# 1. Zero trivy references across all three files
assert_no_match "No trivy references in run-scans.sh" \
    "trivy" "${SKILL_DIR}/scripts/run-scans.sh"

assert_no_match "No trivy references in SKILL.md" \
    "trivy" "${SKILL_DIR}/SKILL.md"

assert_no_match "No trivy references in README.md" \
    "trivy" "${SKILL_DIR}/README.md"

# 2a. grype invocation uses dir:. as target
assert_match "grype uses dir:. target" \
    'grype dir:\.' "${SKILL_DIR}/scripts/run-scans.sh"

# 2b. grype invocation uses run_tool wrapper
assert_match "grype uses run_tool wrapper" \
    'run_tool "grype"' "${SKILL_DIR}/scripts/run-scans.sh"

# 3. SKILL.md front-matter references grype
assert_match "SKILL.md front-matter references grype" \
    'grype' "${SKILL_DIR}/SKILL.md"

# 4. README.md table references grype
assert_match "README.md table references grype" \
    'grype' "${SKILL_DIR}/README.md"

# 5. README.md install hint references grype
assert_match "README.md install hint references grype" \
    'brew install grype' "${SKILL_DIR}/README.md"

# 6. SKILL.md Purpose column has no misconfiguration claim
assert_no_match "SKILL.md grype row has no misconfiguration claim" \
    "misconfiguration" "${SKILL_DIR}/SKILL.md"

# 7. skill-audit score (simplified -- check files exist and have expected content)
assert_test "run-scans.sh exists and is executable" \
    test -x "${SKILL_DIR}/scripts/run-scans.sh"

echo ""
echo "Results: $((10 - FAILURES))/10 passed, ${FAILURES} failed"
exit "${FAILURES}"
