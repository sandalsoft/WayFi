# Napkin

## Corrections
| Date | Source | What Went Wrong | What To Do Instead |
|------|--------|----------------|-------------------|

## User Preferences
- (accumulate here as you learn them)

## Patterns That Work
- Skills in this repo follow a 3-layer structure: command file (.claude/commands/), references (.claude/skills/<name>/references/), scripts (.claude/skills/<name>/scripts/)
- YAML frontmatter in command files uses `name` and `description` fields — description is the discovery mechanism
- Existing skills reference supporting files with backtick-wrapped relative paths from project root
- Python scripts use argparse, shebangs, and docstrings consistently
- CLAUDE.md skills table is the canonical registry for installed skills

## Patterns That Don't Work
- (approaches that failed and why)

## Domain Notes
- This is a template repo for bootstrapping projects inside Claude's sandbox on claude.ai
- The repo uses a flow system: interview -> plan -> ralph (autonomous executor)
- Plugins (dcg, claude-mem) are external tools documented in docs/plugins.md
- Skills vs commands vs plugins are three distinct types with different file structures
