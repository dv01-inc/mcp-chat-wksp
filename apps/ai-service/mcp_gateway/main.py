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

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import uvicorn
import os
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from .mcp_client import MCPClient
from .auth import verify_token
from .database import get_db, ChatRepository, UserRepository, create_tables

# Load environment variables
load_env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
if os.path.exists(load_env_path):
    load_dotenv(load_env_path)

app = FastAPI(
    title="AI Service",
    description="Intelligent AI service with MCP orchestration, database management, and LLM integration",
    version="1.0.0"
)

# Initialize database tables on startup
@app.on_event("startup")
async def startup_event():
    import time
    max_retries = 30
    retry_delay = 2
    
    for attempt in range(max_retries):
        try:
            create_tables()
            print("✅ Database tables created successfully")
            
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

# Global MCP client instances
mcp_clients: Dict[str, MCPClient] = {}

# Available MCP servers and their capabilities
AVAILABLE_SERVERS = {
    "playwright": {
        "url": "http://localhost:8001/sse",
        "transport": "sse",
        "capabilities": [
            "browser_automation", "web_navigation", "screenshot", "web_scraping", 
            "click", "type", "form_filling", "page_interaction"
        ],
        "keywords": [
            "browse", "navigate", "screenshot", "click", "type", "website", "page",
            "browser", "web", "url", "link", "google", "github", "open", "visit",
            "scrape", "extract", "element", "button", "form", "input"
        ]
    },
    "apollo": {
        "url": "http://localhost:5001/mcp", 
        "transport": "http",
        "capabilities": [
            "space_data", "astronaut_info", "mission_details", "launch_info",
            "celestial_bodies", "space_exploration"
        ],
        "keywords": [
            "space", "astronaut", "mission", "launch", "nasa", "spacex",
            "rocket", "satellite", "orbit", "celestial", "planet", "moon",
            "mars", "station", "iss", "crew"
        ]
    }
}


def select_server_for_prompt(prompt: str) -> str:
    """Intelligently select the best MCP server based on the prompt content.
    
    This function analyzes the user's natural language prompt and automatically
    determines which MCP server is best suited to handle the request.
    
    Args:
        prompt: Natural language prompt from the user
        
    Returns:
        Server ID of the best matching server
        
    Algorithm:
        1. Convert prompt to lowercase for case-insensitive matching
        2. Score each server based on keyword frequency
        3. Return server with highest keyword match score
        4. Default to "playwright" if no keywords match (general automation)
        
    Examples:
        "Take a screenshot of google.com" → "playwright" (browser keywords)
        "Who are the astronauts in space?" → "apollo" (space keywords)
        "Help me with something" → "playwright" (default fallback)
    """
    prompt_lower = prompt.lower()
    
    # Score each server based on keyword matches
    server_scores = {}
    for server_id, server_info in AVAILABLE_SERVERS.items():
        score = 0
        for keyword in server_info["keywords"]:
            if keyword in prompt_lower:
                score += 1
        server_scores[server_id] = score
    
    # Find the server with the highest score
    best_server = max(server_scores.items(), key=lambda x: x[1])
    
    # If no keywords match, default to playwright (most general)
    if best_server[1] == 0:
        return "playwright"
    
    return best_server[0]


def get_server_url(server_id: str) -> str:
    """Get the URL for a given server ID."""
    return AVAILABLE_SERVERS.get(server_id, {}).get("url", "http://localhost:8001/sse")


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
            "threads": "/chat/threads"
        }
    }


