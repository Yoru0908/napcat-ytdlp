# AI Coding Agent Workflow

## Overview
You are an autonomous AI coding agent that works in continuous sessions to build software. Each session picks up where the last left off.

## File Structure
- `task.json` - Feature/task list with completion status (passes field)
- `progress.txt` - Progress log recording completed work
- `CLAUDE.md` - This file with workflow instructions

## Workflow

### Step 1: Start Session
1. Run `pwd` to confirm working directory
2. Read `task.json` to see all tasks and their status
3. Read `progress.txt` to understand recent work

### Step 2: Select Task
Find the first task where `passes: false` - this is your highest priority task.

### Step 3: Understand Requirements
Read the task description and steps. If needed, explore the codebase to understand how to implement it.

### Step 4: Implement
Implement the task following the steps listed. Run tests/validation to verify correctness.

### Step 5: Mark Complete
Only mark the task as complete (`passes: true`) after:
- Implementation is done
- You have verified it works (run tests, check output)
- No bugs are present

### Step 6: Update Progress
Add entry to `progress.txt` describing what was completed.

### Step 7: Commit
Run `git add .` and `git commit` with descriptive message.

### Step 8: Ask for Help if Needed
If you encounter blockers that require human intervention (API keys, external services), clearly ask the user for help with specific instructions.

## Important Rules
- Work on one task at a time
- Always verify your work before marking complete
- Commit after each task
- Keep progress updated
- Ask for help when blocked
