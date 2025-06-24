# 🔌 MCP Gateway API Reference

Complete API documentation for the MCP Gateway service.

## 📋 Base Information

- **Base URL**: `http://localhost:8000`
- **Protocol**: HTTP/HTTPS
- **Content Type**: `application/json`
- **Authentication**: Bearer JWT tokens

## 🔐 Authentication

### Production Mode
```http
Authorization: Bearer <jwt_token>
```

JWT token must contain:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com", 
  "exp": 1234567890
}
```

### Development Mode
```http
Authorization: Bearer mock-token
```

When `ENVIRONMENT=development`, any token is accepted and maps to:
- User ID: `550e8400-e29b-41d4-a716-446655440000`
- Email: `mock@example.com`

## 🏥 Health & Status

### GET /health
Get gateway health status.

**Response:**
```json
{
  "status": "healthy",
  "service": "mcp-gateway", 
  "timestamp": "2025-06-24T03:56:00Z",
  "database": "connected",
  "servers": ["playwright", "apollo"]
}
```

### GET /
Get service information and available endpoints.

**Response:**
```json
{
  "message": "MCP Gateway Service is running",
  "service": "mcp-gateway",
  "version": "1.0.0",
  "endpoints": {
    "health": "/health",
    "chat": "/mcp/chat", 
    "servers": "/mcp/servers",
    "threads": "/chat/threads"
  }
}
```

## 🧠 Intelligent MCP Chat

### POST /mcp/chat
**The primary endpoint** - Intelligent natural language interface to all MCP servers.

**Request:**
```json
{
  "prompt": "Take a screenshot of google.com",
  "model_name": "openai:gpt-4",
  "thread_id": "optional-thread-uuid",
  "message_id": "optional-message-uuid",
  "system_prompt": "optional-custom-system-prompt"
}
```

**Parameters:**
- `prompt` (required): Natural language request
- `model_name` (optional): LLM model to use, defaults to `openai:gpt-4.1`
- `thread_id` (optional): Thread ID for conversation context
- `message_id` (optional): Unique message ID for tracking
- `system_prompt` (optional): Custom system prompt override

**Response:**
```json
{
  "result": "I've taken a screenshot of google.com. The page shows...",
  "usage": {
    "prompt_tokens": 156,
    "completion_tokens": 89,
    "total_tokens": 245,
    "selected_server": "playwright",
    "server_capabilities": ["browser_automation", "web_navigation"]
  },
  "error": null,
  "thread_id": "thread-uuid",
  "assistant_message_id": "message-uuid"
}
```

**Intelligence Features:**
- Automatically selects best MCP server based on keywords
- Saves conversation to thread if `thread_id` provided
- Returns server selection reasoning in usage data

**Example Routing:**
```bash
# Browser automation → Playwright
curl -X POST http://localhost:8000/mcp/chat \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Navigate to github.com and take a screenshot"}'

