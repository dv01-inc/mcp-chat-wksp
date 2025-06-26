# Chat API Service

Standalone Express.js API service extracted from the Next.js chat application, with Nx integration and Docker containerization.

## Features

- 🚀 **Express.js** REST API server
- 🐳 **Docker** containerization with @nx-tools/nx-container
- 🔐 **Authentication** middleware (placeholder implementation)
- 📊 **Health checks** and monitoring
- 🧪 **TypeScript** support
- 🔧 **Nx** workspace integration

## API Endpoints

### Core Endpoints
- `GET /health` - Health check
- `POST /api/auth/*` - Authentication endpoints
- `POST /api/chat` - Chat operations
- `GET|POST /api/mcp/*` - MCP server management
- `GET|POST|PUT|DELETE /api/thread/*` - Thread management
- `GET|POST /api/user/*` - User operations

### Authentication
All API endpoints (except `/health` and `/api/auth/*`) require authentication via Bearer token.

Example:
```bash
curl -H "Authorization: Bearer mock-token" http://localhost:3001/api/chat
```

## Development

### Prerequisites
- Node.js 18+
- pnpm

### Commands

```bash
# Development
npx nx dev chat-api              # Start development server
npx nx build chat-api            # Build for production
npx nx start chat-api            # Start production server

# Testing
npx nx test chat-api             # Run tests
npx nx lint chat-api             # Lint code
npx nx typecheck chat-api        # Type checking

# Docker
npx nx container chat-api        # Build container
docker-compose up                # Start with dependencies
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
# Server
PORT=3001
NODE_ENV=development

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/chatdb

# CORS
CORS_ORIGIN=http://localhost:3000,http://localhost:4200

# Authentication
JWT_SECRET=your-secret-key

# AI Models
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## Container Usage

### Build and Run
```bash
# Using Nx
npx nx container chat-api

# Using Docker Compose
docker-compose up -d
```

### Health Check
The container includes health checks:
```bash
curl http://localhost:3001/health
```

## Architecture

```
src/
├── main.ts              # Express server entry point
├── config/              # Configuration
├── middleware/          # Auth, error handling
├── routes/              # API route handlers
└── types/               # TypeScript definitions
```

## Migration Notes

This service was extracted from `/apps/chat/src/app/api` with the following changes:

1. **Framework**: Next.js API routes → Express.js routes
2. **Authentication**: Next.js sessions → JWT middleware
3. **Error Handling**: Next.js → Express error middleware
4. **Dependencies**: Removed Next.js specific imports
5. **Structure**: Reorganized for standalone service

## Next Steps

To complete the migration:

1. **Implement proper authentication** (replace mock auth)
2. **Add database integration** (Drizzle ORM setup)
3. **Implement MCP client manager** (port from original app)
4. **Add comprehensive tests**
5. **Set up CI/CD** for container builds
6. **Configure production deployment**

## Integration

Update the chat frontend to consume this API:

```typescript
// Replace internal API calls with HTTP requests
const response = await fetch('http://localhost:3001/api/chat', {
  method: 'POST',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  },
  body: JSON.stringify(chatData)
});
```