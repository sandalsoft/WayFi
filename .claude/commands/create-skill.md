---
name: create-skill
description: "Scaffold and register new skills, commands, or plugins in this template. Use when adding a new slash command, creating a skill with supporting references/scripts, or integrating a plugin. Handles file creation, frontmatter generation, CLAUDE.md registration, and structural validation. Triggers on 'add a skill', 'create a command', 'new skill', 'add plugin', 'scaffold skill', or when the user wants to extend the template's capabilities."
---

# Create Skill

Scaffold new skills, commands, and plugins into this template with correct structure, conventions, and registration.

## Thinking Framework

Before scaffolding, determine:

1. **What type of addition?** A skill (command + references + scripts), a command-only (standalone `.md`), or a plugin (external tool integration in `docs/plugins.md`)?
2. **What's the scope?** Does this need helper scripts? Reference docs? Both? Neither?
3. **Does it overlap?** Check installed skills in CLAUDE.md — don't duplicate existing capabilities.

## Inputs

Ask the user for (if not provided via `$ARGUMENTS`):

| Input | Required | Example |
|-------|----------|---------|
| **Name** | Yes | `api-designer`, `code-review` |
| **Type** | Yes | `skill` (full), `command` (standalone), `plugin` (external) |
| **Purpose** | Yes | One sentence: what does it do? |
| **Trigger phrases** | Recommended | When should Claude activate this? |
| **Needs scripts?** | For skills | Will it have helper scripts? |
| **Needs references?** | For skills | Will it have reference docs? |

If `$ARGUMENTS` contains a name and description, infer the type and proceed. Default to `skill` (full) when ambiguous.

## Workflow

### Phase 1: Pre-flight Checks

1. **Check for conflicts.** Read CLAUDE.md and scan `.claude/commands/` for name collisions:

```bash
ls .claude/commands/ | grep -i "$NAME"
```

2. **Validate the name.** Must be lowercase, hyphen-separated, no underscores or spaces. Examples: `code-review`, `api-designer`, `deploy-checklist`. Reject names like `mySkill`, `code_review`, or `Code Review`.

3. **Confirm type and scope** with the user using `AskUserQuestion` before creating files.

### Phase 2: Scaffold Files

Read the anatomy reference for the selected type:

- `.claude/skills/create-skill/references/skill-anatomy.md` — structure guide for all three types

Then create the appropriate files:

#### For type: `command` (standalone command)

Create one file:

```
.claude/commands/<name>.md
```

Use the command template structure:

```markdown
---
name: <name>
description: "<one-line description with trigger phrases>"
---

# <Title>

<Purpose paragraph>

## Workflow

### Step 1: ...

## Deliverable

...
```

The frontmatter is critical — the `description` field is what Claude uses to decide when to activate the skill. Write it carefully:
- Start with a verb phrase: "Generate...", "Analyze...", "Create..."
- Include 3-5 trigger phrases the user might say
- Keep it under 300 characters

#### For type: `skill` (full skill with supporting files)

Create the command file AND supporting directories:

```
.claude/commands/<name>.md
.claude/skills/<name>/references/     (if references needed)
.claude/skills/<name>/scripts/        (if scripts needed)
```

Run the scaffold script:

```bash
python3 .claude/skills/create-skill/scripts/scaffold_skill.py "<name>" --type skill [--scripts] [--references] --description "<description>"
```

The scaffold script creates the directory structure and generates template files. After it runs, fill in the generated templates with actual content.

#### For type: `plugin` (external tool integration)

Plugins don't get their own command file. Instead:
1. Add a section to `docs/plugins.md`
2. If the plugin needs a setup step, add it to `scripts/setup-plugins.sh`
3. Optionally create a thin command wrapper in `.claude/commands/<name>.md` if the plugin benefits from guided usage

### Phase 3: Write the Command File

This is the most important file. Follow these principles:

**Structure matters.** Every command file should have:
1. YAML frontmatter with `name` and `description`
2. A title heading explaining what the skill does
3. A workflow section with numbered steps
4. Clear references to any supporting files (use relative paths)
5. A "NEVER Do" section for guardrails (optional but recommended for complex skills)

**Description is discovery.** The frontmatter `description` determines when Claude activates the skill. Invest time here:
- Bad: `"Helps with code reviews"`
- Good: `"Review code changes for bugs, security issues, and style violations. Use when the user asks for a code review, says 'review this PR', 'check my changes', or 'what do you think of this code'. Covers logic errors, security vulnerabilities, performance issues, and adherence to project conventions."`

**Reference external files, don't inline everything.** If a skill needs a long template, checklist, or code example, put it in `.claude/skills/<name>/references/` and reference it:
```markdown
Read `.claude/skills/<name>/references/checklist.md` for the full validation checklist.
```

**Scripts should be self-contained.** Helper scripts in `.claude/skills/<name>/scripts/` should:
- Have a shebang line (`#!/usr/bin/env python3` or `#!/usr/bin/env bash`)
- Include a docstring/comment explaining usage
- Accept arguments via CLI (use argparse for Python)
- Print clear output
- Exit with appropriate codes

### Phase 4: Register in CLAUDE.md

Add the new skill to the "Installed Skills" table in CLAUDE.md:

```markdown
| `/command-name` | One-line purpose description |
```

Read CLAUDE.md first, find the table, and add the new row in alphabetical order.

For plugins, also update the "Recommended Plugins" section if appropriate.

### Phase 5: Validate

Run the validation script to check the skill is properly structured:

```bash
python3 .claude/skills/create-skill/scripts/validate_skill.py "<name>"
```

The validator checks:
- [ ] Command file exists at `.claude/commands/<name>.md`
- [ ] Frontmatter has `name` and `description` fields
- [ ] Description is non-empty and under 500 characters
- [ ] Name matches filename (e.g., `name: foo` in `foo.md`)
- [ ] If skill type: supporting directories exist and are non-empty
- [ ] References use relative paths that resolve to existing files
- [ ] CLAUDE.md has a row for this skill
- [ ] No TODO/placeholder text remains in command file

Fix any issues found before considering the skill complete.

### Phase 6: Summary

Report to the user:
- Files created (with paths)
- Skill name and type
- How to invoke it (`/skill-name`)
- Any manual steps remaining

## NEVER Do

- **NEVER create a command without frontmatter** — the `name` and `description` fields are required for discovery
- **NEVER use underscores or spaces in skill names** — always `kebab-case`
- **NEVER put large templates directly in the command file** — use `.claude/skills/<name>/references/` for anything over ~30 lines
- **NEVER forget to register in CLAUDE.md** — an unregistered skill is invisible to users scanning the docs
- **NEVER write vague descriptions** — "Helps with stuff" tells Claude nothing; be specific about triggers and capabilities
- **NEVER create empty directories** — if a skill has `scripts/` or `references/`, they must contain at least one file
- **NEVER duplicate existing skill capabilities** — check the installed skills table first

## Quick Reference: Anatomy of Each Type

| Type | Files | CLAUDE.md | docs/plugins.md |
|------|-------|-----------|-----------------|
| `command` | `.claude/commands/<name>.md` | Yes (skills table) | No |
| `skill` | Command + `skills/<name>/references/` + `skills/<name>/scripts/` | Yes (skills table) | No |
| `plugin` | Optional command wrapper | Optional | Yes |