# Space data → Apollo  
curl -X POST http://localhost:8000/mcp/chat \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Who are the astronauts currently in space?"}'
```

### POST /mcp/query
Alternative intelligent MCP interface (similar to `/mcp/chat` but without thread management).

**Request:**
```json
{
  "prompt": "What browser tools are available?",
  "model_name": "openai:gpt-4",
  "system_prompt": "You are a helpful assistant."
}
```

**Response:**
```json
{
  "result": "Available browser tools include navigation, screenshots...",
  "usage": {
    "requests": 1,
    "total_tokens": 234,
    "selected_server": "playwright"
  },
  "error": null
}
```

## 🎛️ MCP Server Management

### GET /mcp/servers
List all available MCP servers and their capabilities.

**Response:**
```json
{
  "servers": [
    {
      "id": "playwright",
      "name": "Playwright Browser Automation",
      "description": "Browser automation tools for web scraping, testing, and interaction",
      "server_url": "http://localhost:8001/sse",
      "status": "available",
      "transport": "sse",
      "capabilities": [
        "browser_navigation", "web_scraping", "ui_testing", 
        "screenshot_capture", "form_automation"
      ],
      "tools": [
        "browser_navigate", "browser_click", "browser_type",
        "browser_screenshot", "browser_wait_for", "browser_extract_text"
      ]
    },
    {
      "id": "apollo", 
      "name": "Apollo Space Data",
      "description": "Access to space mission data, astronaut information, and celestial body details",
      "server_url": "http://localhost:5001/mcp",
      "status": "available",
      "transport": "http",
      "capabilities": [
        "space_data", "mission_tracking", "astronaut_info",
        "celestial_bodies", "launch_schedules"
      ],
      "tools": [
        "get_astronaut_details", "search_upcoming_launches",
        "get_astronauts_currently_in_space", "explore_celestial_bodies"
      ]
    }
  ],
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "active_sessions": 2
}
```

### POST /mcp/tools/execute
Execute a specific tool on a specific MCP server.

**Request:**
```json
{
  "server_id": "playwright",
  "tool_name": "browser_screenshot", 
  "parameters": {
    "url": "https://google.com",
    "viewport": {"width": 1280, "height": 720}
  },
  "model_name": "openai:gpt-4"
}
```

**Response:**
```json
{
  "result": "Screenshot captured successfully. The image shows...",
  "usage": {
    "requests": 1,
    "total_tokens": 156,
    "server_id": "playwright",
    "tool_name": "browser_screenshot"
  },
  "error": null
}
```

### DELETE /mcp/servers/{server_id}
Disconnect from a specific MCP server.

**Response:**
```json
{
  "message": "Disconnected from server playwright"
}
```

## 💬 Chat Thread Management

### GET /chat/threads
Get all chat threads for the authenticated user.

**Response:**
```json
{
  "threads": [
    {
      "id": "thread-uuid",
      "title": "Browser Automation Chat",
      "user_id": "user-uuid",
      "project_id": null,
      "created_at": "2024-01-15T10:30:00Z",
      "last_message_at": "2024-01-15T11:45:00Z"
    }
  ]
}
```

### POST /chat/threads
Create a new chat thread.

**Request:**
```json
{
  "title": "My New Chat Thread",
  "project_id": "optional-project-uuid",
  "thread_id": "optional-custom-uuid"
}
```

**Response:**
```json
{
  "id": "thread-uuid",
  "title": "My New Chat Thread", 
  "user_id": "user-uuid",
  "project_id": null,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### GET /chat/threads/{thread_id}
Get a specific thread with all its messages.

**Response:**
```json
{
  "id": "thread-uuid",
  "title": "Browser Automation Chat",
  "user_id": "user-uuid", 
  "project_id": null,
  "created_at": "2024-01-15T10:30:00Z",
  "messages": [
    {
      "id": "message-uuid",
      "role": "user",
      "parts": [
        {"type": "text", "text": "Take a screenshot of google.com"}
      ],
      "attachments": [],
      "annotations": [],
      "model": null,
      "created_at": "2024-01-15T10:30:00Z"
    },
    {
      "id": "assistant-message-uuid", 
      "role": "assistant",
      "parts": [
        {"type": "text", "text": "I've taken a screenshot of google.com..."}
      ],
      "attachments": [],
      "annotations": [
        {
          "type": "gateway-response",
          "selected_server": "playwright",
          "usage": {"total_tokens": 245}
        }
      ],
      "model": "openai:gpt-4",
      "created_at": "2024-01-15T10:31:00Z"
    }
  ]
}
```

### PUT /chat/threads/{thread_id}
Update a chat thread.

**Request:**
```json
{
  "title": "Updated Thread Title",
  "project_id": "new-project-uuid"
}
```

**Response:**
```json
{
  "id": "thread-uuid",
  "title": "Updated Thread Title",
  "user_id": "user-uuid",
  "project_id": "new-project-uuid", 
  "created_at": "2024-01-15T10:30:00Z"
}
```

### DELETE /chat/threads/{thread_id}
Delete a chat thread and all its messages.

**Response:**
```json
{
  "message": "Thread deleted successfully"
}
```

## 📝 Message Management

### POST /chat/threads/{thread_id}/messages
Add a message to a chat thread.

**Request:**
```json
{
  "message_id": "unique-message-id",
  "role": "user",
  "parts": [
    {"type": "text", "text": "Hello, can you help me?"}
  ],
  "attachments": [
    {
      "type": "image",
      "url": "https://example.com/image.png",
      "description": "Screenshot"
    }
  ],
  "annotations": [
    {
      "type": "user-note", 
      "content": "Important message"
    }
  ],
  "model": "openai:gpt-4"
}
```

**Response:**
```json
{
  "id": "unique-message-id",
  "thread_id": "thread-uuid",
  "role": "user",
  "parts": [
    {"type": "text", "text": "Hello, can you help me?"}
  ],
  "attachments": [
    {
      "type": "image",
      "url": "https://example.com/image.png", 
      "description": "Screenshot"
    }
  ],
  "annotations": [
    {
      "type": "user-note",
      "content": "Important message" 
    }
  ],
  "model": "openai:gpt-4",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## 🧪 Development & Testing Endpoints

### GET /test/apollo
Test connectivity to Apollo MCP server.

**Response:**
```json
{
  "status": "success",
  "apollo_server": "reachable",
  "mcp_endpoint_status": 200,
  "message": "Apollo MCP server is reachable"
}
```

### GET /test/playwright  
Test connectivity to Playwright MCP server.

**Response:**
```json
{
  "status": "success",
  "playwright_server": "reachable",
  "mcp_endpoint_status": 400,
  "message": "Playwright MCP server is reachable (400 on /mcp is expected)"
}
```

### GET /test/env
Test environment variable access.

**Response:**
```json
{
  "openai_key_present": true,
  "openai_key_prefix": "sk-proj-...",
  "anthropic_key_present": true,
  "environment": "development"
}
```

### POST /test/mcp
Test actual MCP query to Playwright server.

**Response:**
```json
{
  "status": "success",
  "message": "MCP query successful",
  "result_preview": "Available tools: browser_navigate, browser_click..."
}
```

### POST /test/apollo-mcp
Test actual MCP query to Apollo server.

**Response:**
```json
{
  "status": "success", 
  "message": "Apollo MCP query successful",
  "result_preview": "Available space data tools: get_astronaut_details..."
}
```

## ❌ Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Common HTTP Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (invalid/missing token)
- **404**: Not Found (thread/message not found)
- **500**: Internal Server Error (MCP server issues, database errors)

### Example Error Responses

**Authentication Error (401):**
```json
{
  "detail": "Could not validate credentials"
}
```

**Thread Not Found (404):**
```json
{
  "detail": "Thread not found"
}
```

**MCP Server Error (500):**
```json
{
  "detail": "MCP chat failed: Connection timeout to playwright server"
}
```

## 🚀 Usage Examples

### Python Client
```python
import requests

class MCPGatewayClient:
    def __init__(self, base_url="http://localhost:8000", token="mock-token"):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def chat(self, prompt, thread_id=None):
        return requests.post(
            f"{self.base_url}/mcp/chat",
            headers=self.headers,
            json={"prompt": prompt, "thread_id": thread_id}
        ).json()
    
    def get_threads(self):
        return requests.get(
            f"{self.base_url}/chat/threads",
            headers=self.headers
        ).json()

# Usage
client = MCPGatewayClient()
result = client.chat("Take a screenshot of github.com")
threads = client.get_threads()
```

### JavaScript/Node.js Client
```javascript
class MCPGatewayClient {
  constructor(baseUrl = 'http://localhost:8000', token = 'mock-token') {
    this.baseUrl = baseUrl;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async chat(prompt, threadId = null) {
    const response = await fetch(`${this.baseUrl}/mcp/chat`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ prompt, thread_id: threadId })
    });
    return response.json();
  }

  async getThreads() {
    const response = await fetch(`${this.baseUrl}/chat/threads`, {
      headers: this.headers
    });
    return response.json();
  }
}

