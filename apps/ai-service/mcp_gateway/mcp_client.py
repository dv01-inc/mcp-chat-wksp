"""MCP Client implementation using Pydantic AI for authenticated MCP calls."""

import asyncio
import httpx
from typing import Dict, Optional, List, Any
from pydantic_ai import Agent
from pydantic_ai.mcp import MCPServerHTTP


class DebugTracer:
    """Debug tracer for MCP operations."""
    
    def on_tool_call_start(self, tool_name: str, inputs: Dict[str, Any]) -> None:
        """Called when a tool call starts."""
        print(f"🔧 Calling tool: {tool_name} with {inputs}")

    def on_tool_call_end(self, tool_name: str, inputs: Dict[str, Any], output: Any) -> None:
        """Called when a tool call ends."""
        print(f"✅ Tool result from {tool_name}: {output}")

    def on_step(self, step: Any) -> None:
        """Called on each agent step."""
        print(f"🧠 Agent step: {step}")


class MCPClient:
    """MCP client for interacting with MCP servers using Pydantic AI."""

    def __init__(
        self,
        model_name: str = "openai:gpt-4.1",
        mcp_server_url: str = "http://localhost:8000/sse",
        system_prompt: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        """Initialize the MCP client."""
        self.server = MCPServerHTTP(url=mcp_server_url)

        if headers:
            self.server.headers = headers

        if system_prompt is None:
            system_prompt = (
                "You are an assistant that uses MCP tools to access data and perform tasks. "
                "Always use the available tools when appropriate to fulfill requests. "
                "Provide clear and helpful responses based on the tool results."
            )

        self.agent = Agent(
            model_name,
            mcp_servers=[self.server],
            system_prompt=system_prompt,
        )

        # Enable debug tracing in development
        self.agent.tracer = DebugTracer()
        
        # Store message history for chat functionality
        self._message_history: List[Any] = []

    def set_headers(self, headers: Dict[str, str]) -> None:
        """Set headers on the MCP server."""
        self.server.headers = headers

    async def run(
        self, 
        prompt: str, 
        message_history: Optional[List[Any]] = None, 
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Run a prompt through the agent with MCP server integration."""
        original_headers = None
        if headers:
            original_headers = self.server.headers
            self.server.headers = headers

        try:
            async with self.agent.run_mcp_servers():
                if message_history:
                    result = await self.agent.run(prompt, message_history=message_history)
                else:
                    result = await self.agent.run(prompt)
            
            print(f"Usage: {result.usage()}")

            if original_headers is not None:
                self.server.headers = original_headers

            return result

        except Exception as e:
            if original_headers is not None:
                self.server.headers = original_headers
            raise Exception(f"MCP client error: {e}")

    async def chat(
        self, 
        prompt: str, 
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """Run a prompt with persistent conversation history."""
        result = await self.run(prompt, message_history=self._message_history, headers=headers)
        
        # Update message history
        self._message_history.extend(result.all_messages())
        
        return result

    async def stream(
        self, 
        prompt: str, 
        message_history: Optional[List[Any]] = None, 
        headers: Optional[Dict[str, str]] = None
    ):
        """Stream responses from the agent."""
        original_headers = None
        if headers:
            original_headers = self.server.headers
            self.server.headers = headers

        try:
            async with self.agent.run_mcp_servers():
                if message_history:
                    async with self.agent.iter(prompt, message_history=message_history) as run:
                        async for chunk in run:
                            yield chunk
                else:
                    async with self.agent.iter(prompt) as run:
                        async for chunk in run:
                            yield chunk
        finally:
            if original_headers is not None:
                self.server.headers = original_headers

    def clear_history(self) -> None:
        """Clear the chat message history."""
        self._message_history.clear()

    def get_history_length(self) -> int:
        """Get the number of messages in the history."""
        return len(self._message_history)


class MCPClientManager:
    """Manager for multiple MCP clients with different configurations."""
    
    def __init__(self):
        self.clients: Dict[str, MCPClient] = {}
    
    def get_client(
        self,
        server_url: str,
        user_id: str,
        model_name: str = "openai:gpt-4.1",
        system_prompt: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> MCPClient:
        """Get or create an MCP client for a specific server and user."""
        client_key = f"{server_url}:{user_id}"
        
        if client_key not in self.clients:
            self.clients[client_key] = MCPClient(
                model_name=model_name,
                mcp_server_url=server_url,
                system_prompt=system_prompt,
                headers=headers
            )
        
        return self.clients[client_key]
    
    def remove_client(self, server_url: str, user_id: str) -> bool:
        """Remove a client for a specific server and user."""
        client_key = f"{server_url}:{user_id}"
        
        if client_key in self.clients:
            del self.clients[client_key]
            return True
        
        return False
    
    def list_clients(self, user_id: str) -> List[str]:
        """List all server URLs for a specific user."""
        user_clients = []
        for client_key in self.clients:
            if client_key.endswith(f":{user_id}"):
                server_url = client_key.split(f":{user_id}")[0]
                user_clients.append(server_url)
        
        return user_clients
    
    def clear_all_clients(self) -> None:
        """Clear all clients."""
        self.clients.clear()


# Global client manager instance
client_manager = MCPClientManager()