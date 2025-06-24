# 🧠 Intelligent MCP Gateway

A containerized FastAPI gateway service that provides intelligent routing to Model Context Protocol (MCP) servers with comprehensive chat history management.

## 🌟 Overview

The **Intelligent MCP Gateway** serves as a centralized hub that:
- **🧠 Intelligently routes** user prompts to the most appropriate MCP server based on keyword analysis
- **💾 Manages chat history** with PostgreSQL database integration
- **🔐 Provides authentication** with JWT tokens and development mock auth
- **📱 Offers REST APIs** for complete chat thread and message management
- **🐳 Runs containerized** with Docker and docker-compose for easy deployment
- **🗣️ Natural Language Only**: No tool names, server IDs, or technical knowledge required

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Client Apps   │────│   MCP Gateway   │────│   PostgreSQL    │
│  (Next.js, etc) │    │  (Port 8000)    │    │  (Port 5433)    │
│                 │    │                 │    │                 │
│ • REST API calls│    │ • Intelligent   │    │ • Chat History  │
│ • No MCP logic  │    │   Server Route  │    │ • User Data     │
│ • No Database   │    │ • Chat History  │    │ • Persistence   │
└─────────────────┘    │ • Auth & JWT    │    └─────────────────┘
                       │ • Database ORM  │
                       └─────────────────┘
                                │
                    ┌─────────────────────────┐
                    │      MCP Servers        │
                    │                         │
                    │ • Playwright (Browser)  │
                    │ • Apollo (Space Data)   │
                    │ • Custom Servers...     │
                    └─────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- Node.js 18+ (for development)
- Python 3.11+ (for local development)

### Using Nx (Recommended)

```bash
# Start all containers (builds automatically)
pnpm containers:up

# Check container status
pnpm containers:status

# View logs
pnpm containers:logs

# Stop containers
pnpm containers:down

# Restart with rebuild
pnpm containers:restart
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
- **URL**: `http://localhost:8001/sse`
- **Transport**: Server-Sent Events (SSE)
- **Keywords**: browse, navigate, screenshot, click, type, website, page, browser, web, url, link, google, github, open, visit, scrape, extract, element, button, form, input
- **Examples**:
  - "Take a screenshot of google.com"
  - "Navigate to github.com and click the sign in button"
  - "Extract the text from the homepage"

#### Space Data (→ Apollo Server)
- **URL**: `http://localhost:5001/mcp`
- **Transport**: HTTP
- **Keywords**: space, astronaut, mission, launch, nasa, spacex, rocket, satellite, orbit, celestial, planet, moon, mars, station, iss, crew
- **Examples**:
  - "Who are the astronauts currently in space?"
  - "Show me upcoming SpaceX launches"
  - "Tell me about the Mars mission"

#### Default Fallback
- **Default**: Playwright server for general automation tasks

## 📡 API Reference

### Health Check
```http
GET /health
```
Returns gateway health status.

### Chat Management

#### List User Threads
```http
GET /chat/threads
Authorization: Bearer <token>
```

#### Create Thread
```http
POST /chat/threads
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "My Chat Thread",
  "project_id": "optional-project-id"
}
```

#### Get Thread with Messages
```http
GET /chat/threads/{thread_id}
Authorization: Bearer <token>
```

#### Add Message to Thread
```http
POST /chat/threads/{thread_id}/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "message_id": "unique-message-id",
  "role": "user|assistant",
  "parts": [{"type": "text", "text": "Message content"}],
  "attachments": [],
  "annotations": []
}
```

#### Delete Thread
```http
DELETE /chat/threads/{thread_id}
Authorization: Bearer <token>
```

### The ONLY MCP Endpoint You Need

**POST** `/mcp/chat` - Intelligent natural language interface

```json
{
  "prompt": "Your natural language request",
  "model_name": "openai:gpt-4",
  "thread_id": "optional-thread-id",
  "message_id": "optional-message-id"
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
    "server_capabilities": ["browser_automation", "web_navigation", "..."]
  },
  "error": null,
  "thread_id": "thread-uuid",
  "assistant_message_id": "message-uuid"
}
```

### Optional Debug Endpoints

