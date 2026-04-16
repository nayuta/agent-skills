#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# ///
"""
audit_docs.py

Static validator for CLAUDE.md and AGENTS.md documentation files.

Validates:
- Marker format (required comment markers exist)
- Table structure (3 columns, separator row, valid format)
- Link validity (all file links resolve)
- Skill completeness (all skills listed unless unlisted: true)
- Agent completeness (all agents listed)
- Synchronization (AGENTS.md body matches CLAUDE.md)

Exit codes:
- 0: All checks passed
- 1: Issues found
- 2: Fatal error
"""
from __future__ import annotations

import argparse
import dataclasses
import re
import sys
from pathlib import Path
from typing import Optional, Sequence


@dataclasses.dataclass
class Finding:
    """Represents a validation finding."""
    severity: str  # ERROR, WARN, INFO
    code: str
    message: str
    file: str
    line: Optional[int] = None


@dataclasses.dataclass
class Report:
    """Validation report containing all findings."""
    findings: list[Finding]

    def has_errors(self) -> bool:
        """Check if report contains any errors."""
        return any(f.severity == "ERROR" for f in self.findings)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str, bool]:
    """
    Parse YAML frontmatter from markdown text.

    Returns: (frontmatter_dict, body, had_frontmatter)
    """
    if not text.startswith("---"):
        return {}, text, False

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text, False

    end_idx = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_idx = i
            break

    if end_idx is None:
        return {}, text, False

    raw_frontmatter = "\n".join(lines[1:end_idx])
    body = "\n".join(lines[end_idx + 1:])

    # Simple key: value parser (no PyYAML dependency)
    data: dict[str, str] = {}
    for line in raw_frontmatter.splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        # Handle boolean values
        value_stripped = value.strip().strip('"').strip()
        if value_stripped.lower() == "true":
            data[key.strip()] = "true"
        elif value_stripped.lower() == "false":
            data[key.strip()] = "false"
        else:
            data[key.strip()] = value_stripped

    return data, body, True


def find_marker_section(text: str, start_marker: str, end_marker: str) -> tuple[Optional[str], Optional[int], Optional[int]]:
    """
    Find content between marker comments.

    Returns: (content, start_line, end_line) or (None, None, None) if not found
    """
    start_pattern = f"<!-- {start_marker} -->"
    end_pattern = f"<!-- {end_marker} -->"

    start_idx = text.find(start_pattern)
    end_idx = text.find(end_pattern)

    if start_idx == -1 or end_idx == -1:
        return None, None, None

    if end_idx <= start_idx:
        return None, None, None

    # Get line numbers
    start_line = text[:start_idx].count("\n") + 1
    end_line = text[:end_idx].count("\n") + 1

    # Extract content between markers
    content_start = start_idx + len(start_pattern)
    content = text[content_start:end_idx]

    return content.strip(), start_line, end_line


def validate_table(table_text: str, file: str, line: int) -> list[Finding]:
    """
    Validate markdown table format.

    Expected format:
    | Name | Description | Link |
    | :--- | :---------- | :--- |
    | ... | ... | ... |
    """
    findings: list[Finding] = []

    if not table_text:
        findings.append(Finding("ERROR", "TABLE_MALFORMED", "Table is empty", file, line))
        return findings

    lines = [l for l in table_text.splitlines() if l.strip()]

    if len(lines) < 2:
        findings.append(Finding("ERROR", "TABLE_MALFORMED", "Table must have at least header and separator rows", file, line))
        return findings

    # Check header row
    header_line = lines[0]
    header_cols = [c.strip() for c in header_line.split("|") if c.strip()]

    if len(header_cols) != 3:
        findings.append(Finding("ERROR", "TABLE_MALFORMED", f"Table must have 3 columns (Name, Description, Link), found {len(header_cols)}", file, line))
        return findings

    # Check separator row
    separator_line = lines[1]
    separator_cols = [c.strip() for c in separator_line.split("|") if c.strip()]

    if len(separator_cols) != 3:
        findings.append(Finding("ERROR", "TABLE_MALFORMED", "Separator row must have 3 columns", file, line + 1))
    else:
        sep_pattern = re.compile(r"^:?-+:?$")
        for col in separator_cols:
            if not sep_pattern.match(col):
                findings.append(Finding("ERROR", "TABLE_MALFORMED", f"Invalid separator syntax: '{col}' (expected pattern like :--- or ---)", file, line + 1))

    # Validate data rows have 3 columns
    for i, data_line in enumerate(lines[2:], start=2):
        data_cols = [c.strip() for c in data_line.split("|") if c.strip()]
        if len(data_cols) != 3:
            findings.append(Finding("ERROR", "TABLE_MALFORMED", f"Data row must have 3 columns, found {len(data_cols)}", file, line + i))

    return findings


