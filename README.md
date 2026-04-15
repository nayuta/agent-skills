# agent-skills

Personal collection of agent skills for Claude Code and other AI coding agents. Skills follow the [Agent Skills](https://agentskills.io/) format.

## Usage

### List available skills

```bash
npx skills add nayuta/agent-skills --list
```

### Install a specific skill

```bash
npx skills add nayuta/agent-skills --skill security-scan
```

### Install all skills globally

```bash
npx skills add nayuta/agent-skills --all --global
```

## Available Skills

<!-- REUSABLE_SKILLS_START -->

| Name          | Description                                                                                                                                                                                | Link                                                         |
| :------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------- |
| security-scan | Runs available security scanning tools against the current project and produces a consolidated markdown report. Pairs with security-review for a complete security workflow. | [skills/security-scan/SKILL.md](skills/security-scan/SKILL.md) |

<!-- REUSABLE_SKILLS_END -->

## Development Setup

After cloning, install project-level maintenance skills:

```bash
make setup
```

This runs `npx skills add ubie-inc/agent-skills` to install `validate-fix`, `mend-docs`, and `mend-agent-rules` into `.claude/skills/`.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
