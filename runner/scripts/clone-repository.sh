#!/bin/bash

# =============================================================================
# Repository Clone Script
# Clones the target repository and sets up the workspace
# =============================================================================

set -euo pipefail

AGENT_HOME=${AGENT_HOME:-/home/agent/.autocodit}
WORKSPACE_DIR="/workspace"
REPO_DIR="$WORKSPACE_DIR/repository"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$message\",\"component\":\"repo-cloner\",\"session_id\":\"$SESSION_ID\",\"task_id\":\"$TASK_ID\"}" | tee -a "$AGENT_HOME/logs/clone.log"
}

# Validate environment
if [[ -z "${REPOSITORY_URL:-}" ]]; then
    log "ERROR" "REPOSITORY_URL environment variable is required"
    exit 1
fi

if [[ -z "${GITHUB_INSTALLATION_TOKEN:-}" ]]; then
    log "ERROR" "GITHUB_INSTALLATION_TOKEN environment variable is required"
    exit 1
fi

# Extract repository information
if [[ "$REPOSITORY_URL" =~ ^https://github.com/(.+)/(.+)$ ]]; then
    REPO_OWNER="${BASH_REMATCH[1]}"
    REPO_NAME="${BASH_REMATCH[2]}"
else
    log "ERROR" "Invalid repository URL format: $REPOSITORY_URL"
    exit 1
fi

# Set up authenticated clone URL
AUTH_URL="https://x-access-token:$GITHUB_INSTALLATION_TOKEN@github.com/$REPO_OWNER/$REPO_NAME.git"

log "INFO" "Starting repository clone"
log "INFO" "Repository: $REPO_OWNER/$REPO_NAME"
log "INFO" "Target directory: $REPO_DIR"

# Create workspace directory
mkdir -p "$WORKSPACE_DIR"
cd "$WORKSPACE_DIR"

# Clone repository
log "INFO" "Cloning repository..."
if git clone "$AUTH_URL" repository; then
    log "INFO" "Repository cloned successfully"
else
    log "ERROR" "Failed to clone repository"
    exit 1
fi

cd "$REPO_DIR"

# Get repository information
DEFAULT_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD | sed 's@^refs/remotes/origin/@@')
CURRENT_SHA=$(git rev-parse HEAD)
BRANCH_NAME=${BRANCH_NAME:-$DEFAULT_BRANCH}

log "INFO" "Repository information:"
log "INFO" "  Default branch: $DEFAULT_BRANCH"
log "INFO" "  Current SHA: $CURRENT_SHA"
log "INFO" "  Target branch: $BRANCH_NAME"

# Switch to target branch if different from default
if [[ "$BRANCH_NAME" != "$DEFAULT_BRANCH" ]]; then
    log "INFO" "Switching to branch: $BRANCH_NAME"
    
    if git show-ref --verify --quiet "refs/remotes/origin/$BRANCH_NAME"; then
        # Remote branch exists
        git checkout -b "$BRANCH_NAME" "origin/$BRANCH_NAME"
        log "INFO" "Switched to existing branch: $BRANCH_NAME"
    else
        # Create new branch
        git checkout -b "$BRANCH_NAME"
        log "INFO" "Created new branch: $BRANCH_NAME"
    fi
fi

# Set up git configuration
git config user.name "AutoCodit Agent"
git config user.email "autocodit-bot@users.noreply.github.com"

# Analyze repository structure
log "INFO" "Analyzing repository structure..."

# Count files by type
FILE_STATS=$(find . -type f -name "*.py" | wc -l; find . -type f -name "*.js" | wc -l; find . -type f -name "*.ts" | wc -l; find . -type f -name "*.java" | wc -l; find . -type f -name "*.go" | wc -l)
PY_FILES=$(echo "$FILE_STATS" | sed -n '1p')
JS_FILES=$(echo "$FILE_STATS" | sed -n '2p')
TS_FILES=$(echo "$FILE_STATS" | sed -n '3p')
JAVA_FILES=$(echo "$FILE_STATS" | sed -n '4p')
GO_FILES=$(echo "$FILE_STATS" | sed -n '5p')

log "INFO" "Repository analysis:"
log "INFO" "  Python files: $PY_FILES"
log "INFO" "  JavaScript files: $JS_FILES"
log "INFO" "  TypeScript files: $TS_FILES"
log "INFO" "  Java files: $JAVA_FILES"
log "INFO" "  Go files: $GO_FILES"

# Detect project type and setup
if [[ -f "package.json" ]]; then
    log "INFO" "Detected Node.js project, installing dependencies..."
    npm install --production
fi

if [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]] || [[ -f "setup.py" ]]; then
    log "INFO" "Detected Python project, setting up virtual environment..."
    python3 -m venv .venv
    source .venv/bin/activate
    
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    elif [[ -f "pyproject.toml" ]]; then
        pip install .
    fi
fi

if [[ -f "go.mod" ]]; then
    log "INFO" "Detected Go project, downloading dependencies..."
    go mod download
fi

if [[ -f "pom.xml" ]] || [[ -f "build.gradle" ]]; then
    log "INFO" "Detected Java project"
    # TODO: Setup Java build environment
fi

# Create workspace metadata
cat > "$WORKSPACE_DIR/metadata.json" << EOF
{
  "repository": {
    "owner": "$REPO_OWNER",
    "name": "$REPO_NAME",
    "url": "$REPOSITORY_URL",
    "default_branch": "$DEFAULT_BRANCH",
    "current_branch": "$BRANCH_NAME",
    "current_sha": "$CURRENT_SHA"
  },
  "task": {
    "id": "$TASK_ID",
    "session_id": "$SESSION_ID",
    "action_type": "$ACTION_TYPE",
    "description": "$TASK_DESCRIPTION"
  },
  "analysis": {
    "files": {
      "python": $PY_FILES,
      "javascript": $JS_FILES,
      "typescript": $TS_FILES,
      "java": $JAVA_FILES,
      "go": $GO_FILES
    },
    "project_type": "$(detect_project_type)",
    "has_tests": $(has_tests),
    "has_ci": $(has_ci)
  },
  "timestamp": "$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')"
}
EOF

log "INFO" "Repository clone and setup completed"

# Helper functions
detect_project_type() {
    if [[ -f "package.json" ]]; then
        echo "nodejs"
    elif [[ -f "requirements.txt" ]] || [[ -f "pyproject.toml" ]]; then
        echo "python"
    elif [[ -f "go.mod" ]]; then
        echo "golang"
    elif [[ -f "pom.xml" ]]; then
        echo "java-maven"
    elif [[ -f "build.gradle" ]]; then
        echo "java-gradle"
    else
        echo "unknown"
    fi
}

has_tests() {
    if [[ -d "tests" ]] || [[ -d "test" ]] || [[ -d "__tests__" ]] || [[ -d "src/test" ]]; then
        echo "true"
    else
        echo "false"
    fi
}

has_ci() {
    if [[ -d ".github/workflows" ]] || [[ -f ".gitlab-ci.yml" ]] || [[ -f "Jenkinsfile" ]]; then
        echo "true"
    else
        echo "false"
    fi
}