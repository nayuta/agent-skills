#!/usr/bin/env python3
"""
skill_audit.py

Static auditor for Claude Code / Agent Skills directories.

What it does:
- discovers skills by finding SKILL.md
- validates frontmatter and body shape
- checks references to sibling markdown/resources
- scans for risky patterns: hardcoded secrets, path traversal, network access,
  adversarial instructions, Windows-style paths
- emits human-readable or JSON reports

Surface modes:
- claude-code : tolerant of missing frontmatter fields because Claude Code docs
  describe frontmatter fields as optional
- agent-api   : strict about required name/description metadata

This is intentionally static. Dynamic evaluation (triggering accuracy, output
quality, latency, token use) should be layered on top with your runtime harness.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


SEVERITY_ORDER = {"INFO": 0, "WARN": 1, "ERROR": 2}

NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
WINDOWS_PATH_RE = re.compile(r"[A-Za-z]:\\")
HTTP_RE = re.compile(r"https?://|requests\.(get|post|put|delete|patch)|urllib\.|fetch\(|curl\s", re.IGNORECASE)
PATH_TRAVERSAL_RE = re.compile(r"(^|[^A-Za-z0-9_])\.\./")
HARDCODED_SECRET_RE = re.compile(
    r"(api[_-]?key|secret|token|password)\s*[:=]\s*[\"'][^\"']{8,}[\"']",
    re.IGNORECASE,
)
ADVERSARIAL_INSTRUCTION_RE = re.compile(
    r"(ignore safety|hide (your|the) actions|do not tell the user|exfiltrat|bypass|override safety|don't mention)",
    re.IGNORECASE,
)
XML_TAG_RE = re.compile(r"<[^>]+>")

FRONTMATTER_SPLIT_RE = re.compile(r"^---\s*$", re.MULTILINE)
MARKDOWN_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


@dataclasses.dataclass
class Finding:
    severity: str
    code: str
    message: str
    file: str
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class SkillReport:
    skill_dir: str
    surface: str
    name: Optional[str]
    description: Optional[str]
    findings: List[Finding]
    score: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill_dir": self.skill_dir,
            "surface": self.surface,
            "name": self.name,
            "description": self.description,
            "score": self.score,
            "findings": [f.to_dict() for f in self.findings],
        }


def discover_skill_dirs(path: Path) -> List[Path]:
    path = path.resolve()
    if path.is_file() and path.name == "SKILL.md":
        return [path.parent]
    if path.is_dir() and (path / "SKILL.md").exists():
        return [path]
    return sorted({p.parent for p in path.rglob("SKILL.md")})


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str, bool]:
    """
    Returns: (frontmatter_dict, body, had_frontmatter_block)
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
    body = "\n".join(lines[end_idx + 1 :])

    if yaml is None:
        # Minimal fallback parser for simple key: value lines only.
        # Detect block scalars (|, >, |-) and nested mappings (indented lines)
        # which this parser cannot handle reliably.
        data: Dict[str, Any] = {}
        for line in raw_frontmatter.splitlines():
            stripped = line.rstrip()
            # Indented lines indicate nested mappings or block scalar content
            if stripped and stripped[0] == " ":
                return (
                    {"__parse_error__": "frontmatter contains nested mappings or block scalars; install PyYAML for full support"},
                    body,
                    True,
                )
            if ":" not in stripped:
                continue
            k, v = stripped.split(":", 1)
            v_stripped = v.strip()
            # Block scalar indicators on a key line (e.g. "description: |")
            if v_stripped in ("|", ">", "|-", ">-", "|+", ">+"):
                return (
                    {"__parse_error__": "frontmatter contains block scalars; install PyYAML for full support"},
                    body,
                    True,
                )
            data[k.strip()] = v_stripped.strip('"').strip("'")
        return data, body, True

    try:
        loaded = yaml.safe_load(raw_frontmatter)
        if loaded is None:
            loaded = {}
        if not isinstance(loaded, dict):
            return {"__parse_error__": "frontmatter is not a mapping"}, body, True
        return loaded, body, True
    except Exception as e:  # pragma: no cover
        return {"__parse_error__": str(e)}, body, True


def line_number_of(text: str, pattern: str) -> Optional[int]:
    idx = text.find(pattern)
    if idx == -1:
        return None
    return text[:idx].count("\n") + 1


def add_findings(findings: List[Finding], items: Iterable[Finding]) -> None:
    findings.extend(items)


