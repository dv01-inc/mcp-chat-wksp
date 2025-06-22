/**
 * Simple Gateway Client - A dumb client that only communicates with the MCP Gateway
 * No local MCP server management, just pure gateway communication
 */

export interface MCPServer {
  id: string;
  name: string;
  description: string;
  server_url: string;
  status: 'available' | 'connected' | 'error';
  transport: 'sse' | 'http';
  capabilities: string[];
  tools: string[];
}

export interface MCPServerListResponse {
  servers: MCPServer[];
  user_id: string;
  active_sessions: number;
}

export interface MCPResponse {
  result: string;
  usage?: {
    requests?: number;
    total_tokens?: number;
    server_id?: string;
    tool_name?: string;
  };
  error?: string;
}

export interface MCPToolRequest {
  server_id: string;
  tool_name: string;
  parameters?: Record<string, any>;
  model_name?: string;
}

export interface MCPQueryRequest {
  prompt: string;
  server_url: string;
  model_name?: string;
  system_prompt?: string;
}

export interface MCPChatRequest {
  prompt: string;
  server_url: string;
  model_name?: string;
  system_prompt?: string;
}

export class SimpleGatewayClient {
  private gatewayUrl: string;
  private authToken: string;

  constructor(
    gatewayUrl: string = 'http://localhost:8000',
    authToken: string = 'mock-token'
  ) {
    this.gatewayUrl = gatewayUrl;
    this.authToken = authToken;
  }

  private async makeRequest<T>(
    endpoint: string,
    method: 'GET' | 'POST' | 'DELETE' = 'GET',
    body?: any
  ): Promise<T> {
    const url = `${this.gatewayUrl}${endpoint}`;
    
    const options: RequestInit = {
      method,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.authToken}`,
      },
    };

    if (body && method !== 'GET') {
      options.body = JSON.stringify(body);
    }

    const response = await fetch(url, options);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Gateway request failed: ${response.status} ${response.statusText} - ${errorText}`);
    }

    return response.json();
  }

  /**
   * Get all available MCP servers and their capabilities
   */
  async getServers(): Promise<MCPServerListResponse> {
    return this.makeRequest<MCPServerListResponse>('/mcp/servers');
  }

  /**
   * Execute a specific tool on a server
   */
  async executeTool(request: MCPToolRequest): Promise<MCPResponse> {
    return this.makeRequest<MCPResponse>('/mcp/tools/execute', 'POST', request);
  }

  /**
   * Send a general query to a server (let the AI decide which tools to use)
   */
  async query(request: MCPQueryRequest): Promise<MCPResponse> {
    return this.makeRequest<MCPResponse>('/mcp/query', 'POST', request);
  }

  /**
   * Send a chat message to a server (maintains conversation context)
   */
  async chat(request: MCPChatRequest): Promise<MCPResponse> {
    return this.makeRequest<MCPResponse>('/mcp/chat', 'POST', request);
  }

  /**
   * Disconnect from a specific server
   */
  async disconnectServer(serverId: string): Promise<{ message: string }> {
    return this.makeRequest<{ message: string }>(`/mcp/servers/${serverId}`, 'DELETE');
  }

  /**
   * Check gateway health
   */
  async health(): Promise<{ status: string; service: string }> {
    return this.makeRequest<{ status: string; service: string }>('/health');
  }

  /**
   * Utility method to get a server by ID
   */
  async getServer(serverId: string): Promise<MCPServer | null> {
    const response = await this.getServers();
    return response.servers.find(server => server.id === serverId) || null;
  }

  /**
   * Utility method to get all tools across all servers
   */
  async getAllTools(): Promise<Array<{ server: MCPServer; tool: string }>> {
    const response = await this.getServers();
    const tools: Array<{ server: MCPServer; tool: string }> = [];
    
    for (const server of response.servers) {
      for (const tool of server.tools) {
        tools.push({ server, tool });
      }
    }
    
    return tools;
  }
}

// Export a default instance
export const gatewayClient = new SimpleGatewayClient(
  process.env.NEXT_PUBLIC_MCP_GATEWAY_URL,
  process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN
);