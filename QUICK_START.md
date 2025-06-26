# 🚀 Quick Start Guide

Get the MCP Chat Workspace running in under 5 minutes!

## One-Command Setup

```bash
git clone <your-repo-url>
cd mcp-chat-wksp
./setup.sh
```

This script will:
- ✅ Check system requirements
- ✅ Install all dependencies
- ✅ Set up environment files
- ✅ Start PostgreSQL database
- ✅ Run database migrations
- ✅ Build all projects
- ✅ Start all services

## What You Get

After setup completes, you'll have:

- **Chat API** running on http://localhost:3001
- **Chat App** running on http://localhost:3000
- **PostgreSQL** database ready for use
- **MCP integration** ready to connect to servers

## Quick Commands

```bash
# Start everything
pnpm dev:chat-stack

# Start individual services
pnpm chat-api:dev     # Backend API
pnpm chat:dev         # Frontend App

# Check health
curl http://localhost:3001/health
```

## Add Your First MCP Server

```bash
curl -X POST http://localhost:3001/api/mcp/servers \
  -H "Content-Type: application/json" \
  -d '{
    "name": "filesystem",
    "config": {
      "command": "npx",
      "args": ["@modelcontextprotocol/server-filesystem", "/tmp"]
    }
  }'
```

## Next Steps

1. **Add API Keys** - Update the `.env` files with your AI provider keys
2. **Connect MCP Servers** - Add servers via the API or UI
3. **Start Chatting** - Visit http://localhost:3000 and start a conversation

That's it! You're ready to build with MCP! 🎉