def extract_table_links(table_text: str) -> list[str]:
    """Extract file paths from markdown links in table."""
    links: list[str] = []
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')

    for match in link_pattern.finditer(table_text):
        link_path = match.group(2).strip()
        # Filter out external links and anchors
        if not link_path.startswith(("http://", "https://", "#", "mailto:")):
            links.append(link_path)

    return links


def extract_table_names(table_text: str) -> set[str]:
    """Extract names from first column of table."""
    names: set[str] = set()
    lines = [l for l in table_text.splitlines() if l.strip()]

    # Skip header and separator rows
    for line in lines[2:]:
        cols = [c.strip() for c in line.split("|") if c.strip()]
        if cols:
            names.add(cols[0])

    return names


def validate_claude_md(repo_path: Path) -> Report:
    """Validate CLAUDE.md file."""
    findings: list[Finding] = []
    claude_path = repo_path / "CLAUDE.md"

    if not claude_path.exists():
        findings.append(Finding("ERROR", "FILE_MISSING", "CLAUDE.md not found", str(claude_path), None))
        return Report(findings)

    text = claude_path.read_text(encoding="utf-8")

    # Check markers
    required_markers = [
        ("AVAILABLE_SKILLS_START", "AVAILABLE_SKILLS_END"),
        ("AVAILABLE_AGENTS_START", "AVAILABLE_AGENTS_END"),
    ]

    skill_table_text = None
    agent_table_text = None

    for start_marker, end_marker in required_markers:
        content, start_line, end_line = find_marker_section(text, start_marker, end_marker)

        if content is None:
            findings.append(Finding("ERROR", "MARKER_MISSING", f"Missing marker pair: {start_marker} / {end_marker}", str(claude_path), None))
        else:
            # Validate table format
            if "SKILLS" in start_marker:
                skill_table_text = content
                findings.extend(validate_table(content, str(claude_path), start_line + 1))
            elif "AGENTS" in start_marker:
                agent_table_text = content
                findings.extend(validate_table(content, str(claude_path), start_line + 1))

    # Validate links in skills table
    if skill_table_text:
        links = extract_table_links(skill_table_text)
        for link in links:
            link_path = repo_path / link
            if not link_path.exists():
                findings.append(Finding("ERROR", "LINK_BROKEN", f"Broken link: {link}", str(claude_path), None))

    # Validate links in agents table
    if agent_table_text:
        links = extract_table_links(agent_table_text)
        for link in links:
            link_path = repo_path / link
            if not link_path.exists():
                findings.append(Finding("ERROR", "LINK_BROKEN", f"Broken link: {link}", str(claude_path), None))

    # Check for unlisted skills
    skills_dir = repo_path / ".claude/skills"
    if skills_dir.exists():
        listed_skills = extract_table_names(skill_table_text) if skill_table_text else set()

        for skill_dir in skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue

            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue

            # Parse frontmatter to check for unlisted flag
            skill_text = skill_md.read_text(encoding="utf-8")
            frontmatter, _, had_fm = parse_frontmatter(skill_text)

            # Skip if unlisted: true
            if frontmatter.get("unlisted") == "true":
                continue

            skill_name = frontmatter.get("name", skill_dir.name)

            if skill_name not in listed_skills:
                findings.append(Finding("ERROR", "SKILL_UNLISTED", f"Skill '{skill_name}' not listed in CLAUDE.md table", str(skill_md), None))

    # Check for unlisted agents
    agents_dir = repo_path / ".claude/agents"
    if agents_dir.exists():
        listed_agents = extract_table_names(agent_table_text) if agent_table_text else set()

        for agent_file in agents_dir.glob("*.md"):
            # Parse frontmatter
            agent_text = agent_file.read_text(encoding="utf-8")
            frontmatter, _, had_fm = parse_frontmatter(agent_text)

            # Skip if unlisted: true
            if frontmatter.get("unlisted") == "true":
                continue

            agent_name = frontmatter.get("name", agent_file.stem)

            if agent_name not in listed_agents:
                findings.append(Finding("ERROR", "AGENT_UNLISTED", f"Agent '{agent_name}' not listed in CLAUDE.md table", str(agent_file), None))

    return Report(findings)


