.PHONY: setup lint format validate-skills

setup:
	npx skills add ubie-inc/agent-skills --skill validate-fix --skill mend-docs --skill mend-agent-rules -y

lint:
	shellcheck skills/*/scripts/*.sh
	markdownlint "**/*.md" --ignore node_modules
	prettier --check "**/*.{json,yaml,yml}" --ignore-path .gitignore

format:
	prettier --write "**/*.{md,json,yaml,yml}" --ignore-path .gitignore

validate-skills:
	uv run bash dev/validate_skills.sh
