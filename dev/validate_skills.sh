#!/bin/bash
#
# Agent Skills Validation Script
#
# Usage:
#   make validate-skills
#   OR
#   bash dev/validate_skills.sh
#
# This script uses `skills-ref`, a CLI tool for validating Agent Skills.
# For more information on `skills-ref`, see:
# https://github.com/agentskills/agentskills/tree/main/skills-ref
#

set -Eeuo pipefail

# Find all SKILL.md files and run validation on their parent directories
for dir in skills .claude/skills; do
	if [[ -d ${dir} ]]; then
		find "${dir}" -type f -name "SKILL.md" -print0 | while IFS= read -r -d '' skill_file; do
			skill_dir="${skill_file%/*}"
			echo "Validating ${skill_dir}..."
			skills-ref validate "${skill_dir}"
		done
	fi
done
