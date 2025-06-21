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


@app.get("/test/apollo")
async def test_apollo_connection():
    """Test connection to Apollo MCP server."""
    try:
        import httpx
        
        # Test the /mcp endpoint 
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5000/mcp", timeout=5.0)
            
            # Also test basic connectivity
            try:
                health_response = await client.get("http://localhost:5000", timeout=2.0, follow_redirects=False)
                health_status = health_response.status_code
            except Exception as health_error:
                health_status = "error"
            
        return {
            "status": "success",
            "apollo_server": "reachable",
            "mcp_endpoint_status": response.status_code,
            "mcp_response": response.text[:50] if hasattr(response, 'text') else "N/A",
            "health_endpoint_status": health_status,
            "message": "Apollo MCP server is reachable"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "apollo_server": "unreachable",
            "error": str(e),
            "message": "Failed to connect to Apollo MCP server"
        }


@app.get("/test/playwright")
async def test_playwright_connection():
    """Test connection to Playwright MCP server."""
    try:
        import httpx
        
        # Test the /mcp endpoint (should return 400 "Invalid request" but prove it's reachable)
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8001/mcp", timeout=5.0)
            
            # Also test basic connectivity
            try:
                sse_response = await client.get("http://localhost:8001", timeout=2.0, follow_redirects=False)
                sse_status = sse_response.status_code
                is_sse = "text/event-stream" in sse_response.headers.get("content-type", "")
            except Exception as sse_error:
                sse_status = "error"
                is_sse = False
            
        return {
            "status": "success",
            "playwright_server": "reachable",
            "mcp_endpoint_status": response.status_code,
            "mcp_response": response.text[:50] if hasattr(response, 'text') else "N/A",
            "sse_endpoint_status": sse_status,
            "has_sse_stream": is_sse,
            "message": "Playwright MCP server is reachable (400 on /mcp is expected without proper MCP request)"
        }
        
    except Exception as e:
        return {
            "status": "error", 
            "playwright_server": "unreachable",
            "error": str(e),
            "message": "Failed to connect to Playwright MCP server"
        }


@app.get("/test/env")
async def test_environment():
    """Test if environment variables are accessible."""
    import os
    
    openai_key = os.getenv("OPENAI_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    return {
        "openai_key_present": bool(openai_key),
        "openai_key_prefix": openai_key[:10] if openai_key else None,
        "anthropic_key_present": bool(anthropic_key),
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }


@app.post("/test/mcp")
async def test_mcp_query():
    """Test actual MCP query to Playwright server."""
    try:
        # Test if we can create an MCP client and run a simple query
        from .mcp_client import MCPClient
        import traceback
        
        client = MCPClient(
            model_name="openai:gpt-4.1",
            mcp_server_url="http://localhost:8001/sse"
        )
        
        # Try a simple query
        result = await client.run("List available tools")
        
        return {
            "status": "success",
            "message": "MCP query successful",
            "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        }
        
    except Exception as e:
        # Get full traceback for debugging
        tb = traceback.format_exc()
        return {
            "status": "error",
            "message": "MCP query failed",
            "error": str(e),
            "traceback": tb[-1000:] if len(tb) > 1000 else tb  # Last 1000 chars
        }


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
        
        usage_info = None
        if hasattr(result, 'usage'):
            try:
                usage_obj = result.usage()
                usage_info = {
                    "requests": usage_obj.requests if hasattr(usage_obj, 'requests') else None,
                    "total_tokens": usage_obj.total_tokens if hasattr(usage_obj, 'total_tokens') else None,
                }
            except:
                usage_info = None
        
        return MCPResponse(
            result=str(result),
            usage=usage_info,
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
        
        usage_info = None
        if hasattr(result, 'usage'):
            try:
                usage_obj = result.usage()
                usage_info = {
                    "requests": usage_obj.requests if hasattr(usage_obj, 'requests') else None,
                    "total_tokens": usage_obj.total_tokens if hasattr(usage_obj, 'total_tokens') else None,
                }
            except:
                usage_info = None
        
        return MCPResponse(
            result=str(result),
            usage=usage_info,
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