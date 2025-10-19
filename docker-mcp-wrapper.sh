#!/bin/bash
# Wrapper script to run MCP server in Docker
# Logs to /tmp/mcp-bitbucket-debug.log for debugging

echo "$(date): Starting MCP Bitbucket Docker wrapper" >> /tmp/mcp-bitbucket-debug.log
echo "$(date): Environment variables: BITBUCKET_USERNAME=$BITBUCKET_USERNAME BITBUCKET_WORKSPACE=$BITBUCKET_WORKSPACE" >> /tmp/mcp-bitbucket-debug.log

exec /usr/bin/docker run -i --rm \
  -e BITBUCKET_URL="${BITBUCKET_URL}" \
  -e BITBUCKET_USERNAME="${BITBUCKET_USERNAME}" \
  -e BITBUCKET_PASSWORD="${BITBUCKET_PASSWORD}" \
  -e BITBUCKET_WORKSPACE="${BITBUCKET_WORKSPACE}" \
  -e BITBUCKET_TOKEN="${BITBUCKET_TOKEN:-}" \
  -e FASTMCP_LOG_LEVEL="${FASTMCP_LOG_LEVEL:-INFO}" \
  mcp-bitbucket:latest