// Usage
const client = new MCPGatewayClient();
const result = await client.chat('Who are the astronauts in space?');
const threads = await client.getThreads();
```

### cURL Examples
```bash
# Intelligent chat
curl -X POST http://localhost:8000/mcp/chat \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Take a screenshot of apple.com"}'

# Create thread
curl -X POST http://localhost:8000/chat/threads \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat Thread"}'

# List servers
curl -H "Authorization: Bearer mock-token" \
  http://localhost:8000/mcp/servers

# Health check
curl http://localhost:8000/health
```

## 🔄 Rate Limiting

Currently no rate limiting is implemented. For production deployments, consider:

- Adding rate limiting middleware
- Implementing per-user quotas
- Monitoring MCP server response times
- Setting timeouts for long-running operations

## 🔒 Security Considerations

- **JWT Validation**: All endpoints except `/health` require valid JWT tokens
- **User Isolation**: All operations are scoped to the authenticated user
- **Input Validation**: All request parameters are validated
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **CORS Configuration**: Configured for specific origins only

## 📊 Monitoring Integration

The gateway provides several endpoints for monitoring and observability:

- **Health Checks**: `/health` for service status
- **Metrics**: Usage data in all MCP responses
- **Logging**: Structured logging for all operations
- **Error Tracking**: Detailed error responses with context