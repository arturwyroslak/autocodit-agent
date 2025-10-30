#!/bin/bash

# =============================================================================
# GitHub MCP Server Launcher
# Model Context Protocol server for GitHub repository operations
# =============================================================================

set -euo pipefail

MCP_PORT=${MCP_PORT:-2301}
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start the GitHub MCP server
exec node "$SERVER_DIR/server.js" --port="$MCP_PORT"