---
name: audit-docs
description: Validate CLAUDE.md and AGENTS.md against actual codebase structure and conventions.
---

# Audit Documentation Files

## Purpose

This skill provides static validation of `CLAUDE.md` and `AGENTS.md` documentation files to ensure they accurately reflect the actual codebase structure and follow proper conventions.

## What It Validates

### 1. Marker Format (MARKER_MISSING)

Required comment marker pairs must exist:

- `<!-- AVAILABLE_SKILLS_START -->` / `<!-- AVAILABLE_SKILLS_END -->`
- `<!-- AVAILABLE_AGENTS_START -->` / `<!-- AVAILABLE_AGENTS_END -->`

### 2. Table Structure (TABLE_MALFORMED)

Tables must have:

- Exactly 3 columns: Name | Description | Link
- Proper separator row with `:---` alignment
- Non-empty, well-formed markdown table syntax

### 3. Link Validity (LINK_BROKEN)

All file links in tables must:

- Resolve to existing files in the repository
- Use correct relative paths

### 4. Skill Completeness (SKILL_UNLISTED)

All skills in `.claude/skills/` must:

- Be listed in the Available Skills table
- Exception: Skills with `unlisted: true` in frontmatter are ignored

### 5. Agent Completeness (AGENT_UNLISTED)

All agents in `.claude/agents/` must:

- Be listed in the Available Agents table
- Exception: Agents with `unlisted: true` in frontmatter are ignored

### 6. Synchronization (AGENTS_DESYNC)

`AGENTS.md` must:

- Have identical body content to `CLAUDE.md` (excluding first line)
- The first line of `AGENTS.md` is `# AGENTS.md` while `CLAUDE.md` is `# CLAUDE.md`

## Usage

### Basic Validation

```bash
# Validate current repository
uv run .claude/skills/audit-docs/scripts/audit_docs.py .

# Validate specific repository
uv run .claude/skills/audit-docs/scripts/audit_docs.py /path/to/repo
```

### Via Makefile

```bash
make audit-docs
```

### Exit Codes

- `0` - All checks passed
- `1` - Issues found (validation errors)
- `2` - Fatal error (missing files, invalid arguments)

## Output Format

Human-readable plain text listing all findings:

```
[ERROR] MARKER_MISSING @ /path/to/CLAUDE.md :: Missing marker pair: AVAILABLE_SKILLS_START / AVAILABLE_SKILLS_END
[ERROR] SKILL_UNLISTED @ /path/to/.claude/skills/example/SKILL.md :: Skill 'example' not listed in CLAUDE.md table
[ERROR] LINK_BROKEN @ /path/to/CLAUDE.md :: Broken link: .claude/skills/missing/SKILL.md
```

## Edge Cases

- **Missing CLAUDE.md**: Reports `FILE_MISSING` error
- **Empty skills directory**: Passes (no findings)
- **Skill directory without SKILL.md**: Ignored (not validated)
- **Skills with `unlisted: true`**: Excluded from completeness check
- **No AGENTS.md**: Skips synchronization check
- **Multi-line table cells**: Handled via pipe delimiter parsing

## Implementation Details

- **Zero dependencies**: Uses only Python 3.11+ standard library
- **PEP 723 compliant**: Inline script metadata for `uv run`
- **Simple frontmatter parser**: Manual YAML parsing for basic key: value pairs
- **Pattern**: Follows `skill_audit.py` architecture (dataclasses, Finding/Report)

## Testing

Run test suite:

```bash
uv run pytest .claude/skills/audit-docs/test/test_audit_docs.py -v
```

9 test functions covering:

1. Valid CLAUDE.md passes
2. Missing markers fail
3. Invalid table format fails
4. Broken links fail
5. Orphan skills fail
6. Unlisted frontmatter ignored
7. AGENTS.md desync fails
8. Exit code 0 for clean
9. Exit code 1 for issues

## Integration

This skill is designed to be:

- Run in CI/CD pipelines to catch documentation drift
- Integrated into pre-commit hooks
- Used by documentation maintenance agents
- Part of the `mend-docs` skill workflow
