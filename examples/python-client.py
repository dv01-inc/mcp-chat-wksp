#!/usr/bin/env python3
"""
Example Python client for MCP Gateway
Demonstrates how easy it is to integrate any client with the MCP Gateway
"""

import requests
import json
from typing import Dict, Any, List

class MCPGatewayClient:
    def __init__(self, gateway_url: str = "http://localhost:8000", auth_token: str = "mock-token"):
        self.gateway_url = gateway_url
        self.auth_token = auth_token
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {auth_token}"
        }
    
    def get_servers(self) -> Dict[str, Any]:
        """Get all available MCP servers"""
        response = requests.get(f"{self.gateway_url}/mcp/servers", headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def execute_tool(self, server_id: str, tool_name: str, parameters: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute a specific tool on a server"""
        data = {
            "server_id": server_id,
            "tool_name": tool_name,
            "parameters": parameters or {}
        }
        response = requests.post(f"{self.gateway_url}/mcp/tools/execute", 
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
    def query(self, server_url: str, prompt: str, model_name: str = "gpt-4") -> Dict[str, Any]:
        """Send a natural language query to a server"""
        data = {
            "prompt": prompt,
            "server_url": server_url,
            "model_name": model_name
        }
        response = requests.post(f"{self.gateway_url}/mcp/query",
                               headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()

def main():
    # Initialize client
    client = MCPGatewayClient()
    
    print("🚀 MCP Gateway Python Client Demo")
    print("=" * 40)
    
    # Get available servers
    print("\n1. Discovering available MCP servers...")
    servers_response = client.get_servers()
    servers = servers_response["servers"]
    
    print(f"Found {len(servers)} MCP servers:")
    for server in servers:
        print(f"  • {server['name']} ({server['id']})")
        print(f"    Status: {server['status']}")
        print(f"    Tools: {len(server['tools'])}")
        print(f"    Capabilities: {', '.join(server['capabilities'][:3])}...")
        print()
    
    # Execute a specific tool
    print("2. Executing a Playwright tool...")
    try:
        result = client.execute_tool(
            server_id="playwright",
            tool_name="browser_navigate",
            parameters={"url": "https://github.com"}
        )
        print(f"✅ Tool execution successful!")
        print(f"Result: {result['result'][:100]}...")
        if result.get('usage'):
            print(f"Usage: {result['usage']}")
    except Exception as e:
        print(f"❌ Tool execution failed: {e}")
    
    print()
    
    # Send a natural language query
    print("3. Sending a natural language query...")
    try:
        playwright_server = next(s for s in servers if s['id'] == 'playwright')
        result = client.query(
            server_url=playwright_server['server_url'],
            prompt="Take a screenshot of the current page"
        )
        print(f"✅ Query successful!")
        print(f"Result: {result['result'][:100]}...")
    except Exception as e:
        print(f"❌ Query failed: {e}")
    
    print("\n🎉 Demo completed! Any client can easily integrate with the MCP Gateway.")

if __name__ == "__main__":
    main()