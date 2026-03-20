# Skill Anatomy Reference

How skills, commands, and plugins are structured in this template.

## The Three Types

### 1. Command (Standalone)

A single markdown file that gives Claude instructions for a specific task.

```
.claude/commands/<name>.md
```

**When to use:** The skill is self-contained — all instructions fit in one file without large templates, checklists, or helper scripts.

**Examples:** `commit-work`, `napkin`, `game-changing-features`

### 2. Skill (Full)

A command file with supporting references and/or scripts.

```
.claude/commands/<name>.md              ← Main instructions
.claude/skills/<name>/references/       ← Templates, checklists, guides
.claude/skills/<name>/scripts/          ← Helper scripts (Python, Bash)
```

**When to use:** The skill needs auxiliary material — templates too large to inline, validation scripts, scaffold generators, or reference documentation.

**Examples:** `session-handoff`, `qa-test-planner`, `c4-architecture`, `database-schema-designer`

### 3. Plugin (External Tool)

An external tool integrated via documentation and optional setup scripts. No command file required (but a thin wrapper command is acceptable).

```
docs/plugins.md                         ← Documentation section
scripts/setup-plugins.sh                ← Installation step (optional)
.claude/commands/<name>.md              ← Usage wrapper (optional)
```

**When to use:** The capability comes from an external tool that needs installation, configuration, and documentation.

**Examples:** `dcg` (Destructive Command Guard), `claude-mem`

---

## File Conventions

### Command File (`.claude/commands/<name>.md`)

Every command file must have:

#### 1. YAML Frontmatter (Required)

```yaml
---
name: <kebab-case-name>
description: "<verb-phrase description with trigger phrases, under 500 chars>"
---
```

The `description` is the single most important field — it determines when Claude activates the skill. Guidelines:

| Aspect | Good | Bad |
|--------|------|-----|
| Specificity | "Review code changes for bugs, security issues, and style violations" | "Helps with code" |
| Trigger phrases | "Use when user says 'review this', 'check my code', 'code review'" | (none) |
| Length | 100-300 characters | Under 20 or over 500 |
| Starts with | Verb phrase: "Generate...", "Create...", "Analyze..." | Noun: "A tool for..." |

#### 2. Title and Purpose (Required)

```markdown
# Skill Name

One paragraph explaining what this skill does, when to use it, and what it produces.
```

#### 3. Workflow (Required)

Numbered steps that Claude follows. Use `###` for each step:

```markdown
## Workflow

### Step 1: Gather Inputs
...

### Step 2: Do the Work
...

### Step 3: Validate
...
```

#### 4. References to Supporting Files (If applicable)

Use relative paths from the project root:

```markdown
Read `.claude/skills/<name>/references/checklist.md` for the validation checklist.
```

```markdown
Run the scaffold script:
\```bash
python3 .claude/skills/<name>/scripts/scaffold.py "$ARGUMENTS"
\```
```

#### 5. NEVER Do Section (Recommended)

Guardrails for complex skills:

```markdown
## NEVER Do

- **NEVER do X** — reason why
- **NEVER do Y** — reason why
```

### Reference Files (`.claude/skills/<name>/references/`)

- Markdown files containing templates, checklists, or detailed guides
- Named descriptively: `checklist.md`, `template.md`, `common-mistakes.md`
- Should be useful standalone — Claude reads them as needed

### Script Files (`.claude/skills/<name>/scripts/`)

- Python 3 or Bash scripts
- Must have shebang: `#!/usr/bin/env python3` or `#!/usr/bin/env bash`
- Must accept CLI arguments (use `argparse` for Python)
- Must print clear output
- Must exit with appropriate codes (0 = success, non-zero = error)
- Must include a docstring or comment block explaining usage

---

## Naming Rules

| Rule | Example | Counter-example |
|------|---------|-----------------|
| Lowercase | `code-review` | `Code-Review` |
| Hyphen-separated | `api-designer` | `api_designer` |
| No spaces | `session-handoff` | `session handoff` |
| Descriptive | `database-schema-designer` | `db-tool` |
| Verb or noun phrase | `commit-work`, `dependency-updater` | `stuff` |

The name in the frontmatter must match the filename:
- File: `.claude/commands/code-review.md`
- Frontmatter: `name: code-review`

---

## CLAUDE.md Registration

Every skill or command must be listed in the "Installed Skills" table in CLAUDE.md:

```markdown
| `/command-name` | One-line purpose description |
```

Insert in alphabetical order within the table.

Plugins are listed in the "Recommended Plugins" section with install instructions.

---

## Quality Checklist

Before considering a skill complete, verify:

- [ ] Frontmatter has `name` and `description`
- [ ] `name` matches the filename
- [ ] `description` starts with a verb phrase and includes trigger phrases
- [ ] `description` is under 500 characters
- [ ] Workflow has clear, numbered steps
- [ ] No TODO/placeholder text remains
- [ ] Supporting files referenced by relative path exist
- [ ] Scripts have shebangs, docstrings, and accept CLI args
- [ ] Registered in CLAUDE.md skills table
- [ ] No name collision with existing skills
- [ ] Directories are non-empty (no empty `references/` or `scripts/`)
