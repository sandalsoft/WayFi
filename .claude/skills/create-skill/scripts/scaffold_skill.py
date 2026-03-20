#!/usr/bin/env python3
"""
Scaffold generator for new skills, commands, and plugins.

Creates the directory structure and template files for a new skill
in the autoclaude-project-template.

Usage:
    python3 scaffold_skill.py <name> --type skill|command|plugin [--scripts] [--references] --description "<desc>"

Examples:
    python3 scaffold_skill.py code-review --type command --description "Review code for bugs and style"
    python3 scaffold_skill.py api-designer --type skill --scripts --references --description "Design REST APIs"
    python3 scaffold_skill.py my-tool --type plugin --description "External tool integration"
"""

import argparse
import os
import re
import sys
from pathlib import Path


def find_project_root() -> Path:
    """Walk up from CWD to find the project root (contains .claude/ directory)."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".claude" / "commands").is_dir():
            return current
        current = current.parent
    # Fallback: assume CWD is the project root
    return Path.cwd()


def validate_name(name: str) -> tuple[bool, str]:
    """Validate skill name follows conventions."""
    if not name:
        return False, "Name cannot be empty"
    if name != name.lower():
        return False, f"Name must be lowercase: '{name}' -> '{name.lower()}'"
    if "_" in name:
        return False, f"Use hyphens, not underscores: '{name}' -> '{name.replace('_', '-')}'"
    if " " in name:
        return False, f"Use hyphens, not spaces: '{name}' -> '{name.replace(' ', '-')}'"
    if not re.match(r'^[a-z][a-z0-9-]*[a-z0-9]$', name) and len(name) > 1:
        return False, f"Name must be kebab-case (lowercase letters, numbers, hyphens): '{name}'"
    if len(name) < 2:
        return False, "Name must be at least 2 characters"
    return True, ""


def check_conflicts(root: Path, name: str) -> list[str]:
    """Check for naming conflicts with existing skills."""
    conflicts = []
    command_file = root / ".claude" / "commands" / f"{name}.md"
    if command_file.exists():
        conflicts.append(f"Command file already exists: {command_file}")
    skill_dir = root / ".claude" / "skills" / name
    if skill_dir.exists():
        conflicts.append(f"Skill directory already exists: {skill_dir}")
    return conflicts


def generate_command_file(name: str, description: str, skill_type: str,
                          has_scripts: bool, has_references: bool) -> str:
    """Generate the content for a command markdown file."""
    title = name.replace("-", " ").title()

    # Build reference lines
    ref_lines = ""
    if has_references:
        ref_lines += f"\nRead `.claude/skills/{name}/references/guide.md` for detailed reference material.\n"
    if has_scripts:
        ref_lines += f"\nHelper scripts are available in `.claude/skills/{name}/scripts/`.\n"

    content = f"""---
name: {name}
description: "{description}"
---

# {title}

[Describe what this skill does, when to use it, and what it produces.]
{ref_lines}
## Inputs

[What information does this skill need from the user? List required and optional inputs.]

## Workflow

### Step 1: [First Step Name]

[Describe what happens in this step.]

### Step 2: [Second Step Name]

[Describe what happens in this step.]

### Step 3: [Validate / Deliver]

[Describe the final output and any validation.]

## Deliverable

[What does this skill produce? Files, output, decisions?]
"""
    return content


def generate_reference_file(name: str) -> str:
    """Generate a starter reference file."""
    title = name.replace("-", " ").title()
    return f"""# {title} — Reference Guide

## Overview

[Detailed reference material for the {name} skill.]

## Key Concepts

[Document the domain knowledge this skill needs.]

## Templates

[Include any templates, checklists, or patterns used by the skill.]

## Common Mistakes

[What should be avoided? What are the gotchas?]
"""


def generate_script_file(name: str) -> str:
    """Generate a starter Python helper script."""
    return f'''#!/usr/bin/env python3
"""
Helper script for the {name} skill.

