# MCP Chat Workspace

A full-stack Nx monorepo for Model Context Protocol (MCP) chat applications with browser automation capabilities.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js App   │────│  MCP Gateway    │────│ Playwright MCP  │
│   (Frontend)    │    │ (Java/Python)   │    │    Server       │
│   Port: 4200    │    │ Port: 8000/8002 │    │   Port: 8001    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Projects

### **Apps**
- **`mcp-chat-app`** - Next.js frontend application with MCP integration
- **`mcp-gateway`** - Python FastAPI service for authenticated MCP calls  
- **`mcp-gateway-java`** - Java Spring Boot service with streamable HTTP MCP support
- **`playwright-mcp`** - Microsoft's Playwright MCP server (git submodule)

### **Technology Stack**
- **Frontend**: Next.js 15, TypeScript, Tailwind CSS, Nx
- **Backend**: 
  - Python FastAPI, Pydantic AI, uvicorn
  - Java Spring Boot, Spring AI MCP Client, Gradle
- **Browser Automation**: Playwright MCP Server
- **Database**: PostgreSQL (via Docker)
- **Authentication**: JWT tokens, Better Auth
- **Monorepo**: Nx with TypeScript, Python, and Java support

## Quick Start

### Prerequisites
- Node.js 18+
- Python 3.9+
- Java 21+ (for Java MCP Gateway)
- Docker (for PostgreSQL)
- pnpm (package manager)

### Setup

1. **Clone and install dependencies**
   ```bash
   git clone <repository-url>
   cd mcp-chat-workspace
   pnpm install
   ```

2. **Initialize git submodules**
   ```bash
   git submodule update --init --recursive
   ```

3. **Start PostgreSQL database**
   ```bash
   docker run --name mcp-pg \
     -e POSTGRES_PASSWORD=mcp_password \
     -e POSTGRES_USER=mcp_user \
     -e POSTGRES_DB=mcp_chat_db \
     -p 5432:5432 -d postgres
   ```

4. **Set up database schema**
   ```bash
   npx nx run mcp-chat-app:db:push
   ```

### Development

**Option 1: Start all services at once (Python Gateway)**
```bash
# Start all services simultaneously
npx nx run-many --target=serve --projects=mcp-chat-app,mcp-gateway,playwright-mcp --parallel
```

**Option 2: Start all services at once (Java Gateway)**
```bash
# Start all services simultaneously with Java gateway
npx nx run-many --target=serve --projects=mcp-chat-app,mcp-gateway-java,playwright-mcp --parallel
```

**Option 3: Start services in separate terminals**
```bash
# Terminal 1: Next.js App
npx nx serve mcp-chat-app

# Terminal 2: MCP Gateway (choose one)
npx nx serve mcp-gateway          # Python gateway (port 8000)
npx nx serve mcp-gateway-java     # Java gateway (port 8002)

# Terminal 3: Playwright MCP Server
npx nx serve playwright-mcp
```

### Access Points

- **Frontend**: http://localhost:4200
- **MCP Gateway API**: 
  - Python: http://localhost:8000
  - Java: http://localhost:8002
- **Playwright MCP Server**: http://localhost:8001

### Test Endpoints

After starting all services, you can test the connections:

```bash
# Test MCP Gateway health (choose one)
curl http://localhost:8000/health      # Python gateway
curl http://localhost:8002/api/health  # Java gateway

# Test Playwright MCP Server connectivity (choose one)
curl http://localhost:8000/test/playwright      # Python gateway
curl http://localhost:8002/api/test/playwright  # Java gateway

# Test actual MCP protocol communication (choose one)
curl -X POST http://localhost:8000/test/mcp      # Python gateway
curl -X POST http://localhost:8002/api/test/mcp  # Java gateway

# Test authenticated MCP query (using mock token in development)
# Python gateway:
curl -X POST http://localhost:8000/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "prompt": "What browser automation tools are available?",
    "server_url": "http://localhost:8001/mcp",
    "model_name": "openai:gpt-4.1"
  }'

# Java gateway:
curl -X POST http://localhost:8002/api/mcp/query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer mock-token" \
  -d '{
    "prompt": "What browser automation tools are available?",
    "serverUrl": "http://localhost:8001/mcp",
    "modelName": "openai:gpt-4.1"
  }'
```

