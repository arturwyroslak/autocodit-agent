# =============================================================================
# AutoCodit Agent Runner - Lightweight Container for Code Execution
# =============================================================================

# Base image with essential development tools
FROM ubuntu:22.04 as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential tools
    curl wget ca-certificates gnupg lsb-release \
    # Development tools
    git build-essential pkg-config \
    # Language runtimes
    python3 python3-pip python3-venv \
    nodejs npm \
    openjdk-17-jdk \
    # System utilities
    jq unzip zip \
    # Security tools
    sudo \
    && rm -rf /var/lib/apt/lists/*

# Install Go
RUN wget https://go.dev/dl/go1.21.5.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.5.linux-amd64.tar.gz \
    && rm go1.21.5.linux-amd64.tar.gz

# Install Rust
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Set up environment
ENV PATH=/usr/local/go/bin:/root/.cargo/bin:$PATH
ENV PYTHONUNBUFFERED=1
ENV NODE_ENV=production

# Create non-root user
RUN groupadd -r agent && useradd -r -g agent -m -s /bin/bash agent

# Development stage
FROM base as development

# Install development dependencies
RUN pip3 install --no-cache-dir \
    # Core dependencies
    requests httpx aiohttp \
    # AI/LLM clients
    openai anthropic \
    # Development tools
    black isort flake8 mypy pytest \
    # Web automation
    playwright \
    # Utilities
    structlog rich typer

# Install Playwright browsers
RUN playwright install --with-deps chromium

# Install Node.js dependencies globally
RUN npm install -g \
    typescript ts-node \
    @types/node \
    prettier eslint \
    jest @types/jest

# Set working directory
WORKDIR /workspace

# Copy agent executor
COPY agent-executor /usr/local/bin/agent-executor
COPY mcp-servers/ /opt/mcp-servers/
COPY scripts/ /opt/scripts/

# Make executables
RUN chmod +x /usr/local/bin/agent-executor \
    && chmod +x /opt/scripts/*.sh \
    && chmod +x /opt/mcp-servers/*/start.sh

# Switch to agent user
USER agent

# Set up agent home directory
ENV HOME=/home/agent
ENV AGENT_HOME=/home/agent/.autocodit
RUN mkdir -p $AGENT_HOME/{logs,cache,temp,artifacts}

# Expose MCP server port
EXPOSE 2301

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:2301/health || exit 1

# Default command
CMD ["/usr/local/bin/agent-executor"]

# Production stage
FROM development as production

# Remove development tools to reduce image size
RUN sudo apt-get remove -y build-essential \
    && sudo apt-get autoremove -y \
    && sudo apt-get clean

# Final optimizations
RUN sudo rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

USER agent
CMD ["/usr/local/bin/agent-executor"]