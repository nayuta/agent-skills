#!/usr/bin/env python3
"""
test_audit_docs.py

Test suite for audit_docs.py script.
Tests the 6 categories of static checks plus exit code behavior.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from textwrap import dedent


def test_valid_claude_passes(tmp_path: Path) -> None:
    """Test that a valid CLAUDE.md with all skills and agents listed passes."""
    # Create valid skill
    skill_dir = tmp_path / ".claude/skills/listed-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(dedent("""\
        ---
        name: listed-skill
        description: A listed skill for testing
        ---

        # Listed Skill

        This skill is properly listed in the table.
        """))

    # Create valid agent
    agent_file = tmp_path / ".claude/agents/example-agent.md"
    agent_file.parent.mkdir(parents=True, exist_ok=True)
    agent_file.write_text(dedent("""\
        ---
        name: example-agent
        description: An example agent for testing
        ---

        # Example Agent

        This agent is properly listed.
        """))

    # Create valid CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |
        | listed-skill | A listed skill for testing | [.claude/skills/listed-skill/SKILL.md](.claude/skills/listed-skill/SKILL.md) |

        <!-- AVAILABLE_SKILLS_END -->

        ## Available Agents

        <!-- AVAILABLE_AGENTS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |
        | example-agent | An example agent for testing | [.claude/agents/example-agent.md](.claude/agents/example-agent.md) |

        <!-- AVAILABLE_AGENTS_END -->
        """))

    # Run audit_docs.py
    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should pass with exit code 0
    assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}. Output: {result.stdout}\nError: {result.stderr}"


def test_missing_marker_fails(tmp_path: Path) -> None:
    """Test that missing or malformed markers cause MARKER_MISSING error."""
    # Create CLAUDE.md without proper markers
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        Some text but no markers.
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should fail with MARKER_MISSING error
    assert result.returncode == 1
    assert "MARKER_MISSING" in result.stdout or "marker" in result.stdout.lower()


def test_invalid_table_format_fails(tmp_path: Path) -> None:
    """Test that malformed table structure causes TABLE_MALFORMED error."""
    # Create CLAUDE.md with invalid table (only 2 columns instead of 3)
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description |
        | :--- | :---------- |
        | test-skill | A test skill |

        <!-- AVAILABLE_SKILLS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should fail with TABLE_MALFORMED error
    assert result.returncode == 1
    assert "TABLE_MALFORMED" in result.stdout or "table" in result.stdout.lower()


def test_broken_link_fails(tmp_path: Path) -> None:
    """Test that broken file links cause LINK_BROKEN error."""
    # Create CLAUDE.md with link to non-existent file
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |
        | missing-skill | This skill doesn't exist | [.claude/skills/missing-skill/SKILL.md](.claude/skills/missing-skill/SKILL.md) |

        <!-- AVAILABLE_SKILLS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should fail with LINK_BROKEN error
    assert result.returncode == 1
    assert "LINK_BROKEN" in result.stdout or "broken" in result.stdout.lower()


def test_orphan_skill_fails(tmp_path: Path) -> None:
    """Test that skills not listed in the table cause SKILL_UNLISTED error."""
    # Create skill that's not listed in CLAUDE.md
    skill_dir = tmp_path / ".claude/skills/orphan-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(dedent("""\
        ---
        name: orphan-skill
        description: This skill is not listed in the table
        ---

        # Orphan Skill

        This should trigger SKILL_UNLISTED.
        """))

    # Create CLAUDE.md without this skill
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_SKILLS_END -->

        ## Available Agents

        <!-- AVAILABLE_AGENTS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_AGENTS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should fail with SKILL_UNLISTED error
    assert result.returncode == 1
    assert "SKILL_UNLISTED" in result.stdout or "unlisted" in result.stdout.lower()


def test_unlisted_frontmatter_ignored(tmp_path: Path) -> None:
    """Test that skills with unlisted: true in frontmatter are ignored."""
    # Create skill with unlisted: true
    skill_dir = tmp_path / ".claude/skills/unlisted-skill"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(dedent("""\
        ---
        name: unlisted-skill
        description: This skill has unlisted flag
        unlisted: true
        ---

        # Unlisted Skill

        This should NOT trigger SKILL_UNLISTED.
        """))

    # Create CLAUDE.md without this skill
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_SKILLS_END -->

        ## Available Agents

        <!-- AVAILABLE_AGENTS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_AGENTS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should pass because unlisted skills are ignored
    assert result.returncode == 0


def test_agents_desync_fails(tmp_path: Path) -> None:
    """Test that AGENTS.md differing from CLAUDE.md causes AGENTS_DESYNC error."""
    # Create CLAUDE.md
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_SKILLS_END -->
        """))

    # Create AGENTS.md with different content
    (tmp_path / "AGENTS.md").write_text(dedent("""\
        # AGENTS.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |
        | extra-skill | This is extra | [link](link) |

        <!-- AVAILABLE_SKILLS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should fail with AGENTS_DESYNC error
    assert result.returncode == 1
    assert "AGENTS_DESYNC" in result.stdout or "desync" in result.stdout.lower() or "differ" in result.stdout.lower()


def test_exit_code_clean(tmp_path: Path) -> None:
    """Test that clean validation returns exit code 0."""
    # Create minimal valid setup
    (tmp_path / "CLAUDE.md").write_text(dedent("""\
        # CLAUDE.md

        ## Available Skills

        <!-- AVAILABLE_SKILLS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_SKILLS_END -->

        ## Available Agents

        <!-- AVAILABLE_AGENTS_START -->

        | Name | Description | Link |
        | :--- | :---------- | :--- |

        <!-- AVAILABLE_AGENTS_END -->
        """))

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should return 0
    assert result.returncode == 0


def test_exit_code_issues(tmp_path: Path) -> None:
    """Test that issues found returns exit code 1."""
    # Create CLAUDE.md with missing markers
    (tmp_path / "CLAUDE.md").write_text("# CLAUDE.md\n\nNo markers here.")

    script = Path(__file__).parent.parent / "scripts/audit_docs.py"
    result = subprocess.run(
        [sys.executable, str(script), str(tmp_path)],
        capture_output=True,
        text=True,
    )

    # Should return 1
    assert result.returncode == 1