Usage:
    python3 {name.replace("-", "_")}_helper.py [arguments]
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Helper for the {name} skill"
    )
    parser.add_argument(
        "input",
        nargs="?",
        help="Input argument"
    )

    args = parser.parse_args()

    # TODO: Implement helper logic
    print(f"{{args.input}}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
'''


def generate_plugin_doc(name: str, description: str) -> str:
    """Generate a plugin documentation section."""
    title = name.replace("-", " ").title()
    return f"""
---

## {title}

**Repository:** [owner/repo](https://github.com/owner/repo)

{description}

### Key Features

- [Feature 1]
- [Feature 2]
- [Feature 3]

### Install

```bash
# Installation command here
```

Or use the project setup script:

```bash
bash scripts/setup-plugins.sh
```

### Configuration

[Configuration details here.]
"""


def scaffold(name: str, skill_type: str, description: str,
             has_scripts: bool, has_references: bool) -> dict:
    """Create all files for the new skill. Returns dict of created files."""
    root = find_project_root()
    created = []

    if skill_type in ("command", "skill"):
        # Create command file
        cmd_dir = root / ".claude" / "commands"
        cmd_dir.mkdir(parents=True, exist_ok=True)
        cmd_file = cmd_dir / f"{name}.md"
        cmd_file.write_text(generate_command_file(
            name, description, skill_type, has_scripts, has_references
        ))
        created.append(str(cmd_file.relative_to(root)))

    if skill_type == "skill":
        skill_base = root / ".claude" / "skills" / name

        if has_references:
            ref_dir = skill_base / "references"
            ref_dir.mkdir(parents=True, exist_ok=True)
            ref_file = ref_dir / "guide.md"
            ref_file.write_text(generate_reference_file(name))
            created.append(str(ref_file.relative_to(root)))

        if has_scripts:
            scripts_dir = skill_base / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            script_name = f"{name.replace('-', '_')}_helper.py"
            script_file = scripts_dir / script_name
            script_file.write_text(generate_script_file(name))
            script_file.chmod(0o755)
            created.append(str(script_file.relative_to(root)))

    if skill_type == "plugin":
        plugin_doc = root / "docs" / "plugins.md"
        if plugin_doc.exists():
            existing = plugin_doc.read_text()
            new_section = generate_plugin_doc(name, description)
            plugin_doc.write_text(existing + new_section)
            created.append(f"docs/plugins.md (appended {name} section)")
        else:
            print(f"Warning: docs/plugins.md not found at {plugin_doc}")

    return {
        "root": str(root),
        "name": name,
        "type": skill_type,
        "files_created": created,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Scaffold a new skill, command, or plugin"
    )
    parser.add_argument("name", help="Skill name (kebab-case)")
    parser.add_argument(
        "--type", choices=["skill", "command", "plugin"],
        default="skill", help="Type of addition (default: skill)"
    )
    parser.add_argument(
        "--description", default="",
        help="One-line description of what the skill does"
    )
    parser.add_argument(
        "--scripts", action="store_true",
        help="Include a scripts/ directory with starter script"
    )
    parser.add_argument(
        "--references", action="store_true",
        help="Include a references/ directory with starter guide"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite existing files"
    )

    args = parser.parse_args()

    # Validate name
    valid, error = validate_name(args.name)
    if not valid:
        print(f"Error: {error}")
        sys.exit(1)

    # Check conflicts
    root = find_project_root()
    conflicts = check_conflicts(root, args.name)
    if conflicts and not args.force:
        print("Conflicts found:")
        for c in conflicts:
            print(f"  - {c}")
        print("\nUse --force to overwrite.")
        sys.exit(1)

    # For skill type, default to having both references and scripts
    if args.type == "skill" and not args.scripts and not args.references:
        args.scripts = True
        args.references = True

    # Scaffold
    result = scaffold(
        args.name, args.type, args.description,
        args.scripts, args.references
    )

    # Report
    print(f"\nScaffolded {result['type']}: {result['name']}")
    print(f"Project root: {result['root']}")
    print(f"\nFiles created:")
    for f in result["files_created"]:
        print(f"  {f}")

    print(f"\nNext steps:")
    print(f"  1. Edit .claude/commands/{args.name}.md — fill in the workflow")
    if args.type == "skill" and args.references:
        print(f"  2. Edit .claude/skills/{args.name}/references/guide.md — add reference content")
    if args.type == "skill" and args.scripts:
        print(f"  3. Edit .claude/skills/{args.name}/scripts/ — implement helper logic")
    print(f"  4. Add to CLAUDE.md 'Installed Skills' table")
    print(f"  5. Run: python3 .claude/skills/create-skill/scripts/validate_skill.py {args.name}")


if __name__ == "__main__":
    main()
