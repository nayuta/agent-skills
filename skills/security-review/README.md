# security-review

AI-driven security code review of changes in the current branch. Analyzes diffs for logic flaws, design issues, and vulnerabilities across 8 categories, reporting only high-confidence findings.

## What it does

1. Builds repository context (tech stack, existing security patterns)
2. Collects the diff vs. `origin/main`
3. Systematically checks each changed file against 8 vulnerability categories
4. Filters findings to confidence ≥ 8/10 to minimize noise
5. Produces a structured report with severity ratings and remediation guidance

## Platform support

Language-agnostic — works on any codebase. No tools to install.

## Usage

```
/security-review
```

## Vulnerability categories

| #   | Category                             | Examples                                                    |
| --- | ------------------------------------ | ----------------------------------------------------------- |
| 1   | Secrets and Credentials              | Hardcoded API keys, embedded passwords                      |
| 2   | Injection                            | SQL, command, template, NoSQL injection                     |
| 3   | Authentication and Authorization     | IDOR, broken JWT, missing auth guards, privilege escalation |
| 4   | Cryptography                         | Weak algorithms, insecure RNG, static IVs                   |
| 5   | Input Validation and Output Encoding | XSS, SSRF, path traversal, open redirect                    |
| 6   | Sensitive Data Exposure              | PII in logs, secrets in API responses, verbose errors       |
| 7   | Dependency Risks                     | New packages with CVEs, integrity check bypasses            |
| 8   | Security Configuration               | Missing rate limits, CORS wildcard, TLS skip                |

## Confidence threshold

Only findings with confidence ≥ 8/10 are reported:

| Score | Meaning                                             |
| ----- | --------------------------------------------------- |
| 10    | Exploitable with certainty, clear reproduction path |
| 9     | Very likely exploitable, minor assumption required  |
| 8     | Likely exploitable, context supports it             |
| ≤ 7   | Excluded — possible false positive or low impact    |

## Output format

```markdown
## Security Review

**Date**: 2026-04-08T00:00:00Z
**Branch**: feat/my-feature
**Files reviewed**: 12
**High-confidence findings**: 2 (Critical: 1 | High: 1 | Medium: 0)

---

## Critical

### [SEC-001] SQL Injection in UserRepository

**File**: `src/users/repository.ts:42`
**Category**: Injection > SQL Injection
**Confidence**: 9/10

**Evidence**: ...
**Impact**: ...
**Remediation**: ...
```

## References

- [Vulnerability Categories Detail](references/vulnerability-categories.md) — deeper patterns and examples per category

## Pairs with

- **security-scan** — tool-based scanning for secrets and known CVEs; run before this skill for complete coverage