- **GET** `/mcp/servers` - List available servers and their capabilities
- **POST** `/mcp/query` - Alternative query interface (also intelligent)
- **POST** `/mcp/tools/execute` - Execute specific tools directly

## 🔐 Authentication

### Development Mode
Set `ENVIRONMENT=development` to use mock authentication:
- Any token is accepted
- Mock user ID: `550e8400-e29b-41d4-a716-446655440000`
- Use `Bearer mock-token` for testing

### Production Mode
Use JWT tokens with the following claims:
```json
{
  "sub": "user-uuid",
  "email": "user@example.com",
  "exp": 1234567890
}
```

## ⚙️ Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./mcp_gateway.db` | PostgreSQL connection string |
| `ENVIRONMENT` | `production` | Set to `development` for mock auth |
| `JWT_SECRET_KEY` | `your-secret-key-here` | JWT signing secret |
| `ANTHROPIC_API_KEY` | - | Anthropic API key for Claude models |
| `OPENAI_API_KEY` | - | OpenAI API key for GPT models |

### Container Environment
For containerized deployment, these are automatically set in `docker-compose.yml`:
```yaml
environment:
  DATABASE_URL: postgresql://mcp_user:mcp_password@postgres:5432/mcp_gateway
  ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
  OPENAI_API_KEY: ${OPENAI_API_KEY}
  ENVIRONMENT: development
```

## 🗄️ Database Schema

The gateway uses PostgreSQL with these main tables:

- **users**: User accounts and preferences
- **chat_threads**: Chat conversation threads
- **chat_messages**: Individual messages with parts, attachments, and annotations
- **projects**: Optional project organization
- **sessions**: Authentication sessions
- **mcp_servers**: MCP server configurations

## 🐳 Container Commands

### Nx Integration (Recommended)
```bash
# Single project commands
npx nx container-up mcp-gateway      # Start with build
npx nx container-down mcp-gateway    # Stop containers
npx nx container-restart mcp-gateway # Restart with rebuild
npx nx container-status mcp-gateway  # Check status
npx nx container-logs mcp-gateway    # View logs
npx nx container mcp-gateway         # Build image only

# Multi-project commands (works across all containerized projects)
pnpm containers:up        # Start all containerized projects
pnpm containers:down      # Stop all containerized projects  
pnpm containers:restart   # Restart all with rebuild
pnpm containers:status    # Check status of all containers
pnpm containers:logs      # View logs from all containers

# Or directly with nx
npx nx run-many --target=container-up
npx nx run-many --target=container-down
npx nx run-many --target=container-status
```

### Direct Docker Commands
```bash
# Navigate to gateway directory
cd apps/mcp-gateway

# Start services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild and restart
docker-compose up -d --build --force-recreate
```

## 🛠️ Development

### Local Development Setup

1. **Install Dependencies**:
   ```bash
   cd apps/mcp-gateway
   uv sync
   ```

2. **Start Database**:
   ```bash
   # Using Nx
   npx nx container-up mcp-gateway
   
   # Or just database
   docker-compose up -d postgres
   ```

3. **Run Gateway**:
   ```bash
   # Using Nx
   npx nx serve mcp-gateway
   
   # Or directly
   uv run uvicorn mcp_gateway.main:app --reload --host 0.0.0.0 --port 8000
   ```

### Development Commands
```bash
# Install dependencies
npx nx sync mcp-gateway

# Run the server
npx nx serve mcp-gateway

# Run tests
npx nx test mcp-gateway

# Lint code
npx nx lint mcp-gateway

# Format code
npx nx format mcp-gateway

# Type check
npx nx check-types mcp-gateway
```

### Adding New MCP Servers

1. **Update Server Configuration** in `main.py`:
   ```python
   AVAILABLE_SERVERS = {
       "my-server": {
           "url": "http://localhost:PORT/ENDPOINT",
           "transport": "sse|http",
           "capabilities": ["capability1", "capability2"],
           "keywords": ["keyword1", "keyword2", "keyword3"]
       }
   }
   ```

2. **Add to Server List Endpoint** in the `/mcp/servers` response.

