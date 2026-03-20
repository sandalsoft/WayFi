---
name: dependency-updater
description: Smart dependency management for any language. Auto-detects project type, applies safe updates automatically, prompts for major versions, diagnoses and fixes dependency issues.
license: MIT
metadata:
  version: 1.0.0
---

# Dependency Updater

Smart dependency management for any language with automatic detection and safe updates.

---

## Quick Start

```
update my dependencies
```

The skill auto-detects your project type and handles the rest.

---

## Triggers

| Trigger | Example |
|---------|---------|
| Update dependencies | "update dependencies", "update deps" |
| Check outdated | "check for outdated packages" |
| Fix dependency issues | "fix my dependency problems" |
| Security audit | "audit dependencies for vulnerabilities" |
| Diagnose deps | "diagnose dependency issues" |

---

## Supported Languages

| Language | Package File | Update Tool | Audit Tool |
|----------|--------------|-------------|------------|
| **Node.js** | package.json | `taze` | `npm audit` |
| **Python** | requirements.txt, pyproject.toml | `pip-review` | `safety`, `pip-audit` |
| **Go** | go.mod | `go get -u` | `govulncheck` |
| **Rust** | Cargo.toml | `cargo update` | `cargo audit` |
| **Ruby** | Gemfile | `bundle update` | `bundle audit` |
| **Java** | pom.xml, build.gradle | `mvn versions:*` | `mvn dependency:*` |
| **.NET** | *.csproj | `dotnet outdated` | `dotnet list package --vulnerable` |

---

## Quick Reference

| Update Type | Version Change | Action |
|-------------|----------------|--------|
| **Fixed** | No `^` or `~` | Skip (intentionally pinned) |
| **PATCH** | `x.y.z` → `x.y.Z` | Auto-apply |
| **MINOR** | `x.y.z` → `x.Y.0` | Auto-apply |
| **MAJOR** | `x.y.z` → `X.0.0` | Prompt user individually |

---

## Workflow

```
User Request
    │
    ▼
┌─────────────────────────────────────────────────────┐
│ Step 1: DETECT PROJECT TYPE                         │
│ • Scan for package files (package.json, go.mod...) │
│ • Identify package manager                          │
├─────────────────────────────────────────────────────┤
│ Step 2: CHECK PREREQUISITES                         │
│ • Verify required tools are installed               │
│ • Suggest installation if missing                   │
├─────────────────────────────────────────────────────┤
│ Step 3: SCAN FOR UPDATES                            │
│ • Run language-specific outdated check              │
│ • Categorize: MAJOR / MINOR / PATCH / Fixed         │
├─────────────────────────────────────────────────────┤
│ Step 4: AUTO-APPLY SAFE UPDATES                     │
│ • Apply MINOR and PATCH automatically               │
│ • Report what was updated                           │
├─────────────────────────────────────────────────────┤
│ Step 5: PROMPT FOR MAJOR UPDATES                    │
│ • AskUserQuestion for each MAJOR update             │
│ • Show current → new version                        │
├─────────────────────────────────────────────────────┤
│ Step 6: APPLY APPROVED MAJORS                       │
│ • Update only approved packages                     │
├─────────────────────────────────────────────────────┤
│ Step 7: FINALIZE                                    │
│ • Run install command                               │
│ • Run security audit                                │
└─────────────────────────────────────────────────────┘
```

---

## Anti-Patterns

| Avoid | Why | Instead |
|-------|-----|---------|
| Update fixed versions | Intentionally pinned | Skip them |
| Auto-apply MAJOR | Breaking changes | Prompt user |
| Batch MAJOR prompts | Loses context | Prompt individually |
| Skip lock file | Irreproducible builds | Always commit lock files |
| Ignore security alerts | Vulnerabilities | Address by severity |

---

## Verification Checklist

After updates:

- [ ] Updates scanned without errors
- [ ] MINOR/PATCH auto-applied
- [ ] MAJOR updates prompted individually
- [ ] Fixed versions untouched
- [ ] Lock file updated
- [ ] Install command ran
- [ ] Security audit passed (or issues noted)

---

## Script Reference

| Script | Purpose |
|--------|---------|
| `.claude/skills/dependency-updater/scripts/check-tool.sh` | Verify tool is installed |
| `.claude/skills/dependency-updater/scripts/run-taze.sh` | Run taze with proper flags |
