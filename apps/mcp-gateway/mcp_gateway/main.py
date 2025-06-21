"""MCP Gateway Service - FastAPI application for authenticated MCP calls."""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import os
from dotenv import load_dotenv

from .mcp_client import MCPClient
from .auth import verify_token

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(load_env_path):
    load_dotenv(load_env_path)

app = FastAPI(
    title="MCP Gateway Service",
    description="Gateway service for authenticated MCP calls",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global MCP client instances
mcp_clients: Dict[str, MCPClient] = {}


class MCPRequest(BaseModel):
    """Request model for MCP operations."""
    prompt: str
    server_url: str
    server_auth: Optional[Dict[str, str]] = None
    model_name: Optional[str] = "openai:gpt-4.1"
    system_prompt: Optional[str] = None


class MCPResponse(BaseModel):
    """Response model for MCP operations."""
    result: str
    usage: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class MCPStreamRequest(BaseModel):
    """Request model for MCP streaming operations."""
    prompt: str
    server_url: str
    server_auth: Optional[Dict[str, str]] = None
    model_name: Optional[str] = "openai:gpt-4.1"
    system_prompt: Optional[str] = None


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"message": "MCP Gateway Service is running"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "mcp-gateway"}


@app.post("/mcp/query", response_model=MCPResponse)
async def mcp_query(
    request: MCPRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute an MCP query with authentication."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        # Create MCP client key
        client_key = f"{request.server_url}:{user_info.get('sub', 'anonymous')}"
        
        # Get or create MCP client
        if client_key not in mcp_clients:
            mcp_clients[client_key] = MCPClient(
                model_name=request.model_name,
                mcp_server_url=request.server_url,
                system_prompt=request.system_prompt
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers if provided
        headers = {}
        if request.server_auth:
            headers.update(request.server_auth)
        
        # Add user context to headers
        headers["X-User-ID"] = user_info.get("sub", "anonymous")
        headers["X-User-Email"] = user_info.get("email", "")
        
        # Execute the query
        result = await client.run(request.prompt, headers=headers)
        
        return MCPResponse(
            result=str(result),
            usage=getattr(result, 'usage', None),
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP query failed: {str(e)}")


@app.post("/mcp/chat", response_model=MCPResponse)
async def mcp_chat(
    request: MCPRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute an MCP chat with persistent history."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        # Create MCP client key
        client_key = f"{request.server_url}:{user_info.get('sub', 'anonymous')}"
        
        # Get or create MCP client
        if client_key not in mcp_clients:
            mcp_clients[client_key] = MCPClient(
                model_name=request.model_name,
                mcp_server_url=request.server_url,
                system_prompt=request.system_prompt
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers if provided
        headers = {}
        if request.server_auth:
            headers.update(request.server_auth)
        
        # Add user context to headers
        headers["X-User-ID"] = user_info.get("sub", "anonymous")
        headers["X-User-Email"] = user_info.get("email", "")
        
        # Execute the chat
        result = await client.chat(request.prompt, headers=headers)
        
        return MCPResponse(
            result=str(result),
            usage=getattr(result, 'usage', None),
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP chat failed: {str(e)}")


@app.get("/mcp/servers")
async def list_mcp_servers(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """List available MCP servers for the authenticated user."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        # Return list of user's MCP clients
        user_clients = []
        user_id = user_info.get("sub", "anonymous")
        
        for client_key in mcp_clients:
            if client_key.endswith(f":{user_id}"):
                server_url = client_key.split(f":{user_id}")[0]
                user_clients.append({
                    "server_url": server_url,
                    "status": "connected"
                })
        
        return {"servers": user_clients}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")


@app.delete("/mcp/servers/{server_id}")
async def disconnect_mcp_server(
    server_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Disconnect from an MCP server."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub", "anonymous")
        
        # Find and remove the client
        client_key = f"{server_id}:{user_id}"
        if client_key in mcp_clients:
            del mcp_clients[client_key]
            return {"message": f"Disconnected from server {server_id}"}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)