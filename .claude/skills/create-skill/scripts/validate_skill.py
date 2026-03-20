#!/usr/bin/env python3
"""
Validate that a skill is properly structured and registered.

Checks file existence, frontmatter, references, registration in CLAUDE.md,
and other structural requirements.

Usage:
    python3 validate_skill.py <name>
    python3 validate_skill.py session-handoff
    python3 validate_skill.py --all
"""

import argparse
import re
import sys
from pathlib import Path


class ValidationResult:
    def __init__(self):
        self.checks = []
        self.errors = []
        self.warnings = []

    def passed(self, message: str):
        self.checks.append(("PASS", message))

    def failed(self, message: str):
        self.checks.append(("FAIL", message))
        self.errors.append(message)

    def warn(self, message: str):
        self.checks.append(("WARN", message))
        self.warnings.append(message)

    @property
    def score(self) -> int:
        total = len(self.checks)
        if total == 0:
            return 0
        passed = sum(1 for status, _ in self.checks if status == "PASS")
        return int((passed / total) * 100)

    def report(self) -> str:
        lines = []
        for status, message in self.checks:
            icon = {"PASS": "[OK]", "FAIL": "[FAIL]", "WARN": "[WARN]"}[status]
            lines.append(f"  {icon} {message}")
        return "\n".join(lines)


def find_project_root() -> Path:
    """Walk up from CWD to find the project root."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude" / "commands").is_dir():
            return current
        current = current.parent
    return Path.cwd()


def parse_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from markdown content."""
    match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not match:
        return {}

    fm = {}
    for line in match.group(1).split("\n"):
        line = line.strip()
        if ":" in line:
            key, _, value = line.partition(":")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if value:
                fm[key] = value
            else:
                # Multi-line value (like description with |), capture next lines
                pass
    return fm


def validate_skill(name: str, root: Path) -> ValidationResult:
    """Run all validation checks on a skill."""
    result = ValidationResult()

    # 1. Command file exists
    cmd_file = root / ".claude" / "commands" / f"{name}.md"
    if cmd_file.exists():
        result.passed(f"Command file exists: .claude/commands/{name}.md")
    else:
        result.failed(f"Command file missing: .claude/commands/{name}.md")
        return result  # Can't check much else without the file

    # 2. Read and parse frontmatter
    content = cmd_file.read_text()
    fm = parse_frontmatter(content)

    if fm.get("name"):
        result.passed(f"Frontmatter has 'name' field: {fm['name']}")
    else:
        result.failed("Frontmatter missing 'name' field")

    if fm.get("description"):
        result.passed("Frontmatter has 'description' field")
    else:
        result.failed("Frontmatter missing 'description' field")

    # 3. Name matches filename
    if fm.get("name") == name:
        result.passed(f"Frontmatter name matches filename: {name}")
    elif fm.get("name"):
        result.failed(f"Name mismatch: frontmatter says '{fm['name']}' but file is '{name}.md'")

    # 4. Description quality
    desc = fm.get("description", "")
    if len(desc) > 500:
        result.warn(f"Description is {len(desc)} chars (recommended: under 500)")
    elif len(desc) < 20:
        result.warn(f"Description is only {len(desc)} chars (too short for good discovery)")
    else:
        result.passed(f"Description length is good ({len(desc)} chars)")

    # 5. Check for TODO/placeholder text
    todo_matches = re.findall(r'\[TODO:.*?\]', content)
    placeholder_matches = re.findall(r'\[(?:describe|explain|add|fill|replace|insert).*?\]', content, re.IGNORECASE)
    all_placeholders = todo_matches + placeholder_matches
    if all_placeholders:
        result.failed(f"Found {len(all_placeholders)} placeholder(s): {', '.join(all_placeholders[:3])}")
    else:
        result.passed("No TODO/placeholder text found")

    # 6. Check for workflow section
    if re.search(r'^##\s+Workflow', content, re.MULTILINE):
        result.passed("Has a Workflow section")
    elif re.search(r'^##\s+(Steps|Process|How|Procedure)', content, re.MULTILINE):
        result.passed("Has a workflow-like section")
    else:
        result.warn("No Workflow section found (recommended for clarity)")

    # 7. Check supporting directories
    skill_dir = root / ".claude" / "skills" / name
    has_skill_dir = skill_dir.exists()

    if has_skill_dir:
        result.passed(f"Skill directory exists: .claude/skills/{name}/")

        # Check references
        ref_dir = skill_dir / "references"
        if ref_dir.exists():
            ref_files = list(ref_dir.glob("*"))
            if ref_files:
                result.passed(f"References directory has {len(ref_files)} file(s)")
            else:
                result.failed("References directory exists but is empty")

        # Check scripts
        scripts_dir = skill_dir / "scripts"
        if scripts_dir.exists():
            script_files = list(scripts_dir.glob("*"))
            if script_files:
                result.passed(f"Scripts directory has {len(script_files)} file(s)")
                # Check scripts have shebangs
                for sf in script_files:
                    if sf.suffix in (".py", ".sh"):
                        first_line = sf.read_text().split("\n")[0] if sf.read_text() else ""
                        if first_line.startswith("#!"):
                            result.passed(f"Script {sf.name} has shebang")
                        else:
                            result.warn(f"Script {sf.name} missing shebang line")
            else:
                result.failed("Scripts directory exists but is empty")

    # 8. Check referenced files resolve
    # Skip references that contain template variables like <name>, <slug>, etc.
    file_refs = re.findall(r'`(\.claude/skills/[^`]+)`', content)
    for ref_path in file_refs:
        if re.search(r'<[^>]+>', ref_path):
            continue  # Template example, not a real reference
        full_path = root / ref_path
        if full_path.exists():
            result.passed(f"Referenced file exists: {ref_path}")
        else:
            result.failed(f"Referenced file missing: {ref_path}")

    # 9. Check CLAUDE.md registration
    claude_md = root / "CLAUDE.md"
    if claude_md.exists():
        claude_content = claude_md.read_text()
        # Look for the skill in the table (as /name or `name`)
        pattern = rf'[/`]{re.escape(name)}[`\s|]'
        if re.search(pattern, claude_content):
            result.passed(f"Registered in CLAUDE.md")
        else:
            result.failed(f"Not registered in CLAUDE.md skills table")
    else:
        result.warn("CLAUDE.md not found — cannot check registration")

    return result


