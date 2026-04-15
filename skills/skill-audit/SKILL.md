---
name: skill-audit
description: |
  Audits Claude Code or Agent Skills directories for structural correctness, risky
  instructions, trigger scope, coexistence issues, and efficiency regressions.
  Runs a static checker (skill_audit.py) for deterministic validation, then applies
  AI reasoning for judgment calls: vague descriptions, conflicting skills, context bloat.
  Produces a severity-classified report with blockers, important issues, and optional
  improvements. Use when reviewing a skill before sharing, enabling, or deploying it.
allowed-tools: Read Grep Bash(python *) Bash(uv *) Bash(rg *) Bash(find *)
compatibility: |
  Requires Python 3.8+. Optional: PyYAML for richer frontmatter parsing.
  Install with: pip install pyyaml
metadata:
  version: "1.0.0"
  author: nayuta
---

# Skill Audit

## Purpose

Systematically validate Claude Code / Agent Skills directories for correctness,
security, and quality. Combines static analysis (deterministic checks) with
AI reasoning (judgment on trigger scope, coexistence, context efficiency).

## Workflow

### Step 1: Static Analysis

Run the bundled auditor from the repository root:

```bash
python skills/skill-audit/scripts/skill_audit.py <skill-path> --surface claude-code
```

For agent-api mode (strict, requires `name` and `description`):

```bash
python skills/skill-audit/scripts/skill_audit.py <skill-path> --surface agent-api
```

JSON output for programmatic use:

```bash
python skills/skill-audit/scripts/skill_audit.py <skill-path> --json
```

Exit code is non-zero when the worst score drops below 70.

### Step 2: Read the Skill

Read `SKILL.md` and any directly referenced files (scripts, references, assets).
Do not read files that are not referenced — they are background context only.

### Step 3: AI Judgment Review

Assess four areas that static checks cannot cover:

#### Discovery problems

- Is the `description` narrow enough to avoid false triggers?
- Does it overlap significantly with adjacent skills in the same directory?
- Would a model reliably select this skill for its intended use cases?

#### Isolation problems

- Are all referenced files present and accessible?
- Does the skill rely on environment assumptions not stated in `compatibility`?
- Are external dependencies (APIs, CLIs, credentials) documented?

#### Coexistence problems

- Does this skill's description overlap with other skills in the directory?
- Could two skills be triggered simultaneously causing conflict?
- Are trigger boundaries clear and mutually exclusive where needed?

#### Efficiency problems

- Is `SKILL.md` under 500 lines? (warn above this threshold)
- Is large reference content in separate files rather than inline?
- Does the skill regenerate the same code on every run that could be a script?
- Are volatile business rules or policies externalizable?

### Step 4: Report

Present findings in three severity buckets:

```markdown
## Skill Audit: <skill-name>

**Score**: <0-100> | **Surface**: <claude-code|agent-api>
**Static findings**: N errors, N warnings, N info

---

### Blockers

Issues that prevent safe use or deployment.

- [ERROR] <code> @ <file>:<line> — <message>
  **Why it matters**: <impact>
  **Fix**: <exact change>

### Important

Issues that reduce reliability or increase risk.

- [WARN] <code> @ <file>:<line> — <message>
  **Why it matters**: <impact>
  **Fix**: <exact change>

### Optional

Improvements that increase efficiency or clarity.

- [INFO] <code> — <message>
  **Suggestion**: <recommendation>

### Evaluation Gaps

Missing test cases for the eval suite:

- should-trigger: <prompt that should activate this skill>
- should-not-trigger: <prompt that should NOT activate this skill>
- ambiguous: <edge case worth tracking>

### Efficiency Notes

<Estimate where the skill wastes context, time, or tool calls>
```

If the score is 100 and no AI judgment issues are found, report:

```markdown
## Skill Audit: <skill-name>

**Score**: 100 | No issues found. Safe to use as-is.
```

## Static Checks Covered

| Category               | Checks                                                                    |
| ---------------------- | ------------------------------------------------------------------------- |
| Structure              | `SKILL.md` presence, YAML frontmatter parseable                           |
| Metadata               | `name` format (`^[a-z0-9-]{1,64}$`), reserved words, `description` length |
| Body                   | Non-empty, under 500 lines                                                |
| Links                  | Local markdown links resolve to existing files                            |
| Secrets                | Hardcoded API keys, tokens, passwords                                     |
| Network access         | External network calls embedded in skill instructions                     |
| Path traversal         | Dot-dot-slash escapes in skill instructions                               |
| Adversarial content    | Instructions designed to conceal actions or circumvent safety controls    |
| Portability            | Windows-style paths                                                       |
| Privilege              | Wildcard `allowed-tools`                                                  |
| Time-sensitive wording | `today`, `yesterday`, `latest`, `current policy`                          |

## Bundled Resources

| File                       | Purpose                                           |
| -------------------------- | ------------------------------------------------- |
| `scripts/skill_audit.py`   | Static auditor — run directly or import as module |
| `evals/example-evals.yaml` | Example evaluation schema for dynamic testing     |

## Integration

- Run in CI on every change to any skill directory
- Add a Claude Code hook that triggers this audit after edits to `.claude/skills/**`
- Gate new skill versions on a passing score (≥ 70)
- Pair with `validate-fix` to automatically resolve discovered issues
