# 🧠 Intelligent MCP Gateway

The **Intelligent MCP Gateway** provides a single, natural language interface to all your MCP servers. Clients send pure natural language requests, and the gateway automatically selects the right server and tools.

## 🌟 Key Features

- **🧠 Intelligent Routing**: Automatically selects the best MCP server based on natural language
- **🗣️ Natural Language Only**: No tool names, server IDs, or technical knowledge required
- **🔐 JWT Authentication**: Secure, user-isolated MCP calls
- **📱 Universal Client Support**: Works with any HTTP client in any language
- **💬 Persistent Chat History**: Maintains context per user and conversation
- **🔄 Tool Orchestration**: Automatically chains multiple operations
- **⚡ Real-time Streaming**: Supports streaming responses from MCP servers

## 🚀 Quick Start

### Start the Gateway
```bash
npx nx run mcp-gateway:serve
```

### Send Natural Language Requests
```bash
curl -X POST http://localhost:8000/mcp/chat \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Take a screenshot of github.com",
    "model_name": "openai:gpt-4"
  }'
```

## 🧠 How Intelligence Works

### Automatic Server Selection

The gateway analyzes your natural language prompt and automatically routes to the best server:

#### Browser Automation (→ Playwright Server)
- **Keywords**: navigate, screenshot, click, type, website, browser, url, visit, scrape
- **Examples**:
  - "Take a screenshot of google.com"
  - "Navigate to github.com and click the sign in button"
  - "Extract the text from the homepage"

#### Space Data (→ Apollo Server)  
- **Keywords**: space, astronaut, mission, launch, nasa, spacex, rocket, orbit, mars
- **Examples**:
  - "Who are the astronauts currently in space?"
  - "Show me upcoming SpaceX launches"
  - "Tell me about the Mars mission"

#### Default Fallback
- **Default**: Playwright server for general automation tasks

## 📡 API Reference

### The ONLY Endpoint You Need

**POST** `/mcp/chat` - Intelligent natural language interface

```json
{
  "prompt": "Your natural language request",
  "model_name": "openai:gpt-4"
}
```

**Response:**
```json
{
  "result": "Natural language response with task results",
  "usage": {
    "prompt_tokens": 3647,
    "completion_tokens": 38,
    "total_tokens": 3685,
    "selected_server": "playwright",
    "server_capabilities": ["browser_automation", "web_navigation", ...]
  },
  "error": null
}
```

### Optional Debug Endpoints

- **GET** `/mcp/servers` - List available servers and their capabilities
- **GET** `/health` - Service health status
- **POST** `/mcp/query` - Alternative query interface (also intelligent)

## Configuration

Copy `.env.example` to `.env` and configure:

- `JWT_SECRET_KEY` - Secret key for JWT token signing
- `ENVIRONMENT` - Set to "development" for mock auth
- `OPENAI_API_KEY` - OpenAI API key for LLM models
- `ANTHROPIC_API_KEY` - Anthropic API key for Claude models

## Development

```bash
# Install dependencies
nx run mcp-gateway:sync

# Run the server
nx run mcp-gateway:serve

# Run tests
nx run mcp-gateway:test

# Lint code
nx run mcp-gateway:lint
```

## 🌟 Integration Examples

### Python Client
```python
import requests

def mcp_chat(prompt):
    return requests.post('http://localhost:8000/mcp/chat',
        headers={'Authorization': 'Bearer mock-token'},
        json={'prompt': prompt, 'model_name': 'openai:gpt-4'}
    ).json()

# Usage - pure natural language!
result = mcp_chat("Navigate to google.com")
astronauts = mcp_chat("Who is in space right now?")
```

### JavaScript/Node.js
```javascript
async function mcpChat(prompt) {
    const response = await fetch('http://localhost:8000/mcp/chat', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer mock-token',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt,
            model_name: 'openai:gpt-4'
        })
    });
    return response.json();
}

// Usage
const result = await mcpChat("Take a screenshot of apple.com");
```

### Slack Bot Integration
```javascript
// Slack Bot - Zero MCP Knowledge Required
app.command('/screenshot', async ({ command, ack, respond }) => {
  const result = await mcpChat(`Take a screenshot of ${command.text}`);
  await respond(`Screenshot taken: ${result.result}`);
});
```

### CLI Script
```bash
#!/bin/bash
mcp_chat() {
    curl -s -X POST http://localhost:8000/mcp/chat \
        -H "Authorization: Bearer mock-token" \
        -H "Content-Type: application/json" \
        -d "{\"prompt\": \"$1\", \"model_name\": \"openai:gpt-4\"}"
}

# Usage
mcp_chat "Take a screenshot of github.com"
mcp_chat "Who are the astronauts in space?"
```

## 🚀 Benefits

- **Zero Tool Knowledge**: Clients don't need to know about servers, tools, or MCP protocols
- **Pure Natural Language**: Just describe what you want in plain English
- **Universal Integration**: Works with any HTTP client in any language
- **Intelligent Routing**: Gateway automatically selects the best server for each task
- **Future Proof**: Add new servers/tools without changing any client code

## 🔍 Debugging

Gateway logs show intelligent routing decisions:
```
🧠 Intelligent routing: 'Take a screenshot of github.com' → playwright server
🧠 Intelligent routing: 'Who are astronauts in space?' → apollo server
```