def validate_agents_sync(repo_path: Path) -> Report:
    """Validate that AGENTS.md body matches CLAUDE.md."""
    findings: list[Finding] = []

    claude_path = repo_path / "CLAUDE.md"
    agents_path = repo_path / "AGENTS.md"

    # Skip check if AGENTS.md doesn't exist
    if not agents_path.exists():
        return Report(findings)

    if not claude_path.exists():
        return Report(findings)  # Already reported in validate_claude_md

    claude_text = claude_path.read_text(encoding="utf-8")
    agents_text = agents_path.read_text(encoding="utf-8")

    # Extract body (everything after first line)
    claude_lines = claude_text.splitlines()
    agents_lines = agents_text.splitlines()

    # Validate first-line headers
    if claude_lines and claude_lines[0].strip() != "# CLAUDE.md":
        findings.append(Finding("WARN", "HEADER_UNEXPECTED", f"Expected first line '# CLAUDE.md', found '{claude_lines[0].strip()}'", str(claude_path), 1))
    if agents_lines and agents_lines[0].strip() != "# AGENTS.md":
        findings.append(Finding("WARN", "HEADER_UNEXPECTED", f"Expected first line '# AGENTS.md', found '{agents_lines[0].strip()}'", str(agents_path), 1))

    claude_body = "\n".join(claude_lines[1:]) if len(claude_lines) > 1 else ""
    agents_body = "\n".join(agents_lines[1:]) if len(agents_lines) > 1 else ""

    if claude_body.strip() != agents_body.strip():
        findings.append(Finding("ERROR", "AGENTS_DESYNC", "AGENTS.md body differs from CLAUDE.md (excluding first line)", str(agents_path), 2))

    return Report(findings)


def format_report(report: Report) -> str:
    """Format report as human-readable text."""
    if not report.findings:
        return "All checks passed."

    lines: list[str] = []
    for finding in report.findings:
        loc = f"{finding.file}:{finding.line}" if finding.line else finding.file
        lines.append(f"[{finding.severity}] {finding.code} @ {loc} :: {finding.message}")

    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Validate CLAUDE.md and AGENTS.md documentation files.")
    parser.add_argument("repo_path", help="Path to repository root containing CLAUDE.md")
    args = parser.parse_args(argv)

    repo_path = Path(args.repo_path).resolve()

    if not repo_path.exists():
        print(f"Error: Path does not exist: {repo_path}", file=sys.stderr)
        return 2

    if not repo_path.is_dir():
        print(f"Error: Path is not a directory: {repo_path}", file=sys.stderr)
        return 2

    # Run validations
    claude_report = validate_claude_md(repo_path)
    sync_report = validate_agents_sync(repo_path)

    # Combine findings
    all_findings = claude_report.findings + sync_report.findings
    combined_report = Report(all_findings)

    # Print report
    print(format_report(combined_report))

    # Return exit code
    if combined_report.has_errors():
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