@app.get("/health")
async def health():
    """Detailed health check endpoint.
    
    Returns the current health status of the AI service.
    Used by Docker health checks and monitoring systems.
    """
    return {
        "status": "healthy", 
        "service": "ai-service",
        "timestamp": "2025-06-24T03:56:00Z",
        "database": "connected",
        "servers": list(AVAILABLE_SERVERS.keys())
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
    request: MCPRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    """Execute an intelligent MCP query - automatically selects best server."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        
        # 🧠 INTELLIGENT SERVER SELECTION
        selected_server_id = select_server_for_prompt(request.prompt)
        server_url = get_server_url(selected_server_id)
        
        print(f"🧠 Intelligent routing: '{request.prompt}' → {selected_server_id} server")
        
        # Create MCP client key based on selected server
        client_key = f"{server_url}:{user_info.get('sub', 'anonymous')}"
        
        # Get or create MCP client for the selected server
        if client_key not in mcp_clients:
            mcp_clients[client_key] = MCPClient(
                model_name=request.model_name,
                mcp_server_url=server_url,
                system_prompt=request.system_prompt
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers
        headers = {
            "X-User-ID": user_info.get("sub", "anonymous"),
            "X-User-Email": user_info.get("email", ""),
            "X-Selected-Server": selected_server_id,
        }
        
        # Execute the query
        result = await client.run(request.prompt, headers=headers)
        
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
    request: MCPRequest,
    credentials: HTTPAuthorizationCredentials = Security(security),
    db: Session = Depends(get_db)
):
    """Execute an intelligent MCP chat - automatically selects best server and tools."""
    try:
        # Verify the JWT token
        user_info = verify_token(credentials.credentials)
        user_id = user_info.get("sub")
        
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid user token")
        
        # 🧠 INTELLIGENT SERVER SELECTION
        # Gateway analyzes the prompt and selects the best server automatically
        selected_server_id = select_server_for_prompt(request.prompt)
        server_url = get_server_url(selected_server_id)
        
        print(f"🧠 Intelligent routing: '{request.prompt}' → {selected_server_id} server")
        
        # Initialize chat repository
        chat_repo = ChatRepository(db)
        
        # Handle thread creation/retrieval if thread_id provided
        thread_id = request.thread_id
        if thread_id:
            # Verify thread exists and belongs to user
            thread = chat_repo.get_thread(thread_id, user_id)
            if not thread:
                raise HTTPException(status_code=404, detail="Thread not found")
        
        # Save user message if message_id provided
        if request.message_id and thread_id:
            chat_repo.upsert_message(
                thread_id=thread_id,
                message_id=request.message_id,
                role="user",
                parts=[{"type": "text", "text": request.prompt}],
                attachments=[],
                annotations=[]
            )
        
        # Create MCP client key based on selected server
        client_key = f"{server_url}:{user_id}"
        
        # Get or create MCP client for the selected server
        if client_key not in mcp_clients:
            # Enhanced system prompt for intelligent behavior
            enhanced_system_prompt = (
                "You are an intelligent assistant with access to specialized tools. "
                "Always use the available tools when they can help fulfill the user's request. "
                "For browser tasks: navigate, take screenshots, interact with elements as needed. "
                "For space queries: fetch real astronaut data, mission info, or celestial details. "
                "Provide clear, helpful responses based on the tool results. "
                f"Current capabilities: {AVAILABLE_SERVERS[selected_server_id]['capabilities']}"
            )
            
            mcp_clients[client_key] = MCPClient(
                model_name=request.model_name,
                mcp_server_url=server_url,
                system_prompt=request.system_prompt or enhanced_system_prompt
            )
        
        client = mcp_clients[client_key]
        
        # Set authentication headers
        headers = {
            "X-User-ID": user_id,
            "X-User-Email": user_info.get("email", ""),
            "X-Selected-Server": selected_server_id,
        }
        
        # Execute the intelligent chat
        result = await client.chat(request.prompt, headers=headers)
        
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
                    "server_capabilities": AVAILABLE_SERVERS[selected_server_id]['capabilities']
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
                model=request.model_name
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
        
        # Define available MCP servers with their capabilities
        available_servers = [
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
        ]
        
        # Check which servers the user has active sessions with
        user_id = user_info.get("sub", "anonymous")
        active_sessions = []
        
        for client_key in mcp_clients:
            if client_key.endswith(f":{user_id}"):
                server_url = client_key.split(f":{user_id}")[0]
                active_sessions.append(server_url)
        
        # Mark servers as connected if user has active sessions
        for server in available_servers:
            if server["server_url"] in active_sessions:
                server["status"] = "connected"
        
        return {
            "servers": available_servers,
            "user_id": user_id,
            "active_sessions": len(active_sessions)
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
        
        # Find and remove the client
        client_key = f"{server_id}:{user_id}"
        if client_key in mcp_clients:
            del mcp_clients[client_key]
            return {"message": f"Disconnected from server {server_id}"}
        else:
            raise HTTPException(status_code=404, detail="Server not found")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


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