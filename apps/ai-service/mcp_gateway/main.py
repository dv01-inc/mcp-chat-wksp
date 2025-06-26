"""AI Service - Comprehensive AI backend with intelligent MCP orchestration.

This service provides a complete AI backend that handles LLM communication,
database management, and intelligent routing to specialized MCP servers.
It eliminates the need for clients to understand AI/ML protocols.

Key Features:
- 🧠 Intelligent MCP server selection based on natural language analysis
- 🤖 Direct LLM integration (OpenAI, Anthropic) for AI processing
- 💾 PostgreSQL database for persistent chat history and user management
- 🔐 JWT authentication with development mock mode
- 📱 Complete REST API for chat, threads, and message management
- 🐳 Containerized deployment with Docker Compose

Architecture:
    Client → AI Service → LLMs (OpenAI/Anthropic)
                      → MCP Servers (Playwright, Apollo, etc.)
                      → PostgreSQL Database

The service automatically analyzes user prompts, processes them with appropriate
LLMs and tools, and returns intelligent natural language responses.
"""

from fastapi import FastAPI, HTTPException, Depends, Security, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .mcp_client import MCPClient
from .auth import verify_token, KongAuth
from .database import get_db, ChatRepository, UserRepository, MCPServerRepository, create_tables, SessionLocal
from .mcp_manager import get_mcp_manager, initialize_default_servers

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(load_env_path):
    load_dotenv(load_env_path)

app = FastAPI(
    title="AI Service",
    description="Intelligent AI service with MCP orchestration, database management, and LLM integration",
    version="1.0.0"
)

# Global MCP manager instance
mcp_manager = None

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    global mcp_manager
    import time
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            create_tables()
            print("✅ Database tables created successfully")
            
            # Initialize MCP manager
            mcp_manager = get_mcp_manager(SessionLocal)
            await mcp_manager.initialize()
            await initialize_default_servers(mcp_manager)
            print("✅ MCP manager initialized successfully")
            
            # Create mock user for development
            if os.getenv("ENVIRONMENT") == "development":
                from sqlalchemy.orm import Session
                from .database import SessionLocal, UserRepository
                db = SessionLocal()
                try:
                    user_repo = UserRepository(db)
                    mock_user_id = "550e8400-e29b-41d4-a716-446655440000"
                    existing_user = user_repo.get_user_by_id(mock_user_id)
                    if not existing_user:
                        user_repo.create_user(
                            name="Mock User",
                            email="mock@example.com",
                            id=mock_user_id
                        )
                        print("✅ Mock user created for development")
                finally:
                    db.close()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"⏳ Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
                print(f"   Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print(f"❌ Failed to connect to database after {max_retries} attempts: {e}")
                raise

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

# Flexible authentication for both JWT and Kong
def get_user_info(request: Request, credentials: Optional[HTTPAuthorizationCredentials] = Security(security, auto_error=False)) -> Dict[str, Any]:
    """Get user information from either Kong headers or JWT token."""
    
    # Check if we're using Kong authentication
    if os.getenv("USE_KONG_AUTH") == "true":
        headers = dict(request.headers)
        user_info = KongAuth.extract_user_from_headers(headers)
        if user_info:
            return user_info
        else:
            raise HTTPException(status_code=401, detail="No user information in Kong headers")
    
    # Fallback to JWT authentication
    if not credentials:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    return verify_token(credentials.credentials)

# Legacy global MCP client instances - will be managed by DynamicMCPManager
mcp_clients: Dict[str, MCPClient] = {}


def select_server_for_prompt(prompt: str) -> Optional[str]:
    """Intelligently select the best MCP server based on the prompt content.
    
    This function analyzes the user's natural language prompt and automatically
    determines which MCP server is best suited to handle the request.
    
    Args:
        prompt: Natural language prompt from the user
        
    Returns:
        Server ID of the best matching server, or None if no servers available
    """
    global mcp_manager
    if not mcp_manager:
        return None
    
    return mcp_manager.select_server_for_prompt(prompt)


def get_server_url(server_id: str) -> Optional[str]:
    """Get the URL for a given server ID."""
    global mcp_manager
    if not mcp_manager:
        return None
    
    return mcp_manager.get_server_url(server_id)


class MCPRequest(BaseModel):
    """Request model for MCP operations."""
    prompt: str
    model_name: Optional[str] = "openai:gpt-4.1"
    system_prompt: Optional[str] = None
    thread_id: Optional[str] = None
    message_id: Optional[str] = None
    # Removed server_url - gateway will intelligently select servers


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


class MCPToolRequest(BaseModel):
    """Request model for MCP tool execution."""
    server_id: str  # e.g., "playwright", "apollo"
    tool_name: str  # e.g., "browser_navigate", "get_astronaut_details"
    parameters: Optional[Dict[str, Any]] = None
    model_name: Optional[str] = "openai:gpt-4.1"


@app.get("/")
async def root():
    """Root endpoint with service information.
    
    Returns basic information about the AI Service.
    Used for health checks and service discovery.
    """
    return {
        "message": "AI Service is running",
        "service": "ai-service",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "chat": "/mcp/chat",
            "servers": "/mcp/servers",
            "tools": "/mcp/tools",
            "create_server": "POST /mcp/servers",
            "update_server": "PUT /mcp/servers/{id}",
            "delete_server": "DELETE /mcp/servers/config/{id}",
            "threads": "/chat/threads"
        }
    }


