#!/bin/bash
# Curl examples for MCP Gateway
# Demonstrates how any HTTP client can integrate with the MCP Gateway

GATEWAY_URL="http://localhost:8000"
AUTH_TOKEN="mock-token"

echo "🚀 MCP Gateway cURL Examples"
echo "============================"

echo ""
echo "1. Get available MCP servers:"
echo "curl -H \"Authorization: Bearer $AUTH_TOKEN\" $GATEWAY_URL/mcp/servers"
curl -s -H "Authorization: Bearer $AUTH_TOKEN" "$GATEWAY_URL/mcp/servers" | jq '.'

echo ""
echo ""
echo "2. Execute a specific tool (Playwright navigate):"
echo "curl -X POST -H \"Authorization: Bearer $AUTH_TOKEN\" -H \"Content-Type: application/json\" \\"
echo "  -d '{\"server_id\": \"playwright\", \"tool_name\": \"browser_navigate\", \"parameters\": {\"url\": \"https://example.com\"}}' \\"
echo "  $GATEWAY_URL/mcp/tools/execute"

curl -s -X POST -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"server_id": "playwright", "tool_name": "browser_navigate", "parameters": {"url": "https://example.com"}}' \
  "$GATEWAY_URL/mcp/tools/execute" | jq '.result' | head -c 200

echo "..."
echo ""
echo ""
echo "3. Send a natural language query:"
echo "curl -X POST -H \"Authorization: Bearer $AUTH_TOKEN\" -H \"Content-Type: application/json\" \\"
echo "  -d '{\"prompt\": \"Take a screenshot\", \"server_url\": \"http://localhost:8001/sse\"}' \\"
echo "  $GATEWAY_URL/mcp/query"

curl -s -X POST -H "Authorization: Bearer $AUTH_TOKEN" -H "Content-Type: application/json" \
  -d '{"prompt": "Take a screenshot", "server_url": "http://localhost:8001/sse"}' \
  "$GATEWAY_URL/mcp/query" | jq '.result' | head -c 200

echo "..."
echo ""
echo ""
echo "4. Disconnect from a server:"
echo "curl -X DELETE -H \"Authorization: Bearer $AUTH_TOKEN\" $GATEWAY_URL/mcp/servers/playwright"

echo ""
echo "🎉 Any HTTP client can integrate with these simple endpoints!"
echo ""
echo "Available endpoints:"
echo "  GET    /mcp/servers           - List available servers"
echo "  POST   /mcp/tools/execute     - Execute specific tools"
echo "  POST   /mcp/query             - Natural language queries"
echo "  POST   /mcp/chat              - Chat with conversation context"
echo "  DELETE /mcp/servers/{id}      - Disconnect from server"