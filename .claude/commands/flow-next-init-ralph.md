# Flow: Initialize Ralph — Autonomous Executor

## Prerequisites
- `docs/interview-answers.md` must exist
- `plan.md` must exist
- `scripts/ralph/steps.json` must exist

## Instructions

### 1. Verify Prerequisites

Read and verify all three files exist and are well-formed. If any are missing, tell the user which step to run first.

### 2. Present Plan Summary

Give the user a concise summary:
- Total steps and phases
- Estimated scope (small/medium/large)
- Key technical decisions
- Any assumptions you're making

### 3. Get Confirmation

Ask:
> "Ready to start autonomous execution? Ralph will work through all [N] steps, committing after each one. You can watch progress or come back when it's done.
>
> Say **go** to start."

### 4. Execute

Once confirmed, begin executing the plan. **Do NOT run ralph.sh as a subprocess** — instead, execute the Ralph loop directly:

For each step in `scripts/ralph/steps.json` where `done` is `false`:

1. Read the step details
2. Execute the task — create files, write code, install dependencies, whatever the step requires
3. Validate the work (does it make sense, does it build, etc.)
4. Mark the step as done in `steps.json` using Python:
   ```bash
   python3 scripts/ralph/mark_done.py <step_id>
   ```
5. Update `plan.md` — change `- [ ]` to `- [x]` for the completed step
6. Commit:
   ```bash
   git add -A
   git commit -m "ralph: step <id> — <task summary>"
   ```
7. Print a brief status: `✅ Step X/N complete: <task>`

### Error Handling

- If a step fails, log the error to `scripts/ralph/logs/step-<id>.log`
- Try to fix it once
- If still failing, skip it, mark it as `"done": false, "error": "<reason>"` and continue
- Report skipped steps at the end

### Completion

When all steps are done:
1. Print a summary of what was built
2. List any skipped/failed steps
3. Copy key output files to `/mnt/user-data/outputs/`
4. Suggest next steps to the user

### Critical Rules

- **DO NOT ask the user questions during execution** — make reasonable decisions
- **DO NOT use placeholder code** — every file must be functional
- **DO commit after every step** — this is the progress tracking mechanism
- **DO read interview-answers.md** when you need to make a judgment call
- **DO keep going** even if individual steps have issues