@app.get("/health")
async def health():
    """Detailed health check endpoint.
    
    Returns the current health status of the AI service.
    Used by Docker health checks and monitoring systems.
    """
    global mcp_manager
    servers_info = "not_initialized"
    if mcp_manager:
        enabled_servers = mcp_manager.get_enabled_servers()
        servers_info = {
            "total": len(mcp_manager.get_all_servers()),
            "enabled": len(enabled_servers),
            "names": [info.get("name", "unknown") for info in enabled_servers.values()]
        }
    
    return {
        "status": "healthy", 
        "service": "ai-service",
        "timestamp": "2025-06-26T00:00:00Z",
        "database": "connected",
        "mcp_manager": "initialized" if mcp_manager else "not_initialized",
        "servers": servers_info
    }


@app.get("/test/apollo")
async def test_apollo_connection():
    """Test connection to Apollo MCP server."""
    try:
        import httpx
        
        # Test the /mcp endpoint 
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:5001/mcp", timeout=5.0)
            
            # Also test basic connectivity
            try:
                health_response = await client.get("http://localhost:5001", timeout=2.0, follow_redirects=False)
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


@app.post("/test/apollo-mcp")
async def test_apollo_mcp_query():
    """Test actual MCP query to Apollo server."""
    try:
        # Test if we can create an MCP client and run a simple query
        from .mcp_client import MCPClient
        import traceback
        
        client = MCPClient(
            model_name="openai:gpt-4.1",
            mcp_server_url="http://localhost:5001/mcp"
        )
        
        # Try a simple query
        result = await client.run("List available tools for space data")
        
        return {
            "status": "success",
            "message": "Apollo MCP query successful",
            "result_preview": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
        }
        
    except Exception as e:
        # Get full traceback for debugging
        tb = traceback.format_exc()
        return {
            "status": "error",
            "message": "Apollo MCP query failed",
            "error": str(e),
            "traceback": tb[-1000:] if len(tb) > 1000 else tb  # Last 1000 chars
        }


