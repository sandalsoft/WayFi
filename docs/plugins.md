# Recommended Plugins

This template supports two optional Claude Code plugins that improve safety and continuity across sessions.

## Destructive Command Guard (dcg)

**Repository:** [Dicklesworthstone/destructive_command_guard](https://github.com/Dicklesworthstone/destructive_command_guard)

A high-performance Rust-based safety hook that intercepts and blocks destructive commands before Claude Code can execute them. Protects against accidental `rm -rf`, `git reset --hard`, `git push --force`, database drops, and more.

### What It Blocks

- **Git:** `git reset --hard`, `git push --force`, `git branch -D`, `git clean -f`, `git checkout -- .`
- **Filesystem:** `rm -rf` outside temp directories, destructive operations on system paths
- **Databases:** `DROP TABLE`, `TRUNCATE`, `DELETE` without `WHERE`
- **Cloud/Infra:** AWS/GCP/Azure resource deletion, Kubernetes namespace deletion
- **Embedded scripts:** Destructive code hidden in `python -c`, `node -e`, heredocs

### Key Features

- Sub-millisecond latency (SIMD-accelerated)
- 49+ modular security packs (database, Kubernetes, Docker, cloud providers, CI/CD)
- Fail-open design — never breaks legitimate workflows
- Heredoc and inline script scanning
- `dcg explain "command"` to understand why something was blocked

### Install

```bash
curl -fsSL "https://raw.githubusercontent.com/Dicklesworthstone/destructive_command_guard/master/install.sh?$(date +%s)" | bash -s -- --easy-mode
```

Or use the project setup script:

```bash
bash scripts/setup-plugins.sh
```

### Configuration

After installation, dcg config lives at `~/.config/dcg/config.toml`:

```toml
[packs]
enabled = [
    "core.filesystem",
    "core.git",
    "database.postgresql",
    "containers.docker",
]

[agents.claude-code]
trust_level = "high"
```

### Useful Commands

```bash
dcg status                    # Check installation status
dcg packs --verbose           # List all available security packs
dcg explain "rm -rf /"        # See why a command would be blocked
```

---

## Claude-Mem

**Repository:** [thedotmack/claude-mem](https://github.com/thedotmack/claude-mem)

Persistent memory for Claude Code across sessions. Automatically captures observations during your session, compresses them with AI, and injects relevant context into future sessions.

### How It Works

Claude-Mem operates through 5 lifecycle hooks:

| Hook | Purpose |
|------|---------|
| `SessionStart` | Retrieves relevant memories from prior sessions |
| `UserPromptSubmit` | Captures user input context |
| `PostToolUse` | Records tool execution results and observations |
| `Stop` | Handles session pause events |
| `SessionEnd` | Compresses and stores session memories |

### Key Features

- Automatic observation capture — no manual intervention needed
- AI-powered compression for efficient storage
- Progressive disclosure with layered context retrieval
- Web viewer UI at `http://localhost:37777`
- 5 MCP search tools: `search`, `timeline`, `get_observations`, `save_memory`, and docs

### Install

In a Claude Code session:

```
/plugin marketplace add thedotmack/claude-mem
/plugin install claude-mem
```

Or use the project setup script:

```bash
bash scripts/setup-plugins.sh
```

### Configuration

Settings are stored at `~/.claude-mem/settings.json`, auto-generated with defaults on first launch.

---

## Gitleaks (Secret Scanning)

**Repository:** [gitleaks/gitleaks](https://github.com/gitleaks/gitleaks)

Prevents secrets (API keys, tokens, private keys, passwords) from being committed to the repository. Protection operates at two layers:

### Pre-commit Hook (Local)

Runs `gitleaks git --pre-commit --staged` before every commit. If secrets are found, the commit is blocked.

```bash
bash scripts/setup-gitleaks-hook.sh
```

The hook script lives in `.githooks/pre-commit` (tracked in git, included in every clone). The setup script will:
1. Install the `gitleaks` CLI (via Homebrew or the official install script)
2. Set `git config core.hooksPath .githooks` to activate the tracked hooks directory

### GitHub Actions CI (Remote)

`.github/workflows/gitleaks.yaml` calls the shared workflow at `sandalsoft/.github/workflows/gitleaks.yaml@master` on every push and pull request across **all branches**. This is the safety net — if a secret bypasses the local hook, CI catches it.

### Configuration

Customize scanning rules in `.gitleaks.toml` at the repo root. The config uses `[extend] useDefault = true` to inherit all default detection rules (AWS, GitHub tokens, private keys, etc.) while allowing project-specific overrides:

```toml
[extend]
  useDefault = true

[allowlist]
  # Ignore a specific test fixture
  paths = ["testdata/fake-creds.json"]

  # Ignore a known false positive regex
  [[allowlist.regexes]]
  description = "example API key in docs"
  regex = "EXAMPLE_KEY_\\w+"
```

**Important:** Without `[extend] useDefault = true`, a custom config replaces all default rules, disabling detection entirely.

### Useful Commands

```bash
gitleaks detect --staged          # Scan staged changes (what the hook runs)
gitleaks detect                   # Scan entire repo working tree
gitleaks detect --log-opts="HEAD" # Scan full git history
```

---

## Setup Script

Install all plugins at once:

```bash
bash scripts/setup-plugins.sh
```

The script will:
1. Install dcg with automatic platform detection
2. Install claude-mem plugin
3. Install gitleaks and configure the pre-commit hook
4. Verify installations
5. Display status summary