3. **Test the Integration**:
   ```bash
   curl -X POST http://localhost:8000/mcp/chat \
     -H "Authorization: Bearer mock-token" \
     -H "Content-Type: application/json" \
     -d '{"prompt": "test prompt with your keywords"}'
   ```

## 🌟 Integration Examples

### Python Client
```python
import requests

def mcp_chat(prompt, thread_id=None):
    return requests.post('http://localhost:8000/mcp/chat',
        headers={'Authorization': 'Bearer mock-token'},
        json={
            'prompt': prompt, 
            'model_name': 'openai:gpt-4',
            'thread_id': thread_id
        }
    ).json()

# Usage - pure natural language!
result = mcp_chat("Navigate to google.com")
astronauts = mcp_chat("Who is in space right now?")
```

### JavaScript/Node.js
```javascript
async function mcpChat(prompt, threadId = null) {
    const response = await fetch('http://localhost:8000/mcp/chat', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer mock-token',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            prompt,
            model_name: 'openai:gpt-4',
            thread_id: threadId
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

## 📊 Monitoring and Debugging

### Health Checks
- Gateway: `http://localhost:8000/health`
- Database connectivity is verified during startup
- Containers have built-in health checks

### Logs
```bash
# Container logs
pnpm containers:logs

# Or specific service
docker-compose logs -f gateway
docker-compose logs -f postgres

# Nx commands
npx nx container-logs mcp-gateway
```

### Database Access
```bash
# Connect to PostgreSQL container
docker exec -it mcp-gateway-postgres-1 psql -U mcp_user -d mcp_gateway

# Common queries
\dt                              # List tables
SELECT * FROM users;             # View users
SELECT * FROM chat_threads;      # View threads
SELECT * FROM chat_messages;     # View messages
```

### Debug Information
Gateway logs show intelligent routing decisions:
```
🧠 Intelligent routing: 'Take a screenshot of github.com' → playwright server
🧠 Intelligent routing: 'Who are astronauts in space?' → apollo server
✅ Database tables created successfully
✅ Mock user created for development
```

## 🧪 Testing

### Automated Tests
```bash
# Run test script
node test-containerized-gateway.js

# Expected output shows:
# ✅ Gateway health check
# ✅ Thread creation
# ✅ Message storage
# ✅ Data persistence
```

### Manual Testing
```bash
# Health check
curl http://localhost:8000/health

# Create thread
curl -X POST http://localhost:8000/chat/threads \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Thread"}'

# Intelligent chat
curl -X POST http://localhost:8000/mcp/chat \
  -H "Authorization: Bearer mock-token" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Take a screenshot of google.com", "model_name": "openai:gpt-4"}'
```

## 🔧 Troubleshooting

### Common Issues

**Port Already in Use**:
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5433

# Kill the process or change ports in docker-compose.yml
```

**Database Connection Failed**:
```bash
# Check PostgreSQL is running
docker-compose ps postgres

# Check logs
docker-compose logs postgres

# Restart database
docker-compose restart postgres
```

**Container Build Failed**:
```bash
# Clean Docker cache
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache gateway
```

**Mock User Not Found**:
- Ensure `ENVIRONMENT=development` is set
- Check startup logs for "Mock user created for development"
- Restart containers if needed

**MCP Server Not Responding**:
- Check that MCP servers are running on expected ports
- Test server connectivity: `curl http://localhost:8001/sse`
- Review gateway logs for connection errors

### Performance Tuning

**Database**:
- Monitor connection pool usage
- Adjust PostgreSQL settings in docker-compose.yml
- Consider read replicas for high traffic

**Gateway**:
- Scale horizontally with multiple gateway instances
- Use load balancer in front of gateway
- Monitor MCP server response times

## 🚀 Benefits

- **Zero Tool Knowledge**: Clients don't need to know about servers, tools, or MCP protocols
- **Pure Natural Language**: Just describe what you want in plain English
- **Universal Integration**: Works with any HTTP client in any language
- **Intelligent Routing**: Gateway automatically selects the best server for each task
- **Future Proof**: Add new servers/tools without changing any client code
- **Containerized**: Easy deployment and scaling with Docker
- **Database Persistence**: Full chat history and user management
- **Development Ready**: Mock authentication and automatic setup

## 🏷️ License

MIT License - see project root for details.