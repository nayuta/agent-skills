# CLAUDE.md

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with code in this repository.

## Available Skills

<!-- AVAILABLE_SKILLS_START -->

| Name             | Description                                                                                | Link                                                                                 |
| :--------------- | :----------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------- |
| audit-docs       | Validate CLAUDE.md and AGENTS.md against actual codebase structure and conventions.        | [.claude/skills/audit-docs/SKILL.md](.claude/skills/audit-docs/SKILL.md)             |
| validate-fix     | Iteratively run Agent Skill validation and resolve any issues found.                       | [.claude/skills/validate-fix/SKILL.md](.claude/skills/validate-fix/SKILL.md)         |
| mend-docs        | Maintain and synchronize documentation files with the actual codebase (agents and skills). | [.claude/skills/mend-docs/SKILL.md](.claude/skills/mend-docs/SKILL.md)               |
| mend-agent-rules | Synchronize CLAUDE.md and AGENTS.md with available agents and skills.                      | [.claude/skills/mend-agent-rules/SKILL.md](.claude/skills/mend-agent-rules/SKILL.md) |

<!-- AVAILABLE_SKILLS_END -->

## Available Agents

<!-- AVAILABLE_AGENTS_START -->

| Name             | Description                                                                                                                 | Link                                                                     |
| :--------------- | :-------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------- |
| maintainer-agent | Expert codebase maintainer. Proactively synchronizes documentation with the actual codebase and validates all Agent Skills. | [.claude/agents/maintainer-agent.md](.claude/agents/maintainer-agent.md) |

<!-- AVAILABLE_AGENTS_END -->

## Agent Skills

<!-- FRAMEWORK_DOCS_START -->

### What are Agent Skills?

Agent Skills are a lightweight, open format for defining specialized tasks that an AI agent can perform. Each skill is contained in a directory within the `skills/` folder and includes a `SKILL.md` file with metadata and instructions.

### Directory Structure

Skills are organized as follows:

```
skills/
  <skill-name>/
    SKILL.md       # Required: instructions + metadata
    scripts/       # Optional: executable code
    references/    # Optional: documentation
    assets/        # Optional: templates, resources
```

### Guidelines for Agents

- **Read Skills Proactively**: When you identify a relevant skill, read and follow it IMMEDIATELY as your first action.
- **Progressive Disclosure**: Only read the full `SKILL.md` or referenced files when the skill is actually needed to save context.
- **Follow the Specification**: Ensure any new skills you create follow the [Agent Skills Specification](https://agentskills.io/specification).
- **No Relative Links Between Skills**: Do not use relative path links between skills. When referencing another skill, use the skill name instead.
- **Write in English**: `CLAUDE.md` and `AGENTS.md` must be written in English.
- **Python Scripts**: Avoid implementing Python scripts. If necessary, use `uv`'s script dependency management (PEP 723) with inline metadata.

<!-- FRAMEWORK_DOCS_END -->
