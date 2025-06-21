# MCP Gateway Service

A FastAPI-based gateway service for authenticated Model Context Protocol (MCP) calls.

## Features

- **Authentication**: JWT-based authentication for secure MCP calls
- **Multiple MCP Servers**: Support for connecting to multiple MCP servers
- **User Isolation**: Each user has their own MCP client instances
- **Streaming Support**: Support for streaming responses from MCP servers
- **Chat History**: Persistent chat history per user and server
- **CORS Support**: Configured for Next.js frontend integration

## API Endpoints

- `GET /` - Health check
- `GET /health` - Service health status
- `POST /mcp/query` - Execute MCP query
- `POST /mcp/chat` - Execute MCP chat with history
- `GET /mcp/servers` - List connected servers
- `DELETE /mcp/servers/{server_id}` - Disconnect from server

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

## Usage

The gateway acts as a proxy between your Next.js app and MCP servers, handling authentication and user isolation.

1. Authenticate with JWT token
2. Send MCP requests to the gateway
3. Gateway forwards requests to MCP servers with user context
4. Responses are returned to the client