@app.post("/mcp/query", response_model=MCPResponse)
async def intelligent_mcp_query(
    mcp_request: MCPRequest,
    request: Request
):
    """Execute an intelligent MCP query - automatically selects best server."""
    try:
        # Get user info from Kong headers or JWT token
        user_info = get_user_info(request)
        
        # 🧠 INTELLIGENT SERVER SELECTION
        selected_server_id = select_server_for_prompt(mcp_request.prompt)
        server_url = get_server_url(selected_server_id)
        
        print(f"🧠 Intelligent routing: '{mcp_request.prompt}' → {selected_server_id} server")
        
        # Create MCP client key based on selected server
        client_key = f"{server_url}:{user_info.get('sub', 'anonymous')}"
        
        # Get or create MCP client for the selected server
        if client_key not in mcp_clients:
            mcp_clients[client_key] = MCPClient(
                model_name=mcp_request.model_name,
                mcp_server_url=server_url,
                system_prompt=mcp_request.system_prompt
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers
        headers = {
            "X-User-ID": user_info.get("sub", "anonymous"),
            "X-User-Email": user_info.get("email", ""),
            "X-Selected-Server": selected_server_id,
        }
        
        # Execute the query
        result = await client.run(mcp_request.prompt, headers=headers)
        
        usage_info = None
        if hasattr(result, 'usage'):
            try:
                usage_obj = result.usage()
                usage_info = {
                    "requests": usage_obj.requests if hasattr(usage_obj, 'requests') else None,
                    "total_tokens": usage_obj.total_tokens if hasattr(usage_obj, 'total_tokens') else None,
                    "selected_server": selected_server_id,
                }
            except:
                usage_info = {"selected_server": selected_server_id}
        
        return MCPResponse(
            result=str(result),
            usage=usage_info,
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP query failed: {str(e)}")


@app.post("/mcp/chat", response_model=MCPResponse)
async def intelligent_mcp_chat(
    mcp_request: MCPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Execute an intelligent MCP chat - automatically selects best server and tools."""
    try:
        # Get user info from Kong headers or JWT token
        user_info = get_user_info(request)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user information")
        
        # 🧠 INTELLIGENT SERVER SELECTION
        # AI Service analyzes the prompt and selects the best server automatically
        selected_server_id = select_server_for_prompt(mcp_request.prompt)
        
        if not selected_server_id:
            raise HTTPException(status_code=503, detail="No MCP servers available")
        
        server_url = get_server_url(selected_server_id)
        if not server_url:
            raise HTTPException(status_code=404, detail=f"Server {selected_server_id} not found")
        
        print(f"🧠 Intelligent routing: '{mcp_request.prompt}' → {selected_server_id} server")
        
        # Initialize chat repository
        chat_repo = ChatRepository(db)
        
        # Handle thread creation/retrieval if thread_id provided
        thread_id = mcp_request.thread_id
        if thread_id:
            # Verify thread exists and belongs to user
            thread = chat_repo.get_thread(thread_id, user_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
        
        # Save user message if message_id provided
        if mcp_request.message_id and thread_id:
            chat_repo.upsert_message(
                thread_id=thread_id,
                message_id=mcp_request.message_id,
                role="user",
                parts=[{"type": "text", "text": mcp_request.prompt}],
                attachments=[],
                annotations=[]
            )
        
        # Get server info for enhanced system prompt
        global mcp_manager
        server_info = mcp_manager.get_server(selected_server_id) if mcp_manager else {}
        server_capabilities = server_info.get("capabilities", [])
        
        # Enhanced system prompt for intelligent behavior
        enhanced_system_prompt = (
            "You are an intelligent assistant with access to specialized tools. "
            "Always use the available tools when they can help fulfill the user's request. "
            "For browser tasks: navigate, take screenshots, interact with elements as needed. "
            "For space queries: fetch real astronaut data, mission info, or celestial details. "
            "Provide clear, helpful responses based on the tool results. "
            f"Current capabilities: {server_capabilities}"
        )
        
        # Get or create MCP client for the selected server using the manager
        if mcp_manager:
            client = await mcp_manager.get_or_create_client(
                selected_server_id, 
                user_id, 
                mcp_request.model_name,
                mcp_request.system_prompt or enhanced_system_prompt
            )
        else:
            # Fallback to legacy client management
            client_key = f"{server_url}:{user_id}"
            if client_key not in mcp_clients:
                mcp_clients[client_key] = MCPClient(
                    model_name=mcp_request.model_name,
                    mcp_server_url=server_url,
                    system_prompt=mcp_request.system_prompt or enhanced_system_prompt
                )
            client = mcp_clients[client_key]
        
        if not client:
            raise HTTPException(status_code=503, detail=f"Unable to connect to server {selected_server_id}")
        
        # Set authentication headers
        headers = {
            "X-User-ID": user_id,
            "X-User-Email": user_info.get("email", ""),
            "X-Selected-Server": selected_server_id,
        }
        
        # Execute the intelligent chat
        result = await client.chat(mcp_request.prompt, headers=headers)
        
        # Extract usage information
        usage_info = None
        if hasattr(result, 'usage'):
            try:
                usage_obj = result.usage()
                usage_info = {
                    "prompt_tokens": usage_obj.total_tokens - (usage_obj.response_tokens or 0) if hasattr(usage_obj, 'total_tokens') else None,
                    "completion_tokens": usage_obj.response_tokens if hasattr(usage_obj, 'response_tokens') else None,
                    "total_tokens": usage_obj.total_tokens if hasattr(usage_obj, 'total_tokens') else None,
                    "selected_server": selected_server_id,
                    "server_capabilities": server_capabilities
                }
            except:
                usage_info = {"selected_server": selected_server_id}
        
        # Save assistant message if thread_id provided
        assistant_message_id = None
        if thread_id:
            import time
            assistant_message_id = f"assistant-{int(time.time() * 1000)}"
            chat_repo.upsert_message(
                thread_id=thread_id,
                message_id=assistant_message_id,
                role="assistant",
                parts=[{"type": "text", "text": str(result)}],
                attachments=[],
                annotations=[{
                    "type": "gateway-response",
                    "selected_server": selected_server_id,
                    "usage": usage_info
                }],
                model=mcp_request.model_name
            )
        
        response_data = {
            "result": str(result),
            "usage": usage_info,
            "error": None
        }
        
        # Include message IDs in response if thread_id was provided
        if thread_id:
            response_data["thread_id"] = thread_id
            response_data["assistant_message_id"] = assistant_message_id
        
        return MCPResponse(**response_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MCP chat failed: {str(e)}")


@app.get("/mcp/servers")
async def list_mcp_servers(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """List available MCP servers and their capabilities."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub", "anonymous")
        
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager not initialized")
        
        # Get all servers from dynamic manager
        all_servers = mcp_manager.get_all_servers()
        available_servers = []
        
        for server_id, server_info in all_servers.items():
            server_data = {
                "id": server_id,
                "name": server_info.get("name", "Unknown"),
                "description": server_info.get("description", ""),
                "server_url": server_info.get("url", ""),
                "status": "available" if server_info.get("enabled", True) else "disabled",
                "transport": server_info.get("transport", "http"),
                "capabilities": server_info.get("capabilities", []),
                "tools": server_info.get("tools", []),
                "keywords": server_info.get("keywords", []),
                "enabled": server_info.get("enabled", True)
            }
            available_servers.append(server_data)
        
        # Check which servers have active client connections
        active_sessions = 0
        for client_key in mcp_clients:
            if client_key.endswith(f":{user_id}"):
                active_sessions += 1
        
        return {
            "servers": available_servers,
            "user_id": user_id,
            "active_sessions": active_sessions,
            "total_servers": len(available_servers),
            "enabled_servers": len([s for s in available_servers if s["enabled"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list servers: {str(e)}")


@app.post("/mcp/tools/execute", response_model=MCPResponse)
async def execute_mcp_tool(
    request: MCPToolRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute a specific tool on an MCP server."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        # Map server IDs to URLs
        server_mapping = {
            "playwright": "http://localhost:8001/sse",
            "apollo": "http://localhost:5001/mcp"
        }
        
        server_url = server_mapping.get(request.server_id)
        if not server_url:
            raise HTTPException(status_code=400, detail=f"Unknown server ID: {request.server_id}")
        
        # Build tool execution prompt
        if request.parameters:
            param_str = ", ".join([f"{k}: {v}" for k, v in request.parameters.items()])
            prompt = f"Execute the {request.tool_name} tool with parameters: {param_str}"
        else:
            prompt = f"Execute the {request.tool_name} tool"
        
        # Create MCP client key
        client_key = f"{server_url}:{user_info.get('sub', 'anonymous')}"
        
        # Get or create MCP client
        if client_key not in mcp_clients:
            mcp_clients[client_key] = MCPClient(
                model_name=request.model_name,
                mcp_server_url=server_url,
                system_prompt=f"You are a tool executor. Use the {request.tool_name} tool to fulfill the request."
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers
        headers = {
            "X-User-ID": user_info.get("sub", "anonymous"),
            "X-User-Email": user_info.get("email", ""),
            "X-Tool-Name": request.tool_name,
            "X-Server-ID": request.server_id
        }
        
        # Execute the tool
        result = await client.run(prompt, headers=headers)
        
        usage_info = None
        if hasattr(result, 'usage'):
            try:
                usage_obj = result.usage()
                usage_info = {
                    "requests": usage_obj.requests if hasattr(usage_obj, 'requests') else None,
                    "total_tokens": usage_obj.total_tokens if hasattr(usage_obj, 'total_tokens') else None,
                    "server_id": request.server_id,
                    "tool_name": request.tool_name
                }
            except:
                usage_info = None
        
        return MCPResponse(
            result=str(result),
            usage=usage_info,
            error=None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {str(e)}")


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
        
        global mcp_manager
        if mcp_manager:
            await mcp_manager.disconnect_client(server_id, user_id)
        
        # Also clean up legacy clients
        client_key = f"{server_id}:{user_id}"
        if client_key in mcp_clients:
            del mcp_clients[client_key]
        
        return {"message": f"Disconnected from server {server_id}"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


# New Dynamic MCP Server Management Endpoints

class MCPServerCreateRequest(BaseModel):
    """Request model for creating an MCP server."""
    name: str
    url: str
    transport: Optional[str] = "http"
    description: Optional[str] = ""
    capabilities: Optional[List[str]] = []
    keywords: Optional[List[str]] = []
    tools: Optional[List[str]] = []
    auth: Optional[Dict[str, str]] = None


class MCPServerUpdateRequest(BaseModel):
    """Request model for updating an MCP server."""
    name: Optional[str] = None
    url: Optional[str] = None
    transport: Optional[str] = None
    description: Optional[str] = None
    capabilities: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    tools: Optional[List[str]] = None
    enabled: Optional[bool] = None
    auth: Optional[Dict[str, str]] = None


@app.post("/mcp/servers")
async def create_mcp_server(
    request: MCPServerCreateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Create a new MCP server configuration."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager not initialized")
        
        # Build config object
        config = {
            "url": request.url,
            "transport": request.transport,
            "description": request.description,
            "capabilities": request.capabilities,
            "keywords": request.keywords,
            "tools": request.tools
        }
        
        if request.auth:
            config["auth"] = request.auth
        
        # Add server
        server_id = await mcp_manager.add_server(request.name, config)
        
        return {
            "id": server_id,
            "name": request.name,
            "message": f"MCP server '{request.name}' created successfully",
            "config": config
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create server: {str(e)}")


@app.put("/mcp/servers/{server_id}")
async def update_mcp_server(
    server_id: str,
    request: MCPServerUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Update an MCP server configuration."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager not initialized")
        
        # Build updates
        updates = {}
        
        # Handle individual field updates
        if request.name is not None:
            updates["name"] = request.name
        if request.enabled is not None:
            updates["enabled"] = request.enabled
        
        # Handle config updates
        config_updates = {}
        if request.url is not None:
            config_updates["url"] = request.url
        if request.transport is not None:
            config_updates["transport"] = request.transport
        if request.description is not None:
            config_updates["description"] = request.description
        if request.capabilities is not None:
            config_updates["capabilities"] = request.capabilities
        if request.keywords is not None:
            config_updates["keywords"] = request.keywords
        if request.tools is not None:
            config_updates["tools"] = request.tools
        if request.auth is not None:
            config_updates["auth"] = request.auth
        
        # Get current config and merge updates
        if config_updates:
            server_info = mcp_manager.get_server(server_id)
            if not server_info:
                raise HTTPException(status_code=404, detail="Server not found")
            
            current_config = server_info.get("config", {})
            new_config = {**current_config, **config_updates}
            updates["config"] = new_config
        
        # Update server
        success = await mcp_manager.update_server(server_id, **updates)
        
        if not success:
            raise HTTPException(status_code=404, detail="Server not found")
        
        return {
            "id": server_id,
            "message": "MCP server updated successfully",
            "updates": updates
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update server: {str(e)}")


@app.delete("/mcp/servers/config/{server_id}")
async def delete_mcp_server(
    server_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Delete an MCP server configuration."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager not initialized")
        
        # Remove server
        success = await mcp_manager.remove_server(server_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Server not found")
        
        return {"message": f"MCP server {server_id} deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete server: {str(e)}")


@app.get("/mcp/tools")
async def list_mcp_tools(
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """List all available tools from all MCP servers."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        global mcp_manager
        if not mcp_manager:
            raise HTTPException(status_code=500, detail="MCP manager not initialized")
        
        tools = mcp_manager.get_available_tools()
        
        return {
            "tools": tools,
            "total_tools": len(tools)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list tools: {str(e)}")


# Chat History Management Endpoints

class ThreadCreateRequest(BaseModel):
    """Request model for creating a chat thread."""
    title: str
    project_id: Optional[str] = None
    thread_id: Optional[str] = None


class ThreadUpdateRequest(BaseModel):
    """Request model for updating a chat thread."""
    title: Optional[str] = None
    project_id: Optional[str] = None


class MessageRequest(BaseModel):
    """Request model for adding a message."""
    message_id: str
    role: str
    parts: List[Any]
    attachments: Optional[List[Any]] = None
    annotations: Optional[List[Any]] = None
    model: Optional[str] = None


@app.get("/chat/threads")
async def get_user_threads(
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Get all chat threads for the authenticated user."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        chat_repo = ChatRepository(db)
        threads = chat_repo.get_user_threads(user_id)
        
        return {"threads": threads}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get threads: {str(e)}")


@app.post("/chat/threads")
async def create_thread(
    request: ThreadCreateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Create a new chat thread."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        chat_repo = ChatRepository(db)
        thread = chat_repo.create_thread(
            user_id=user_id,
            title=request.title,
            project_id=request.project_id,
            thread_id=request.thread_id
        )
        
        return {
            "id": str(thread.id),
            "title": thread.title,
            "user_id": str(thread.user_id),
            "project_id": str(thread.project_id) if thread.project_id else None,
            "created_at": thread.created_at.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create thread: {str(e)}")


@app.get("/chat/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Get a specific chat thread with its messages."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        chat_repo = ChatRepository(db)
        thread_data = chat_repo.get_thread_with_messages(thread_id, user_id)
        
        if not thread_data:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return thread_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get thread: {str(e)}")


@app.put("/chat/threads/{thread_id}")
async def update_thread(
    thread_id: str,
    request: ThreadUpdateRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Update a chat thread."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        chat_repo = ChatRepository(db)
        
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.project_id is not None:
            updates["project_id"] = request.project_id
        
        thread = chat_repo.update_thread(thread_id, user_id, **updates)
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {
            "id": str(thread.id),
            "title": thread.title,
            "user_id": str(thread.user_id),
            "project_id": str(thread.project_id) if thread.project_id else None,
            "created_at": thread.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update thread: {str(e)}")


@app.delete("/chat/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Delete a chat thread and all its messages."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        chat_repo = ChatRepository(db)
        success = chat_repo.delete_thread(thread_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        return {"message": "Thread deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete thread: {str(e)}")


@app.post("/chat/threads/{thread_id}/messages")
async def add_message(
    thread_id: str,
    request: MessageRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Add a message to a chat thread."""
    try:
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # Verify the user owns the thread
        chat_repo = ChatRepository(db)
        thread = chat_repo.get_thread(thread_id, user_id)
        
        if not thread:
            raise HTTPException(status_code=404, detail="Thread not found")
        
        message = chat_repo.upsert_message(
            thread_id=thread_id,
            message_id=request.message_id,
            role=request.role,
            parts=request.parts,
            attachments=request.attachments,
            annotations=request.annotations,
            model=request.model
        )
        
        return {
            "id": message.id,
            "thread_id": str(message.thread_id),
            "role": message.role,
            "parts": message.parts,
            "attachments": message.attachments,
            "annotations": message.annotations,
            "model": message.model,
            "created_at": message.created_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add message: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)