#!/bin/bash

echo "Testing MCP Gateway to Playwright MCP Server connection..."

# Test 1: Check if MCP Gateway is running
echo "1. Testing MCP Gateway health..."
curl -s http://localhost:8000/health | jq || echo "MCP Gateway not responding"

# Test 2: Check if Playwright MCP Server is running
echo -e "\n2. Testing Playwright MCP Server..."
curl -s http://localhost:8001 | head -20 || echo "Playwright MCP Server not responding"

# Test 3: Test MCP query through gateway (using mock auth)
echo -e "\n3. Testing MCP query through gateway..."
curl -X POST http://localhost:8000/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "prompt": "What tools are available?",
    "server_url": "http://localhost:8001/mcp",
    "model_name": "openai:gpt-4.1"
  }' | jq || echo "MCP query failed"

echo -e "\nTest complete!"