def validate_frontmatter(skill_dir: Path, text: str, frontmatter: Dict[str, Any], body: str, had_frontmatter: bool, surface: str) -> List[Finding]:
    findings: List[Finding] = []
    file = str(skill_dir / "SKILL.md")

    if not had_frontmatter:
        sev = "WARN" if surface == "claude-code" else "ERROR"
        findings.append(Finding(sev, "missing_frontmatter", "SKILL.md has no YAML frontmatter block.", file, 1))
        return findings

    if "__parse_error__" in frontmatter:
        findings.append(
            Finding("ERROR", "invalid_frontmatter_yaml", f"Frontmatter could not be parsed: {frontmatter['__parse_error__']}", file, 1)
        )
        return findings

    name = frontmatter.get("name")
    description = frontmatter.get("description")

    if surface == "agent-api":
        if not name:
            findings.append(Finding("ERROR", "missing_name", "Agent/API mode requires a frontmatter `name`.", file, 1))
        if not description:
            findings.append(Finding("ERROR", "missing_description", "Agent/API mode requires a frontmatter `description`.", file, 1))
    else:
        if not description:
            findings.append(Finding("WARN", "missing_description", "Claude Code mode recommends a frontmatter `description` for reliable auto-discovery.", file, 1))

    if name is not None:
        if not isinstance(name, str):
            findings.append(Finding("ERROR", "invalid_name_type", "`name` must be a string.", file, 1))
        else:
            if not NAME_RE.match(name):
                findings.append(
                    Finding(
                        "ERROR",
                        "invalid_name_format",
                        "`name` must match ^[a-z0-9-]{1,64}$.",
                        file,
                        line_number_of(text, "name:"),
                    )
                )
            if "claude" in name or "anthropic" in name:
                findings.append(
                    Finding(
                        "ERROR",
                        "reserved_name_term",
                        "`name` should not contain reserved words `claude` or `anthropic`.",
                        file,
                        line_number_of(text, "name:"),
                    )
                )
            if XML_TAG_RE.search(name):
                findings.append(Finding("ERROR", "name_contains_xml", "`name` must not contain XML tags.", file, line_number_of(text, "name:")))

    if description is not None:
        if not isinstance(description, str):
            findings.append(Finding("ERROR", "invalid_description_type", "`description` must be a string.", file, 1))
        else:
            if surface == "agent-api" and not description.strip():
                findings.append(Finding("ERROR", "empty_description", "`description` must be non-empty.", file, line_number_of(text, "description:")))
            if len(description) > 1024:
                findings.append(Finding("ERROR", "description_too_long", "`description` exceeds 1024 characters.", file, line_number_of(text, "description:")))
            if XML_TAG_RE.search(description):
                findings.append(Finding("ERROR", "description_contains_xml", "`description` must not contain XML tags.", file, line_number_of(text, "description:")))
            if re.search(r"\b(I|you)\b", description):
                findings.append(Finding("WARN", "description_pov", "Description is usually clearer in third person for discovery.", file, line_number_of(text, "description:")))

    body_lines = body.splitlines()
    if len(body_lines) == 0 or not body.strip():
        findings.append(Finding("ERROR", "missing_body", "SKILL.md has no instruction body after frontmatter.", file, 1))
    elif len(body_lines) > 500:
        findings.append(Finding("WARN", "body_too_long", f"SKILL.md body has {len(body_lines)} lines; recommended budget is under 500.", file, 1))

    return findings


def validate_links(skill_dir: Path, body: str) -> List[Finding]:
    findings: List[Finding] = []
    file = skill_dir / "SKILL.md"
    for match in MARKDOWN_LINK_RE.finditer(body):
        target = match.group(1).strip()
        if target.startswith(("http://", "https://", "#", "mailto:")):
            continue
        clean_target = target.split("#", 1)[0].split("?", 1)[0]
        if not clean_target:
            continue
        target_path = (skill_dir / clean_target).resolve()
        try:
            target_path.relative_to(skill_dir.resolve())
        except Exception:
            findings.append(Finding("WARN", "link_outside_skill", f"Link points outside the skill directory: {target}", str(file), body[:match.start()].count("\n") + 1))
            continue
        if not target_path.exists():
            findings.append(Finding("ERROR", "broken_link", f"Referenced file does not exist: {target}", str(file), body[:match.start()].count("\n") + 1))
    return findings


def scan_file_for_patterns(path: Path, root: Path) -> List[Finding]:
    findings: List[Finding] = []
    text = read_text(path)
    try:
        rel = str(path.relative_to(root))
    except ValueError:
        rel = str(path)
    lines = text.splitlines()

    # Determine if this is a security-domain skill by checking the skill name
    is_security_skill = root.name.startswith("security-")

    for i, line in enumerate(lines, start=1):
        if WINDOWS_PATH_RE.search(line):
            findings.append(Finding("WARN", "windows_path", "Windows-style path found; prefer portable relative paths.", rel, i))
        if HTTP_RE.search(line):
            # Skip network_access warnings for security skills as they legitimately discuss network patterns
            if not is_security_skill:
                findings.append(Finding("WARN", "network_access", "Potential network access pattern found.", rel, i))
        if PATH_TRAVERSAL_RE.search(line):
            findings.append(Finding("WARN", "path_traversal", "Potential path traversal / outside-directory access pattern found.", rel, i))
        if HARDCODED_SECRET_RE.search(line):
            # Skip hardcoded_secret warnings for security skills as they contain example vulnerabilities
            if not is_security_skill:
                findings.append(Finding("ERROR", "hardcoded_secret", "Potential hardcoded secret found.", rel, i))
        if ADVERSARIAL_INSTRUCTION_RE.search(line):
            # Skip adversarial_instruction warnings for security skills as they discuss security attack patterns
            if not is_security_skill:
                findings.append(Finding("ERROR", "adversarial_instruction", "Potential adversarial or concealment instruction found.", rel, i))
        if re.search(r"allowed-tools:\s*\*\s*$", line):
            findings.append(Finding("WARN", "broad_allowed_tools", "Bare wildcard (*) in allowed-tools grants all tools; review for excessive privilege.", rel, i))
        if re.search(r"\b(today|yesterday|tomorrow|current policy|latest)\b", line, re.IGNORECASE):
            findings.append(Finding("INFO", "time_sensitive_content", "Time-sensitive wording found; consider externalizing volatile content.", rel, i))
    return findings


