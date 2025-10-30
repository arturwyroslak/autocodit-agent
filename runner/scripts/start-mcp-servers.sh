#!/bin/bash

# =============================================================================
# Start MCP Servers
# Launches all configured MCP servers for the agent
# =============================================================================

set -euo pipefail

AGENT_HOME=${AGENT_HOME:-/home/agent/.autocodit}
MCP_PORT=${MCP_SERVER_PORT:-2301}
MCP_SERVERS_DIR="/opt/mcp-servers"

# Logging function
log() {
    local level=$1
    shift
    local message="$*"
    local timestamp=$(date -u '+%Y-%m-%dT%H:%M:%S.%3NZ')
    
    echo "{\"timestamp\":\"$timestamp\",\"level\":\"$level\",\"message\":\"$message\",\"component\":\"mcp-launcher\",\"session_id\":\"$SESSION_ID\",\"task_id\":\"$TASK_ID\"}" | tee -a "$AGENT_HOME/logs/mcp.log"
}

# Start GitHub MCP Server
start_github_mcp() {
    log "INFO" "Starting GitHub MCP Server on port $MCP_PORT"
    
    cd "$MCP_SERVERS_DIR/github"
    
    # Set GitHub MCP configuration
    export GITHUB_TOKEN="$GITHUB_INSTALLATION_TOKEN"
    export GITHUB_REPOSITORY="$REPOSITORY_URL"
    export GITHUB_BRANCH="$BRANCH_NAME"
    export MCP_PORT="$MCP_PORT"
    
    # Start the server
    ./start.sh &
    
    local pid=$!
    echo $pid > "$AGENT_HOME/github-mcp.pid"
    
    log "INFO" "GitHub MCP Server started with PID: $pid"
}

# Start Playwright MCP Server
start_playwright_mcp() {
    log "INFO" "Starting Playwright MCP Server"
    
    cd "$MCP_SERVERS_DIR/playwright"
    
    # Set Playwright configuration
    export PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    export PLAYWRIGHT_HEADLESS=true
    export MCP_PORT=$((MCP_PORT + 1))
    
    # Start the server
    ./start.sh &
    
    local pid=$!
    echo $pid > "$AGENT_HOME/playwright-mcp.pid"
    
    log "INFO" "Playwright MCP Server started with PID: $pid"
}

# Start Custom MCP Servers
start_custom_mcp() {
    log "INFO" "Starting custom MCP servers"
    
    # Parse AGENT_CONFIG for custom MCP servers
    if [[ -n "${AGENT_CONFIG:-}" ]]; then
        echo "$AGENT_CONFIG" | jq -r '.mcp_servers[]?' | while IFS= read -r server_config; do
            if [[ -n "$server_config" ]]; then
                local server_name=$(echo "$server_config" | jq -r '.name')
                local server_type=$(echo "$server_config" | jq -r '.type')
                
                if [[ "$server_type" == "docker" ]]; then
                    start_docker_mcp_server "$server_name" "$server_config"
                elif [[ "$server_type" == "local" ]]; then
                    start_local_mcp_server "$server_name" "$server_config"
                fi
            fi
        done
    fi
}

# Start Docker MCP Server
start_docker_mcp_server() {
    local name=$1
    local config=$2
    
    log "INFO" "Starting Docker MCP server: $name"
    
    local image=$(echo "$config" | jq -r '.image')
    local port=$(echo "$config" | jq -r '.port // 0')
    
    if [[ $port -eq 0 ]]; then
        port=$((MCP_PORT + 10 + $(( RANDOM % 90 ))))
    fi
    
    # Start Docker container
    docker run -d \
        --name "mcp-$name-$SESSION_ID" \
        --network "$(docker network ls --filter name=autocodit-runners -q | head -1)" \
        -p "$port:$port" \
        -e "MCP_PORT=$port" \
        -e "SESSION_ID=$SESSION_ID" \
        -e "TASK_ID=$TASK_ID" \
        "$image"
    
    log "INFO" "Docker MCP server $name started on port $port"
}

# Start Local MCP Server
start_local_mcp_server() {
    local name=$1
    local config=$2
    
    log "INFO" "Starting local MCP server: $name"
    
    local command=$(echo "$config" | jq -r '.command')
    local args=$(echo "$config" | jq -r '.args[]?' | tr '\n' ' ')
    
    # Execute command
    cd "$MCP_SERVERS_DIR/$name" 2>/dev/null || cd "$AGENT_HOME/temp"
    
    $command $args &
    
    local pid=$!
    echo $pid > "$AGENT_HOME/$name-mcp.pid"
    
    log "INFO" "Local MCP server $name started with PID: $pid"
}

# Health check for MCP servers
health_check() {
    local retries=30
    local delay=2
    
    for ((i=1; i<=retries; i++)); do
        if curl -s -f "http://localhost:$MCP_PORT/health" >/dev/null 2>&1; then
            log "INFO" "MCP servers health check passed"
            return 0
        fi
        
        log "DEBUG" "MCP servers not ready yet (attempt $i/$retries)"
        sleep $delay
    done
    
    log "ERROR" "MCP servers failed health check"
    return 1
}

# Main execution
main() {
    log "INFO" "Starting MCP servers initialization"
    
    # Start core MCP servers
    start_github_mcp
    start_playwright_mcp
    
    # Start custom MCP servers if configured
    start_custom_mcp
    
    # Wait for all servers to be ready
    if health_check; then
        log "INFO" "All MCP servers started successfully"
    else
        log "ERROR" "Failed to start MCP servers"
        exit 1
    fi
    
    # Keep running (this script runs in background)
    wait
}

# Cleanup function
cleanup() {
    log "INFO" "Shutting down MCP servers"
    
    # Stop all MCP server processes
    for pid_file in "$AGENT_HOME"/*-mcp.pid; do
        if [[ -f "$pid_file" ]]; then
            local pid=$(cat "$pid_file")
            if kill -0 $pid 2>/dev/null; then
                log "INFO" "Stopping MCP server (PID: $pid)"
                kill -TERM $pid
                sleep 2
                kill -KILL $pid 2>/dev/null || true
            fi
            rm -f "$pid_file"
        fi
    done
    
    # Stop Docker MCP containers
    docker ps --filter "name=mcp-*-$SESSION_ID" -q | xargs -r docker stop
    docker ps -a --filter "name=mcp-*-$SESSION_ID" -q | xargs -r docker rm
    
    log "INFO" "MCP servers shutdown completed"
}

trap cleanup EXIT

# Run main function
main "$@"