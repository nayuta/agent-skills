# Contributing to agent-skills

## Adding a New Skill

Skills live in the `skills/` directory. Each skill must follow the [Agent Skills Specification](https://agentskills.io/specification).

1. Create a directory: `skills/my-skill/`
2. Add `SKILL.md` with YAML frontmatter:

   ```markdown
   ---
   name: my-skill
   description: What it does and when to use it.
   ---

   # My Skill

   ## Instructions

   ...
   ```

3. Add optional supporting files:
   - `scripts/` — executable shell scripts
   - `references/` — documentation, schemas
   - `assets/` — templates, static files

## Development Workflow

### Prerequisites

- [Node.js](https://nodejs.org/) (for `npx skills`)
- [uv](https://docs.astral.sh/uv/) (for skill validation)
- [shellcheck](https://www.shellcheck.net/) (for shell linting)
- [markdownlint-cli2](https://github.com/DavidAnson/markdownlint-cli2) (for markdown linting)
- [prettier](https://prettier.io/) (for formatting)

### Setup

```bash
# Install project-level maintenance skills (validate-fix, mend-docs, mend-agent-rules)
make setup
```

### Validation

```bash
# Validate all skills against the Agent Skills Specification
make validate-skills

# Lint shell scripts, markdown, and JSON/YAML
make lint

# Format files
make format
```

### Pull Request Process

1. Create a branch: `git checkout -b feat/skill-name`
2. Add or update the skill
3. Run `make validate-skills` — must pass
4. Run `make lint` — must pass
5. Submit a PR

## Project-Level Skills

The following skills are installed via `make setup` from `ubie-inc/agent-skills` and tracked in `skills-lock.json`:

<!-- PROJECT_SKILLS_START -->

| Name              | Description                                                                        | Source                    |
| :---------------- | :--------------------------------------------------------------------------------- | :------------------------ |
| validate-fix      | Iteratively run Agent Skill validation and resolve any issues found.               | `ubie-inc/agent-skills`   |
| mend-docs         | Maintain and synchronize documentation files with the actual codebase.             | `ubie-inc/agent-skills`   |
| mend-agent-rules  | Synchronize CLAUDE.md and AGENTS.md with available agents and skills.              | `ubie-inc/agent-skills`   |

<!-- PROJECT_SKILLS_END -->

## Project-Level Agents

<!-- PROJECT_AGENTS_START -->

| Name              | Description                                                                                                                  | Link                                                                         |
| :---------------- | :--------------------------------------------------------------------------------------------------------------------------- | :--------------------------------------------------------------------------- |
| maintainer-agent  | Expert codebase maintainer. Synchronizes documentation and ensures all Agent Skills are valid. | [.claude/agents/maintainer-agent.md](.claude/agents/maintainer-agent.md) |

<!-- PROJECT_AGENTS_END -->