**Expected responses:**
- `/health` → `{"status": "healthy", "service": "mcp-gateway"}`
- `/test/playwright` → Connection status with SSE stream confirmation
- `/test/mcp` → MCP protocol test results
- `/mcp/query` → Authenticated MCP query response

## Configuration

### Environment Variables

**Next.js App** (`apps/mcp-chat-app/.env`):
- Database connection (PostgreSQL)
- LLM provider API keys (OpenAI, Anthropic, etc.)
- Authentication secrets

**MCP Gateway** (`apps/mcp-gateway/.env`):
- JWT authentication configuration
- LLM provider API keys  
- MCP server endpoints

## Available Commands

### Workspace Level
```bash
# Development - Start all services (Python gateway)
npx nx run-many --target=serve --projects=mcp-chat-app,mcp-gateway,playwright-mcp --parallel

# Development - Start all services (Java gateway)
npx nx run-many --target=serve --projects=mcp-chat-app,mcp-gateway-java,playwright-mcp --parallel

# Development - Individual services
npx nx serve mcp-chat-app        # Start Next.js app
npx nx serve mcp-gateway         # Start Python MCP gateway
npx nx serve mcp-gateway-java    # Start Java MCP gateway
npx nx serve playwright-mcp      # Start Playwright MCP server

# Testing & Quality
npx nx run-many --target=test    # Run all tests
npx nx run-many --target=lint    # Lint all projects
npx nx run-many --target=format  # Format all projects (where available)
npx nx affected --target=test    # Run tests for affected projects only

# Building
npx nx run-many --target=build   # Build all projects
npx nx build mcp-chat-app        # Build Next.js app
npx nx build playwright-mcp      # Build Playwright MCP server
```

### Project Specific
```bash
# Next.js App
npx nx serve mcp-chat-app              # Start dev server
npx nx build mcp-chat-app              # Build for production
npx nx test mcp-chat-app               # Run tests
npx nx run mcp-chat-app:db:push        # Push database schema

# MCP Gateway (Python)
npx nx serve mcp-gateway               # Start FastAPI server
npx nx test mcp-gateway                # Run Python tests
npx nx run mcp-gateway:sync            # Install Python dependencies

# MCP Gateway (Java)
npx nx serve mcp-gateway-java          # Start Spring Boot server
npx nx test mcp-gateway-java           # Run Java tests
npx nx build mcp-gateway-java          # Build JAR file

# Playwright MCP
npx nx serve playwright-mcp            # Start MCP server
npx nx build playwright-mcp            # Build TypeScript
npx nx test playwright-mcp             # Run Playwright tests
```

## Development Workflow

1. **Start the database** (Docker PostgreSQL)
2. **Start all services**: `npx nx run-many --target=serve --projects=mcp-chat-app,mcp-gateway,playwright-mcp --parallel`
3. **Test the connections** using the test endpoints above
4. **Access the frontend** at http://localhost:4200
5. **Authenticate** with JWT tokens (mock tokens in development)
6. **Connect to MCP servers** through the gateway
7. **Use browser automation** via Playwright MCP tools

### Pro Tips
- Use `npx nx affected --target=test` to only test changed projects
- Use `npx nx graph` to visualize project dependencies
- Use `npx nx reset` to clear Nx cache if needed
- Use the test endpoints to verify all services are communicating properly

## MCP Integration

The architecture provides:

- **Authenticated Access**: All MCP calls go through the gateway with JWT auth
- **User Isolation**: Each user gets isolated MCP client sessions
- **Browser Automation**: Full Playwright capabilities via MCP protocol
- **Extensible**: Easy to add more MCP servers as git submodules

## Git Submodules

This monorepo uses git submodules for external MCP servers:

```bash
# Update submodules
git submodule update --remote

# Add new MCP server submodule
git submodule add <repo-url> apps/<server-name>
```

## Project Structure

```
mcp-chat-workspace/
├── apps/
│   ├── mcp-chat-app/          # Next.js frontend
│   ├── mcp-gateway/           # Python MCP gateway
│   └── playwright-mcp/        # Playwright MCP server (submodule)
├── docs/                      # Documentation
├── docker/                    # Docker configurations
├── nx.json                    # Nx workspace configuration
├── package.json               # Workspace dependencies
└── tsconfig.base.json         # Base TypeScript config
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see individual project licenses for details.