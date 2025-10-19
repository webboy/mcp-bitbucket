# Use Python 3.10 slim base image for smaller footprint
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install uv for dependency management
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY README.md ./
COPY src/ ./src/

# Install dependencies using uv
RUN uv pip install --system -e .

# Create non-root user for security
RUN useradd -m -u 1000 mcp && \
    chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose port for HTTP/SSE transport
EXPOSE 9000

# Use SSE transport by default for Docker
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=9000

# Set entrypoint to the CLI command
ENTRYPOINT ["mcp-bitbucket"]

