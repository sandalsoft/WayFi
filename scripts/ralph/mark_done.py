#!/usr/bin/env python3
"""Mark a step as done in scripts/ralph/steps.json"""
import json
import sys
import os

STEPS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "steps.json")

def mark_done(step_id: int, error: str = None):
    with open(STEPS_FILE, "r") as f:
        steps = json.load(f)

    for step in steps:
        if step["id"] == step_id:
            step["done"] = True
            if error:
                step["error"] = error
            break
    else:
        print(f"Warning: step {step_id} not found")
        return

    with open(STEPS_FILE, "w") as f:
        json.dump(steps, f, indent=2)

    print(f"Marked step {step_id} as done")

def get_next():
    """Print the next incomplete step"""
    with open(STEPS_FILE, "r") as f:
        steps = json.load(f)

    for step in steps:
        if not step.get("done", False):
            print(json.dumps(step, indent=2))
            return

    print("ALL_DONE")

def status():
    """Print progress summary"""
    with open(STEPS_FILE, "r") as f:
        steps = json.load(f)

    total = len(steps)
    done = sum(1 for s in steps if s.get("done", False))
    errors = sum(1 for s in steps if s.get("error"))

    print(f"Progress: {done}/{total} steps complete")
    if errors:
        print(f"Errors: {errors} steps had issues")

    for step in steps:
        check = "✅" if step.get("done") else "⬜"
        err = f" ❌ {step['error']}" if step.get("error") else ""
        print(f"  {check} Step {step['id']}: {step['task']}{err}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: mark_done.py <step_id> | next | status")
        sys.exit(1)

    command = sys.argv[1]

    if command == "next":
        get_next()
    elif command == "status":
        status()
    else:
        step_id = int(command)
        error = sys.argv[2] if len(sys.argv) > 2 else None
        mark_done(step_id, error)
