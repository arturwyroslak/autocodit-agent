# =============================================================================
# AutoCodit Agent Runner - Lightweight execution container
# =============================================================================

# Multi-stage build for minimal production image
FROM ubuntu:22.04 as base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Essential tools
    curl wget ca-certificates \
    git openssh-client \
    # Development tools
    build-essential \
    # Node.js 20.x
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    # Python 3.11
    && apt-get install -y python3 python3-pip python3-dev \
    # Go 1.21
    && wget https://go.dev/dl/go1.21.0.linux-amd64.tar.gz \
    && tar -C /usr/local -xzf go1.21.0.linux-amd64.tar.gz \
    && rm go1.21.0.linux-amd64.tar.gz \
    # Java 17
    && apt-get install -y openjdk-17-jdk \
    # Docker CLI (for Docker-in-Docker if needed)
    && curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu jammy stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null \
    && apt-get update && apt-get install -y docker-ce-cli \
    # Cleanup
    && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Set up PATH for Go
ENV PATH="/usr/local/go/bin:${PATH}"
ENV GOPATH="/go"
ENV PATH="$GOPATH/bin:$PATH"

# Create workspace directory
WORKDIR /workspace

# Install global Node.js tools
RUN npm install -g \
    typescript \
    @types/node \
    jest \
    eslint \
    prettier \
    nodemon

# Install global Python tools
RUN pip3 install --no-cache-dir \
    pytest \
    black \
    flake8 \
    mypy \
    requests \
    aiohttp

# Copy agent executor
COPY agent-executor /usr/local/bin/agent-executor
RUN chmod +x /usr/local/bin/agent-executor

# Copy MCP servers
COPY mcp-servers/ /usr/local/lib/mcp-servers/
RUN chmod +x /usr/local/lib/mcp-servers/*/bin/*

# Copy agent configuration
COPY config/ /etc/autocodit-agent/

# Set up user (non-root for security)
RUN groupadd -r agent && useradd -r -g agent -d /workspace agent \
    && chown -R agent:agent /workspace

# Switch to agent user
USER agent

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default command
CMD ["/usr/local/bin/agent-executor"]