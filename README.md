# Claude Code Template

A template repository for bootstrapping projects using Claude's code execution environment on claude.ai.

## How to Use

### 1. Create a new repo from this template
- Click **"Use this template"** on GitHub
- Name your new repo
- Clone it or leave it on GitHub

### 2. Start a new conversation on claude.ai

Tell Claude:

> Clone https://github.com/YOUR_USERNAME/YOUR_NEW_REPO and build me a [your idea]

Or if you just want to use the template without a GitHub repo:

> Read the CLAUDE.md and flow commands from my template, then interview me about building [your idea]

### 3. The Flow

1. **Interview** — Claude asks you questions about the project
2. **Plan** — Claude generates a detailed implementation plan
3. **Execute** — Ralph (the autonomous executor) builds it step by step

## Structure

```
├── CLAUDE.md                          # Project instructions for Claude
├── .claude/
│   ├── commands/                      # Slash commands (flow + skills)
│   │   ├── flow-next-interview.md     # Discovery interview
│   │   ├── flow-next-plan.md          # Plan generation
│   │   ├── flow-next-init-ralph.md    # Autonomous execution
│   │   └── *.md                       # 12 installed skill commands
│   └── skills/                        # Supporting files for skills
│       ├── session-handoff/           # Scripts & templates
│       ├── qa-test-planner/           # Test case generators & references
│       ├── c4-architecture/           # C4 syntax & pattern references
│       ├── database-schema-designer/  # Schema checklists & templates
│       ├── dependency-updater/        # Update scripts
│       └── clean-web-design/          # Design tokens & component patterns
├── scripts/ralph/
│   ├── mark_done.py                   # Step tracking utility
│   ├── steps.json                     # Machine-readable plan (generated)
│   ├── logs/                          # Execution logs
│   └── state/                         # State tracking
├── docs/
│   ├── interview-answers.md           # Interview output (generated)
│   └── plugins.md                     # Plugin documentation
├── scripts/
│   ├── setup-plugins.sh               # Plugin installation script
│   └── ralph/
│       └── ...
└── plan.md                            # Implementation plan (generated)
```

## Flow Commands

| Command | What it does |
|---------|-------------|
| `/flow-next-interview <idea>` | Structured discovery interview |
| `/flow-next-plan` | Generate implementation plan |
| `/flow-next-init-ralph` | Begin autonomous execution |

## Plugins

Optional plugins for safety and continuity:

| Plugin | Purpose | Install |
|--------|---------|---------|
| [Destructive Command Guard](https://github.com/Dicklesworthstone/destructive_command_guard) | Blocks dangerous commands before execution | `bash scripts/setup-plugins.sh` |
| [Claude-Mem](https://github.com/thedotmack/claude-mem) | Persistent memory across sessions | `/plugin install claude-mem` |

Run `bash scripts/setup-plugins.sh` to install both, or see `docs/plugins.md` for details.

## Installed Skills

This template comes with 12 pre-installed Claude Code skills:

| Command | Purpose |
|---------|---------|
| `/crafting-effective-readmes` | Write or improve README files matched to project type |
| `/commit-work` | Review, stage, and create well-structured git commits |
| `/game-changing-features` | Find 10x product opportunities and high-leverage improvements |
| `/mermaid-diagrams` | Create software diagrams (class, sequence, flowchart, ERD, C4) |
| `/napkin` | Per-repo learning file — tracks mistakes and patterns |
| `/tailwind-v4-shadcn` | Set up Tailwind v4 + shadcn/ui with correct architecture |
| `/session-handoff` | Create handoff documents for seamless session transfers |
| `/qa-test-planner` | Generate test plans, test cases, regression suites, bug reports |
| `/c4-architecture` | Generate C4 model architecture diagrams in Mermaid |
| `/database-schema-designer` | Design SQL/NoSQL schemas with migrations and indexing |
| `/dependency-updater` | Smart dependency management for any language |
| `/clean-web-design` | Professional design system with HSL tokens and components |

## Customization

Edit `CLAUDE.md` to add your own coding standards, preferred tech stack, or project-specific instructions. Add custom flow commands in `.claude/commands/`.