def list_all_skills(root: Path) -> list[str]:
    """List all command files to discover skills."""
    commands_dir = root / ".claude" / "commands"
    if not commands_dir.exists():
        return []
    return [f.stem for f in commands_dir.glob("*.md")]


def main():
    parser = argparse.ArgumentParser(
        description="Validate skill structure and registration"
    )
    parser.add_argument(
        "name", nargs="?",
        help="Skill name to validate (e.g., 'session-handoff')"
    )
    parser.add_argument(
        "--all", action="store_true",
        help="Validate all installed skills"
    )

    args = parser.parse_args()

    root = find_project_root()

    if args.all:
        skills = list_all_skills(root)
        if not skills:
            print("No skills found.")
            sys.exit(0)

        total_errors = 0
        for skill_name in sorted(skills):
            result = validate_skill(skill_name, root)
            print(f"\n{'=' * 50}")
            print(f"Skill: {skill_name} (Score: {result.score}%)")
            print(f"{'=' * 50}")
            print(result.report())
            total_errors += len(result.errors)

        print(f"\n{'=' * 50}")
        print(f"Validated {len(skills)} skill(s), {total_errors} error(s) total")
        sys.exit(1 if total_errors > 0 else 0)

    elif args.name:
        result = validate_skill(args.name, root)
        print(f"\nValidation: {args.name} (Score: {result.score}%)")
        print(f"{'-' * 40}")
        print(result.report())

        if result.errors:
            print(f"\n{len(result.errors)} error(s) found:")
            for e in result.errors:
                print(f"  - {e}")
            sys.exit(1)
        elif result.warnings:
            print(f"\n{len(result.warnings)} warning(s) — skill is usable but could be improved")
            sys.exit(0)
        else:
            print(f"\nAll checks passed.")
            sys.exit(0)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
