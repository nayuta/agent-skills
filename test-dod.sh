#!/bin/bash
# Test script to validate DoD items for FEL-330
# This script should FAIL initially (RED phase), then PASS after implementation (GREEN phase)

set -e

FAILED_TESTS=0
PASSED_TESTS=0

echo "=== Testing DoD Items for FEL-330 ==="
echo ""

# Test T1: allowed-tools in security-review/SKILL.md frontmatter
echo "[T1] Testing allowed-tools in security-review/SKILL.md frontmatter..."
if grep -q "^allowed-tools:" skills/security-review/SKILL.md; then
    echo "✓ PASS: allowed-tools field exists"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "✗ FAIL: allowed-tools field missing"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Test T2: security-review/README.md <= 40 lines
echo "[T2] Testing security-review/README.md line count..."
if [[ ! -f "skills/security-review/README.md" ]]; then
    echo "✗ FAIL: README.md does not exist"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    if [[ -f "skills/security-review/README.md" ]]; then
        LINE_COUNT=$(wc -l < skills/security-review/README.md)
    else
        LINE_COUNT=0
    fi
    if [[ ${LINE_COUNT} -le 40 ]]; then
        echo "✓ PASS: README.md has ${LINE_COUNT} lines (<= 40)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "✗ FAIL: README.md has ${LINE_COUNT} lines (> 40)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
fi

# Check that duplicated tables are removed
if grep -q "Vulnerability categories" skills/security-review/README.md; then
    echo "✗ FAIL: Duplicated 'Vulnerability categories' table still exists"
    FAILED_TESTS=$((FAILED_TESTS + 1))
else
    echo "✓ PASS: Duplicated tables removed"
    PASSED_TESTS=$((PASSED_TESTS + 1))
fi
echo ""

# Test T3: Eval test cases exist for both skills
echo "[T3] Testing eval test cases existence..."
if [[ -f "skills/security-review/evals/security-review-evals.yaml" ]]; then
    CASE_COUNT=$(grep -c "^  - id:" skills/security-review/evals/security-review-evals.yaml || echo "0")
    if [[ ${CASE_COUNT} -ge 3 ]]; then
        echo "✓ PASS: security-review has ${CASE_COUNT} test cases (>= 3)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "✗ FAIL: security-review has ${CASE_COUNT} test cases (< 3)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "✗ FAIL: security-review/evals/security-review-evals.yaml does not exist"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi

if [[ -f "skills/security-scan/evals/security-scan-evals.yaml" ]]; then
    CASE_COUNT=$(grep -c "^  - id:" skills/security-scan/evals/security-scan-evals.yaml || echo "0")
    if [[ ${CASE_COUNT} -ge 3 ]]; then
        echo "✓ PASS: security-scan has ${CASE_COUNT} test cases (>= 3)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo "✗ FAIL: security-scan has ${CASE_COUNT} test cases (< 3)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
else
    echo "✗ FAIL: security-scan/evals/security-scan-evals.yaml does not exist"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Test T4: --strict flag functionality
echo "[T4] Testing run-scans.sh --strict flag..."
if grep -q "\-\-strict" skills/security-scan/scripts/run-scans.sh; then
    echo "✓ PASS: --strict flag exists in run-scans.sh"
    PASSED_TESTS=$((PASSED_TESTS + 1))
else
    echo "✗ FAIL: --strict flag not implemented in run-scans.sh"
    FAILED_TESTS=$((FAILED_TESTS + 1))
fi
echo ""

# Summary
echo "=== Test Summary ==="
echo "Passed: ${PASSED_TESTS}"
echo "Failed: ${FAILED_TESTS}"
echo ""

if [[ ${FAILED_TESTS} -gt 0 ]]; then
    echo "RED PHASE: Tests are failing as expected"
    exit 1
else
    echo "GREEN PHASE: All tests passing!"
    exit 0
fi
