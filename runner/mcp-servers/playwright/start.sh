#!/bin/bash

# =============================================================================
# Playwright MCP Server Launcher
# Model Context Protocol server for browser automation and UI testing
# =============================================================================

set -euo pipefail

MCP_PORT=${MCP_PORT:-2302}
SERVER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Start the Playwright MCP server
exec python3 "$SERVER_DIR/server.py" --port="$MCP_PORT"