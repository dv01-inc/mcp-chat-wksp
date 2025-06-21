#!/bin/bash

echo "🧪 Testing Gateway Integration..."
echo ""

# Test 1: Gateway Health
echo "1️⃣ Testing Gateway Health..."
curl -s http://localhost:8002/api/health | jq '.' || echo "❌ Gateway not responding"
echo ""

# Test 2: Gateway Environment
echo "2️⃣ Testing Gateway Environment..."
curl -s http://localhost:8002/api/test/env | jq '.' || echo "❌ Gateway env test failed"
echo ""

# Test 3: Apollo MCP Connection
echo "3️⃣ Testing Apollo MCP Connection..."
curl -s http://localhost:8002/api/test/apollo | jq '.' || echo "❌ Apollo test failed"
echo ""

# Test 4: Authenticated MCP Query
echo "4️⃣ Testing Authenticated MCP Query..."
curl -s -X POST http://localhost:8002/api/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "prompt": "Who are the astronauts currently in space?",
    "serverUrl": "http://localhost:5000/mcp",
    "modelName": "gpt-4"
  }' | jq '.' || echo "❌ MCP query failed"
echo ""

# Test 5: Chat App Integration (if running)
echo "5️⃣ Testing Chat App Gateway Integration..."
curl -s http://localhost:4200/api/test/gateway | jq '.' || echo "⚠️ Chat App not running or endpoint not available"
echo ""

echo "🎉 Gateway Integration Test Complete!"