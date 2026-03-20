#!/usr/bin/env python3
"""
Check staleness of a handoff document compared to current project state.

Usage:
    python check_staleness.py <handoff-file>
"""

import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run_cmd(cmd: list[str], cwd: str = None) -> tuple[bool, str]:
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, timeout=10)
        return result.returncode == 0, result.stdout.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False, ""


def parse_handoff_metadata(filepath: str) -> dict:
    content = Path(filepath).read_text()
    metadata = {"created": None, "branch": None, "project_path": None, "modified_files": []}

    match = re.search(r'Created:\s*(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', content)
    if match:
        try:
            metadata["created"] = datetime.strptime(match.group(1), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

    match = re.search(r'Branch:\s*(\S+)', content)
    if match:
        branch = match.group(1)
        if branch and not branch.startswith('['):
            metadata["branch"] = branch

    match = re.search(r'Project:\s*(.+?)(?:\n|$)', content)
    if match:
        metadata["project_path"] = match.group(1).strip()

    table_matches = re.findall(r'\|\s*([a-zA-Z0-9_\-./]+\.[a-zA-Z]+)\s*\|', content)
    for f in table_matches:
        if '/' in f and not f.startswith('['):
            metadata["modified_files"].append(f)

    return metadata


def get_commits_since(timestamp, project_path):
    if not timestamp:
        return []
    iso_time = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
    success, output = run_cmd(
        ["git", "log", f"--since={iso_time}", "--oneline", "--no-decorate"],
        cwd=project_path
    )
    if success and output:
        return output.split("\n")
    return []


def get_current_branch(project_path):
    success, branch = run_cmd(["git", "branch", "--show-current"], cwd=project_path)
    return branch if success else None


def check_staleness(handoff_path: str) -> dict:
    path = Path(handoff_path)
    if not path.exists():
        return {"error": f"Handoff file not found: {handoff_path}"}

    metadata = parse_handoff_metadata(handoff_path)
    project_path = metadata.get("project_path")
    if not project_path or not Path(project_path).exists():
        project_path = str(path.parent.parent.parent)

    success, _ = run_cmd(["git", "rev-parse", "--git-dir"], cwd=project_path)
    is_git_repo = success

    result = {
        "handoff_file": str(path),
        "project_path": project_path,
        "is_git_repo": is_git_repo,
        "created": metadata["created"],
        "handoff_branch": metadata["branch"],
    }

    if metadata["created"]:
        age = datetime.now() - metadata["created"]
        result["days_old"] = age.total_seconds() / 86400
    else:
        result["days_old"] = None

    if is_git_repo:
        result["current_branch"] = get_current_branch(project_path)
        result["branch_matches"] = (
            result["current_branch"] == metadata["branch"]
            if metadata["branch"] else True
        )
        commits = get_commits_since(metadata["created"], project_path)
        result["commits_since"] = len(commits)

        staleness_score = 0
        issues = []
        days = result.get("days_old", 0) or 0

        if days > 30:
            staleness_score += 3
            issues.append(f"Handoff is {int(days)} days old")
        elif days > 7:
            staleness_score += 2
            issues.append(f"Handoff is {int(days)} days old")
        elif days > 1:
            staleness_score += 1

        if result["commits_since"] > 50:
            staleness_score += 3
            issues.append(f"{result['commits_since']} commits since handoff")
        elif result["commits_since"] > 20:
            staleness_score += 2
            issues.append(f"{result['commits_since']} commits since handoff")
        elif result["commits_since"] > 5:
            staleness_score += 1

        if not result["branch_matches"]:
            staleness_score += 2
            issues.append("Current branch differs from handoff branch")

        if staleness_score == 0:
            level = "FRESH"
            rec = "Safe to resume - minimal changes since handoff"
        elif staleness_score <= 2:
            level = "SLIGHTLY_STALE"
            rec = "Generally safe to resume - review changes before continuing"
        elif staleness_score <= 4:
            level = "STALE"
            rec = "Proceed with caution - significant changes may affect context"
        else:
            level = "VERY_STALE"
            rec = "Consider creating new handoff - too many changes since original"

        result["staleness_level"] = level
        result["recommendation"] = rec
        result["issues"] = issues
    else:
        result["staleness_level"] = "UNKNOWN"
        result["recommendation"] = "Not a git repo - unable to detect changes"
        result["issues"] = ["Project is not a git repository"]

    return result


def print_report(result):
    if "error" in result:
        print(f"Error: {result['error']}")
        return

    print(f"\n{'='*60}")
    print(f"Handoff Staleness Report")
    print(f"{'='*60}")
    print(f"File: {result['handoff_file']}")

    if result["created"]:
        print(f"Created: {result['created'].strftime('%Y-%m-%d %H:%M:%S')}")
        if result["days_old"] is not None:
            if result["days_old"] < 1:
                print(f"Age: {result['days_old'] * 24:.1f} hours")
            else:
                print(f"Age: {result['days_old']:.1f} days")

    print(f"\nStaleness Level: {result['staleness_level']}")
    print(f"Recommendation: {result['recommendation']}")

    if result.get("issues"):
        print(f"\nIssues:")
        for issue in result["issues"]:
            print(f"  - {issue}")

    print(f"\n{'='*60}")

    level = result.get("staleness_level", "UNKNOWN")
    if level in ["FRESH", "SLIGHTLY_STALE"]:
        print("Verdict: [OK] Safe to resume")
    elif level == "STALE":
        print("Verdict: [CAUTION] Verify context before resuming")
    else:
        print("Verdict: [WARNING] Consider creating fresh handoff")


def main():
    if len(sys.argv) < 2:
        print("Usage: python check_staleness.py <handoff-file>")
        sys.exit(1)

    result = check_staleness(sys.argv[1])
    print_report(result)

    level = result.get("staleness_level", "UNKNOWN")
    if level in ["FRESH", "SLIGHTLY_STALE"]:
        sys.exit(0)
    elif level == "STALE":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()
