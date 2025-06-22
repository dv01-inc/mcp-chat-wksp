# Simplified MCP Gateway Architecture

## Overview

The MCP Gateway architecture has been refactored to follow a "dumb client" approach, where the Next.js app (and any other client) only handles:

1. **UI** - User interface components
2. **Authentication** - JWT token management  
3. **Gateway Communication** - Simple HTTP calls to the MCP Gateway

This makes it extremely easy to integrate **any client** (Slack apps, mobile apps, CLI tools, etc.) with the MCP ecosystem.

## Architecture Diagram

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Any Client    │    │   MCP Gateway   │    │   MCP Servers   │
│                 │    │                 │    │                 │
│ • Next.js App   │◄──►│ • Server Discovery  │◄──►│ • Playwright     │
│ • Slack Bot     │    │ • Tool Execution    │    │ • Apollo        │
│ • Python Script│    │ • Authentication    │    │ • Custom Servers│
│ • CLI Tool      │    │ • Session Mgmt     │    │                 │
│ • Mobile App    │    │ • Protocol Handling│    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Gateway API Endpoints

### 🔍 **Server Discovery**
```http
GET /mcp/servers
Authorization: Bearer <token>
```

**Response:**
```json
{
  "servers": [
    {
      "id": "playwright",
      "name": "Playwright Browser Automation", 
      "description": "Browser automation tools...",
      "server_url": "http://localhost:8001/sse",
      "status": "available",
      "transport": "sse",
      "capabilities": ["browser_navigation", "web_scraping", ...],
      "tools": ["browser_navigate", "browser_click", ...]
    }
  ],
  "user_id": "user123",
  "active_sessions": 1
}
```

### 🔧 **Tool Execution**
```http
POST /mcp/tools/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "server_id": "playwright",
  "tool_name": "browser_navigate", 
  "parameters": {"url": "https://example.com"}
}
```

### 💬 **Natural Language Queries**
```http
POST /mcp/query
Authorization: Bearer <token>
Content-Type: application/json

{
  "prompt": "Take a screenshot of the homepage",
  "server_url": "http://localhost:8001/sse"
}
```

### 💭 **Chat with Context**
```http
POST /mcp/chat
Authorization: Bearer <token>
Content-Type: application/json

{
  "prompt": "Now click the login button",
  "server_url": "http://localhost:8001/sse"
}
```

## Client Integration Examples

### 🌐 **Next.js/React Client**
```typescript
import { useMCPGateway } from '@/hooks/use-mcp-gateway';

function MyComponent() {
  const { servers, executeTool, query } = useMCPGateway();
  
  const handleNavigate = async () => {
    await executeTool({
      server_id: 'playwright',
      tool_name: 'browser_navigate',
      parameters: { url: 'https://example.com' }
    });
  };
  
  return <button onClick={handleNavigate}>Navigate</button>;
}
```

### 🐍 **Python Client**
```python
import requests

class MCPClient:
    def __init__(self, gateway_url, auth_token):
        self.gateway_url = gateway_url
        self.headers = {"Authorization": f"Bearer {auth_token}"}
    
    def get_servers(self):
        response = requests.get(f"{self.gateway_url}/mcp/servers", 
                              headers=self.headers)
        return response.json()
    
    def execute_tool(self, server_id, tool_name, parameters=None):
        data = {
            "server_id": server_id,
            "tool_name": tool_name, 
            "parameters": parameters or {}
        }
        response = requests.post(f"{self.gateway_url}/mcp/tools/execute",
                               headers=self.headers, json=data)
        return response.json()

# Usage
client = MCPClient("http://localhost:8000", "mock-token")
servers = client.get_servers()
result = client.execute_tool("playwright", "browser_navigate", {"url": "https://github.com"})
```

### 📱 **cURL/Shell Script**
```bash
# Get servers
curl -H "Authorization: Bearer mock-token" \
     http://localhost:8000/mcp/servers

# Execute tool
curl -X POST \
     -H "Authorization: Bearer mock-token" \
     -H "Content-Type: application/json" \
     -d '{"server_id": "playwright", "tool_name": "browser_screenshot"}' \
     http://localhost:8000/mcp/tools/execute
```

### 🤖 **Slack Bot Example**
```javascript
// Slack bot handler
app.command('/mcp', async ({ command, ack, respond }) => {
  await ack();
  
  const mcpClient = new MCPGatewayClient('http://localhost:8000', process.env.MCP_TOKEN);
  
  if (command.text.startsWith('screenshot')) {
    const result = await mcpClient.executeTool('playwright', 'browser_screenshot');
    await respond(`Screenshot taken: ${result.result}`);
  }
});
```

## Benefits of This Architecture

### ✅ **For Developers**
- **Simple Integration**: Just HTTP calls, any language/framework
- **No MCP Complexity**: Gateway handles all MCP protocol details
- **Rich Discovery**: Servers, tools, and capabilities auto-discovered
- **Authentication**: JWT-based auth built-in
- **Session Management**: User isolation and connection pooling

### ✅ **For Clients**
- **Plug and Play**: Add new servers without client changes
- **Protocol Agnostic**: SSE, HTTP, WebSocket all handled by gateway
- **Error Handling**: Centralized error handling and retries
- **Caching**: Connection reuse and response caching
- **Monitoring**: Usage tracking and analytics

### ✅ **For Operations**
- **Centralized**: Single gateway to monitor and manage
- **Scalable**: Gateway can be load balanced and scaled
- **Secure**: Authentication and authorization in one place
- **Observable**: Centralized logging and metrics

## Available MCP Servers

### 🎭 **Playwright (Browser Automation)**
- **URL**: `http://localhost:8001/sse`
- **Transport**: SSE
- **Tools**: navigate, click, type, screenshot, wait, extract text
- **Use Cases**: Web scraping, UI testing, automation

### 🚀 **Apollo (Space Data)**
- **URL**: `http://localhost:5001/mcp` 
- **Transport**: HTTP (Streamable)
- **Tools**: astronaut details, launch schedules, space missions
- **Use Cases**: Space data queries, mission tracking

## Example Use Cases

### 📊 **Dashboard Integration**
```javascript
// Auto-refresh server status
const servers = await mcpClient.getServers();
const healthStatus = servers.map(s => ({ name: s.name, status: s.status }));
```

### 🔄 **Workflow Automation**
```python
# Multi-step automation
mcpClient.execute_tool("playwright", "browser_navigate", {"url": "https://site.com"})
mcpClient.execute_tool("playwright", "browser_click", {"selector": "#login"}) 
mcpClient.execute_tool("playwright", "browser_screenshot", {"path": "result.png"})
```

### 💬 **Conversational Interface**
```typescript
// Natural language to tool execution
const response = await mcpClient.query({
  prompt: "Take a screenshot of the NASA homepage",
  server_url: "http://localhost:8001/sse"
});
```

This architecture makes MCP integration as simple as making HTTP requests, enabling rapid development of new interfaces and automations! 🎉