_SKIP_DIRS = {"__pycache__", ".git", ".mypy_cache", ".ruff_cache", "node_modules"}
_SKIP_SUFFIXES = {
    # Compiled Python
    ".pyc", ".pyo", ".pyd",
    # Images
    ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg", ".webp", ".tiff",
    # Archives and binaries
    ".gz", ".bz2", ".xz", ".zip", ".tar", ".tgz", ".whl", ".egg",
    ".so", ".dylib", ".dll", ".exe", ".bin", ".a", ".o",
    # Audio / video
    ".mp3", ".mp4", ".wav", ".ogg", ".mov", ".avi",
    # Fonts
    ".woff", ".woff2", ".ttf", ".otf", ".eot",
    # Database / data blobs
    ".db", ".sqlite", ".pkl", ".parquet", ".npy", ".npz",
}
_MAX_FILE_SIZE = 1024 * 1024  # 1 MB


def collect_files(skill_dir: Path) -> List[Path]:
    files: List[Path] = []
    for path in skill_dir.rglob("*"):
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in _SKIP_SUFFIXES:
            continue
        if not path.is_file():
            continue
        if path.stat().st_size > _MAX_FILE_SIZE:
            continue
        files.append(path)
    return sorted(files)


def compute_score(findings: Sequence[Finding]) -> int:
    score = 100
    for finding in findings:
        if finding.severity == "ERROR":
            score -= 10
        elif finding.severity == "WARN":
            score -= 3
        else:
            score -= 0
    return max(score, 0)


def audit_skill(skill_dir: Path, surface: str) -> SkillReport:
    skill_md = skill_dir / "SKILL.md"
    text = read_text(skill_md)
    frontmatter, body, had_frontmatter = parse_frontmatter(text)
    findings: List[Finding] = []

    add_findings(findings, validate_frontmatter(skill_dir, text, frontmatter, body, had_frontmatter, surface))
    add_findings(findings, validate_links(skill_dir, body))

    for file in collect_files(skill_dir):
        add_findings(findings, scan_file_for_patterns(file, skill_dir))

    findings.sort(key=lambda f: (SEVERITY_ORDER[f.severity], f.file, f.line or 0), reverse=True)

    return SkillReport(
        skill_dir=str(skill_dir),
        surface=surface,
        name=frontmatter.get("name") if isinstance(frontmatter, dict) else None,
        description=frontmatter.get("description") if isinstance(frontmatter, dict) else None,
        findings=findings,
        score=compute_score(findings),
    )


def format_human(reports: Sequence[SkillReport]) -> str:
    chunks: List[str] = []
    for report in reports:
        chunks.append(f"{report.skill_dir}\n  surface: {report.surface}\n  name: {report.name!r}\n  score: {report.score}")
        if not report.findings:
            chunks.append("  findings: none")
            continue
        for finding in report.findings:
            loc = f"{finding.file}:{finding.line}" if finding.line else finding.file
            chunks.append(f"  - [{finding.severity}] {finding.code} @ {loc} :: {finding.message}")
        chunks.append("")
    return "\n".join(chunks).rstrip()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Audit Claude skills directories.")
    parser.add_argument("path", help="Skill directory, SKILL.md file, or a directory to search recursively.")
    parser.add_argument(
        "--surface",
        choices=["claude-code", "agent-api"],
        default="claude-code",
        help="Validation mode. Claude Code is tolerant; agent-api is strict.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    target = Path(args.path)
    if not target.exists():
        print(f"Path does not exist: {target}", file=sys.stderr)
        return 2

    skill_dirs = discover_skill_dirs(target)
    if not skill_dirs:
        print(f"No SKILL.md files found under: {target}", file=sys.stderr)
        return 2

    reports = [audit_skill(skill_dir, args.surface) for skill_dir in skill_dirs]

    if args.json:
        print(json.dumps({"reports": [r.to_dict() for r in reports]}, indent=2))
    else:
        print(format_human(reports))

    worst = min((r.score for r in reports), default=100)
    if worst < 70:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
