# CLAUDE.md — Project Bootstrap Template

## What This Is

This is a template repository designed to be cloned by Claude inside claude.ai's code execution environment. It provides a structured workflow for going from an idea to a working project autonomously.

## Environment

This repo runs inside Claude's Linux sandbox on claude.ai. Key constraints:
- **No `gh` CLI, no `jq`** — use `python3` for JSON manipulation and API calls
- **No persistent state between conversations** — the filesystem resets each session
- **Git is available** but there's no push access unless the user provides credentials
- **Python 3.12+, Node 20+, bash** are available
- **pip install with `--break-system-packages`** flag required
- **Working directory**: clone into `/home/claude/project/`
- **Outputs for user**: copy deliverables to `/mnt/user-data/outputs/`

## Flow Commands

This project uses a sequential flow system. Each flow command is a markdown file in `.claude/commands/` that Claude reads and executes.

### Standard Flow

1. **`/flow-next-interview <idea>`** — Structured discovery interview. Asks the user questions to understand the project. Writes answers to `docs/interview-answers.md`.
2. **`/flow-next-plan`** — Generates an implementation plan from the interview. Writes `plan.md` and `scripts/ralph/steps.json`.
3. **`/flow-next-init-ralph`** — Reviews the plan with the user, gets confirmation, then begins autonomous execution.
4. **Ralph** (`scripts/ralph/ralph.sh`) — Iterates through steps.json, executing each task, committing progress.

### How to Trigger (User Prompt)

The user will say something like:
> "Clone my template and build me a [idea]"

Claude should:
1. Clone this repo (or the user's fork) into `/home/claude/project/`
2. Read this CLAUDE.md
3. Read and execute `.claude/commands/flow-next-interview.md`, passing the idea as context
4. Continue through the flow as each step completes

## Recommended Plugins

Two optional plugins improve safety and session continuity:

- **Destructive Command Guard (dcg)** — Blocks dangerous commands (`rm -rf`, `git reset --hard`, `git push --force`, etc.) before execution. Install with `bash scripts/setup-plugins.sh` or see `docs/plugins.md`.
- **Claude-Mem** — Persistent memory across Claude Code sessions. Captures observations automatically and injects relevant context into future sessions. Install from within Claude Code: `/plugin install claude-mem`.

See `docs/plugins.md` for full details, configuration, and security pack options.

## Secret Scanning (Gitleaks)

Secrets are blocked at two layers:

- **Pre-commit hook** — `.githooks/pre-commit` runs `gitleaks git --pre-commit --staged` before every commit. The hook is tracked in git; activate with `bash scripts/setup-gitleaks-hook.sh` or `bash scripts/setup-plugins.sh`.
- **GitHub Actions CI** — `.github/workflows/gitleaks.yaml` calls the shared `sandalsoft/.github` gitleaks workflow on every push and PR across all branches.

Customize false-positive allowlists in `.gitleaks.toml`.

## Installed Skills

This template includes pre-installed skill commands available via slash commands:

| Command | Purpose |
|---------|---------|
| `/crafting-effective-readmes` | Write or improve README files matched to project type and audience |
| `/commit-work` | Review, stage, and create well-structured git commits |
| `/create-skill` | Scaffold and register new skills, commands, or plugins in this template |
| `/game-changing-features` | Find 10x product opportunities and high-leverage improvements |
| `/mermaid-diagrams` | Create software diagrams (class, sequence, flowchart, ERD, C4, state) |
| `/napkin` | Per-repo learning file — tracks mistakes, corrections, and patterns |
| `/tailwind-v4-shadcn` | Set up Tailwind v4 + shadcn/ui with correct architecture |
| `/session-handoff` | Create handoff documents for seamless session transfers |
| `/qa-test-planner` | Generate test plans, test cases, regression suites, and bug reports |
| `/c4-architecture` | Generate C4 model architecture diagrams in Mermaid |
| `/database-schema-designer` | Design SQL/NoSQL schemas with normalization and migration patterns |
| `/dependency-updater` | Smart dependency management for any language |
| `/clean-web-design` | Professional design system with HSL tokens, Tailwind, and components |
| `/skill-selector` | Analyze plans, discover ecosystem skills, install them, and rewrite plans to leverage what's available |

Skills are stored in `.claude/commands/` (command files) and `.claude/skills/` (supporting references and scripts).

## Coding Standards

- Write clean, working code — no placeholders or TODOs
- Prefer simple solutions over clever ones
- Use the language/framework decided during the interview
- Every file should be functional — no stub implementations
- Commit after each logical unit of work with descriptive messages

## Ralph Autonomous Mode

Ralph is the autonomous executor. Key rules:
- Read `plan.md` and `scripts/ralph/steps.json` before each step
- Execute one step at a time
- Mark steps complete in `steps.json` after finishing
- Commit after each step
- If a step fails, log the error and continue to the next step
- Do NOT ask the user questions during autonomous execution — make reasonable decisions based on `docs/interview-answers.md`

## Output

When the project is complete:
- All source code should be in the repo
- `plan.md` should show all steps checked off
- A final summary should be provided to the user
- Key deliverable files should be copied to `/mnt/user-data/outputs/` for download
