"""Dynamic MCP Server Manager.

This module provides a dynamic management system for MCP servers, replacing
the hardcoded server configurations with database-backed, runtime-configurable
server management.

Features:
- Load servers from database on startup
- Dynamic server addition/removal without code changes
- Intelligent server selection based on capabilities and keywords
- Connection pooling and lifecycle management
- Tool discovery and aggregation across all servers
"""

import asyncio
from typing import Dict, List, Optional, Any, Set
from sqlalchemy.orm import Session
from .database import MCPServerRepository, MCPServer
from .mcp_client import MCPClient


class DynamicMCPManager:
    """Dynamic MCP server manager with database-backed configuration."""

    def __init__(self, db_session_factory):
        self.db_session_factory = db_session_factory
        self.servers: Dict[str, Dict[str, Any]] = {}  # server_id -> server_info
        self.clients: Dict[str, MCPClient] = {}  # client_key -> MCPClient
        self.tools_cache: Dict[str, Any] = {}  # aggregated tools cache
        self._initialized = False

    async def initialize(self):
        """Initialize the manager by loading servers from database."""
        if self._initialized:
            return

        db = self.db_session_factory()
        try:
            server_repo = MCPServerRepository(db)
            db_servers = server_repo.get_all_servers()

            for db_server in db_servers:
                self.servers[str(db_server.id)] = {
                    "id": str(db_server.id),
                    "name": db_server.name,
                    "config": db_server.config,
                    "enabled": db_server.enabled,
                    "url": db_server.config.get("url"),
                    "transport": db_server.config.get("transport", "http"),
                    "capabilities": db_server.config.get("capabilities", []),
                    "keywords": db_server.config.get("keywords", []),
                    "description": db_server.config.get("description", ""),
                    "tools": db_server.config.get("tools", []),
                }

            print(f"✅ Loaded {len(self.servers)} MCP servers from database")
            self._initialized = True

        finally:
            db.close()

    def get_all_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get all configured servers."""
        return self.servers.copy()

    def get_enabled_servers(self) -> Dict[str, Dict[str, Any]]:
        """Get only enabled servers."""
        return {
            server_id: server_info
            for server_id, server_info in self.servers.items()
            if server_info.get("enabled", True)
        }

    def get_server(self, server_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific server by ID."""
        return self.servers.get(server_id)

    def get_server_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a server by name."""
        for server_info in self.servers.values():
            if server_info["name"] == name:
                return server_info
        return None

    async def add_server(self, name: str, config: Dict[str, Any]) -> str:
        """Add a new MCP server configuration."""
        db = self.db_session_factory()
        try:
            server_repo = MCPServerRepository(db)

            # Check if server name already exists
            existing = server_repo.get_server_by_name(name)
            if existing:
                raise ValueError(f"Server with name '{name}' already exists")

            # Validate config
            if not config.get("url"):
                raise ValueError("Server config must include 'url'")

            # Create in database
            db_server = server_repo.create_server(name, config)

            # Add to memory
            server_id = str(db_server.id)
            self.servers[server_id] = {
                "id": server_id,
                "name": name,
                "config": config,
                "enabled": True,
                "url": config.get("url"),
                "transport": config.get("transport", "http"),
                "capabilities": config.get("capabilities", []),
                "keywords": config.get("keywords", []),
                "description": config.get("description", ""),
                "tools": config.get("tools", []),
            }

            print(f"✅ Added MCP server: {name} ({server_id})")
            return server_id

        finally:
            db.close()

    async def remove_server(self, server_id: str) -> bool:
        """Remove an MCP server configuration."""
        if server_id not in self.servers:
            return False

        db = self.db_session_factory()
        try:
            server_repo = MCPServerRepository(db)
            success = server_repo.delete_server(server_id)

            if success:
                # Disconnect any active clients
                await self._disconnect_server_clients(server_id)

                # Remove from memory
                del self.servers[server_id]
                print(f"✅ Removed MCP server: {server_id}")

            return success

        finally:
            db.close()

    async def update_server(self, server_id: str, **updates) -> bool:
        """Update an MCP server configuration."""
        if server_id not in self.servers:
            return False

        db = self.db_session_factory()
        try:
            server_repo = MCPServerRepository(db)
            db_server = server_repo.update_server(server_id, **updates)

            if db_server:
                # Update memory
                server_info = self.servers[server_id]
                for key, value in updates.items():
                    if key == "config":
                        server_info["config"] = value
                        # Update derived fields from config
                        server_info["url"] = value.get("url", server_info.get("url"))
                        server_info["transport"] = value.get("transport", "http")
                        server_info["capabilities"] = value.get("capabilities", [])
                        server_info["keywords"] = value.get("keywords", [])
                        server_info["description"] = value.get("description", "")
                        server_info["tools"] = value.get("tools", [])
                    else:
                        server_info[key] = value

                print(f"✅ Updated MCP server: {server_id}")
                return True

        finally:
            db.close()

        return False

    def select_server_for_prompt(self, prompt: str) -> Optional[str]:
        """Intelligently select the best MCP server based on the prompt content."""
        if not self.servers:
            return None

        prompt_lower = prompt.lower()
        enabled_servers = self.get_enabled_servers()

        if not enabled_servers:
            return None

        # Score each server based on keyword matches
        server_scores = {}
        for server_id, server_info in enabled_servers.items():
            score = 0
            keywords = server_info.get("keywords", [])

            for keyword in keywords:
                if keyword.lower() in prompt_lower:
                    score += 1

            server_scores[server_id] = score

        # Find the server with the highest score
        if not server_scores:
            return None

        best_server = max(server_scores.items(), key=lambda x: x[1])

        # If no keywords match, return the first available server
        if best_server[1] == 0:
            return next(iter(enabled_servers.keys()))

        return best_server[0]

    def get_server_url(self, server_id: str) -> Optional[str]:
        """Get the URL for a given server ID."""
        server_info = self.servers.get(server_id)
        return server_info.get("url") if server_info else None

    async def get_or_create_client(
        self,
        server_id: str,
        user_id: str,
        model_name: str = "openai:gpt-4.1",
        system_prompt: str = None,
    ) -> Optional[MCPClient]:
        """Get or create an MCP client for a server."""
        server_info = self.servers.get(server_id)
        if not server_info or not server_info.get("enabled", True):
            return None

        client_key = f"{server_id}:{user_id}"

        if client_key not in self.clients:
            server_url = server_info.get("url")
            if not server_url:
                return None

            self.clients[client_key] = MCPClient(
                model_name=model_name,
                mcp_server_url=server_url,
                system_prompt=system_prompt,
            )

        return self.clients[client_key]

    async def disconnect_client(self, server_id: str, user_id: str):
        """Disconnect a specific client."""
        client_key = f"{server_id}:{user_id}"
        if client_key in self.clients:
            client = self.clients[client_key]
            await client.disconnect() if hasattr(client, "disconnect") else None
            del self.clients[client_key]

    async def _disconnect_server_clients(self, server_id: str):
        """Disconnect all clients for a specific server."""
        clients_to_remove = [
            key for key in self.clients.keys() if key.startswith(f"{server_id}:")
        ]

        for client_key in clients_to_remove:
            client = self.clients[client_key]
            await client.disconnect() if hasattr(client, "disconnect") else None
            del self.clients[client_key]

    def get_available_tools(self) -> Dict[str, Any]:
        """Get all available tools from all enabled servers."""
        tools = {}

        for server_id, server_info in self.get_enabled_servers().items():
            server_tools = server_info.get("tools", [])
            server_name = server_info.get("name", server_id)

            for tool_name in server_tools:
                tool_id = f"{server_name}:{tool_name}"
                tools[tool_id] = {
                    "name": tool_name,
                    "server_id": server_id,
                    "server_name": server_name,
                    "capabilities": server_info.get("capabilities", []),
                }

        return tools

    async def cleanup(self):
        """Cleanup all connections."""
        clients = list(self.clients.values())
        self.clients.clear()

        for client in clients:
            try:
                await client.disconnect() if hasattr(client, "disconnect") else None
            except Exception as e:
                print(f"Error disconnecting client: {e}")


# Global instance
_manager: Optional[DynamicMCPManager] = None


def get_mcp_manager(db_session_factory) -> DynamicMCPManager:
    """Get or create the global MCP manager instance."""
    global _manager
    if _manager is None:
        _manager = DynamicMCPManager(db_session_factory)
    return _manager


async def initialize_default_servers(manager: DynamicMCPManager):
    """Initialize default MCP servers if none exist."""
    if not manager.get_all_servers():
        print("🔧 No MCP servers found, adding default servers...")

        # Add default Playwright server
        await manager.add_server(
            "playwright",
            {
                "url": "http://localhost:8001/sse",
                "transport": "sse",
                "description": "Browser automation tools for web scraping, testing, and interaction",
                "capabilities": [
                    "browser_automation",
                    "web_navigation",
                    "screenshot",
                    "web_scraping",
                    "click",
                    "type",
                    "form_filling",
                    "page_interaction",
                ],
                "keywords": [
                    "browse",
                    "navigate",
                    "screenshot",
                    "click",
                    "type",
                    "website",
                    "page",
                    "browser",
                    "web",
                    "url",
                    "link",
                    "google",
                    "github",
                    "open",
                    "visit",
                    "scrape",
                    "extract",
                    "element",
                    "button",
                    "form",
                    "input",
                ],
                "tools": [
                    "browser_navigate",
                    "browser_click",
                    "browser_type",
                    "browser_screenshot",
                    "browser_wait_for",
                    "browser_extract_text",
                ],
            },
        )

        # Add default Apollo server
        await manager.add_server(
            "apollo",
            {
                "url": "http://localhost:5001/mcp",
                "transport": "http",
                "description": "Access to space mission data, astronaut information, and celestial body details",
                "capabilities": [
                    "space_data",
                    "astronaut_info",
                    "mission_details",
                    "launch_info",
                    "celestial_bodies",
                    "space_exploration",
                ],
                "keywords": [
                    "space",
                    "astronaut",
                    "mission",
                    "launch",
                    "nasa",
                    "spacex",
                    "rocket",
                    "satellite",
                    "orbit",
                    "celestial",
                    "planet",
                    "moon",
                    "mars",
                    "station",
                    "iss",
                    "crew",
                ],
                "tools": [
                    "get_astronaut_details",
                    "search_upcoming_launches",
                    "get_astronauts_currently_in_space",
                    "explore_celestial_bodies",
                ],
            },
        )

        print("✅ Default MCP servers added successfully")
