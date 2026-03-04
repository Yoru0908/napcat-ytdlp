#!/bin/bash

# AI Coding Agent - Continuous Loop Runner
# Usage:
#   ./run-loop.sh          # Run indefinitely (while loop)
#   ./run-loop.sh 10       # Run 10 iterations
#   ./run-loop.sh --once   # Run single iteration

set -e

# Configuration
PROJECT_DIR="/home/srzwyuu/video-bot"
TASK_FILE="$PROJECT_DIR/task.json"
PROGRESS_FILE="$PROJECT_DIR/progress.txt"
LOG_FILE="$PROJECT_DIR/run.log"

# Default values
INFINITE_MODE=false
NUM_ITERATIONS=1
PERMISSION_MODE="bypassPermissions"

# Parse arguments
if [ "$1" = "--once" ]; then
    NUM_ITERATIONS=1
elif [ "$1" = "--infinite" ] || [ "$1" = "-i" ]; then
    INFINITE_MODE=true
elif [ -n "$1" ]; then
    NUM_ITERATIONS=$1
else
    # Default: infinite loop like the video describes
    INFINITE_MODE=true
fi

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✓${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✓ $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ✗${NC} $1" >&2
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✗ $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠ $1" >> "$LOG_FILE"
}

log_info() {
    echo -e "${CYAN}[$(date '+%Y-%m-%d %H:%M:%S')] ℹ${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ℹ $1" >> "$LOG_FILE"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."

    # Check if Claude Code is installed
    if ! command -v claude &> /dev/null; then
        log_error "Claude Code is not installed. Install with: npm install -g @anthropic-ai/claude-code"
        exit 1
    fi

    # Check if project directory exists
    if [ ! -d "$PROJECT_DIR" ]; then
        log_error "Project directory not found: $PROJECT_DIR"
        exit 1
    fi

    # Check if task.json exists
    if [ ! -f "$TASK_FILE" ]; then
        log_error "Task file not found: $TASK_FILE"
        exit 1
    fi

    log_success "Prerequisites check passed"
}

# Get next pending task
get_next_task() {
    # Find first task where passes is false
    python3 -c "
import json
with open('$TASK_FILE', 'r') as f:
    tasks = json.load(f)
    for task in tasks:
        if not task.get('passes', False):
            print(json.dumps(task))
            exit(0)
    print('{}')
"
}

# Mark task as completed
mark_task_completed() {
    local task_id=$1
    python3 -c "
import json
with open('$TASK_FILE', 'r') as f:
    tasks = json.load(f)
for task in tasks:
    if task['id'] == $task_id:
        task['passes'] = True
with open('$TASK_FILE', 'w') as f:
    json.dump(tasks, f, indent=2)
"
    log_success "Task $task_id marked as completed"
}

# Update progress file
update_progress() {
    local task_id=$1
    local status=$2
    local description=$3

    echo "[$(date '+%Y-%m-%d %H:%M:%S')] - Round $ROUND - Task $task_id - $status - $description" >> "$PROGRESS_FILE"
}

# Run Claude Code with the task
run_claude_task() {
    local task_id=$1
    local task_description=$2
    local task_steps=$3

    log "Starting Claude Code for task $task_id: $task_description"

    # Build the prompt based on video workflow
    PROMPT="Work on the following task from task.json:

Task ID: $task_id
Description: $task_description

Steps to complete:
$task_steps

Follow this workflow:
1. Run 'pwd' to confirm working directory
2. Read task.json to confirm the task
3. Read CLAUDE.md for workflow instructions
4. Implement the task following the steps
5. Test and verify your implementation (use browser, run tests, etc.)
6. Mark the task as completed by setting passes: true in task.json
7. Update progress.txt with what you completed
8. Run 'git add .' and 'git commit' to save your work

If you encounter issues that require human help (like missing API keys, external services), clearly ask the user for specific instructions on what to do.

Begin working on this task now."

    # Run Claude Code in non-interactive mode
    # --permission-mode bypassPermissions: avoid needing human to accept permissions
    # --print: non-interactive output
    claude \
        --permission-mode "$PERMISSION_MODE" \
        --print \
        --add-dir "$PROJECT_DIR" \
        "$PROMPT" 2>&1 | tee -a "$LOG_FILE"

    local exit_code=${PIPESTATUS[0]}

    if [ $exit_code -eq 0 ]; then
        log_success "Task $task_id completed successfully"
        update_progress "$task_id" "COMPLETED" "$task_description"
        mark_task_completed "$task_id"
    else
        log_error "Task $task_id failed with exit code $exit_code"
        update_progress "$task_id" "FAILED" "$task_description"
    fi

    return $exit_code
}

