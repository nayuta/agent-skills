---
name: validate-fix
description: Iteratively run Agent Skill validation and resolve any issues found.
---

# Validate & Fix Agent Skills

## Purpose

This skill provides an autonomous loop for identifying and fixing validation issues in Agent Skills using `make validate`. Use this when you need to ensure all skills in the repository adhere to the Agent Skills Specification.

## Loop Logic

1.  **Validate**: Run `make validate` to check all Agent Skills.
2.  **Analyze**: For any failures reported:
    - Examine the error message and the failing `SKILL.md` or directory structure.
    - Identify the specific validation rule being violated (e.g., missing frontmatter, unsupported fields).
3.  **Fix**: Apply the necessary changes to the failing skill.
4.  **Verify**: Re-run `make validate`.
    - If passed: Move to next issue or terminate if all pass.
    - If failed: Analyze the new failure and repeat the loop.

## Termination Criteria

- No more errors reported by `make validate`.
- Reached max iteration limit (default: 5).

## Common Commands

| Task                | Command                       |
| :------------------ | :---------------------------- |
| Validate all skills | `make validate`               |
| Validate via script | `bash dev/validate_skills.sh` |

## Examples

### Scenario: Fixing Frontmatter Errors

1.  `make validate` reports `Unexpected fields in frontmatter: argument-hint` in `skills/tf-debug/SKILL.md`.
2.  Agent removes the unsupported `argument-hint` field from `skills/tf-debug/SKILL.md`.
3.  `make validate` passes for all skills.