# Initialize git if needed
init_git() {
    if [ ! -d "$PROJECT_DIR/.git" ]; then
        log "Initializing git repository..."
        cd "$PROJECT_DIR"
        git init
        git add .
        git commit -m "Initial commit: project structure"
        log_success "Git repository initialized"
    fi
}

# Get total pending tasks count
get_pending_count() {
    python3 -c "
import json
with open('$TASK_FILE', 'r') as f:
    tasks = json.load(f)
    count = sum(1 for t in tasks if not t.get('passes', False))
    print(count)
"
}

# Main loop
main() {
    MODE_TEXT="Infinite (while true)"
    if [ "$INFINITE_MODE" = true ]; then
        MODE_TEXT="Infinite (while true)"
    elif [ "$NUM_ITERATIONS" -eq 1 ]; then
        MODE_TEXT="Single iteration"
    else
        MODE_TEXT="$NUM_ITERATIONS iterations"
    fi

    echo "=========================================="
    echo "AI Coding Agent - Continuous Runner"
    echo "=========================================="
    echo "Project: $PROJECT_DIR"
    echo "Mode: $MODE_TEXT"
    echo "Permission Mode: $PERMISSION_MODE"
    echo "=========================================="
    echo ""
    echo "Press Ctrl+C to stop"
    echo ""

    # Initialize
    check_prerequisites
    init_git

    ROUND=0

    # The while loop - same as video describes
    while true; do
        # Check iteration limit for non-infinite mode
        if [ "$INFINITE_MODE" = false ] && [ $ROUND -ge $NUM_ITERATIONS ]; then
            break
        fi

        ROUND=$((ROUND + 1))

        log "=========================================="
        log "Starting Round $ROUND"
        PENDING=$(get_pending_count)
        log "Pending tasks: $PENDING"
        log "=========================================="

        # Get next task
        TASK_JSON=$(get_next_task)

        if [ -z "$TASK_JSON" ] || [ "$TASK_JSON" = "{}" ]; then
            log_warning "No pending tasks found. All tasks completed!"
            log "Project development finished!"
            break
        fi

        # Parse task info
        TASK_ID=$(echo "$TASK_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['id'])")
        TASK_DESC=$(echo "$TASK_JSON" | python3 -c "import json,sys; print(json.load(sys.stdin)['description'])")
        TASK_STEPS=$(echo "$TASK_JSON" | python3 -c "import json,sys; t=json.load(sys.stdin); print('\\n'.join(f'{i+1}. {s}' for i,s in enumerate(t['steps'])))")

        log_info "Selected task: [$TASK_ID] $TASK_DESC"

        # Run the task
        if run_claude_task "$TASK_ID" "$TASK_DESC" "$TASK_STEPS"; then
            log_success "Round $ROUND completed"
        else
            log_error "Round $ROUND failed - continuing to next task"
        fi

        log "-------------------------------------------"

        # Small delay between iterations (like video shows)
        sleep 2
    done

    log "=========================================="
    log "Development loop finished!"
    log "Total rounds: $ROUND"
    log "=========================================="
}

# Run main
main
