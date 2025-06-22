/**
 * React hook for MCP Gateway communication
 * Provides a simple interface for React components to interact with MCP servers
 */

import { useState, useEffect, useCallback } from 'react';
import { 
  SimpleGatewayClient, 
  type MCPServer, 
  type MCPResponse,
  type MCPToolRequest,
  type MCPQueryRequest,
  type MCPChatRequest 
} from '../lib/ai/mcp/simple-gateway-client';

export interface UseMCPGatewayResult {
  // State
  servers: MCPServer[];
  loading: boolean;
  error: string | null;
  
  // Actions
  refreshServers: () => Promise<void>;
  executeTool: (request: MCPToolRequest) => Promise<MCPResponse>;
  query: (request: MCPQueryRequest) => Promise<MCPResponse>;
  chat: (request: MCPChatRequest) => Promise<MCPResponse>;
  disconnectServer: (serverId: string) => Promise<void>;
  
  // Utilities
  getServer: (serverId: string) => MCPServer | undefined;
  getServerTools: (serverId: string) => string[];
  getAllTools: () => Array<{ server: MCPServer; tool: string }>;
}

export function useMCPGateway(
  gatewayUrl?: string,
  authToken?: string
): UseMCPGatewayResult {
  const [client] = useState(() => new SimpleGatewayClient(gatewayUrl, authToken));
  const [servers, setServers] = useState<MCPServer[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshServers = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await client.getServers();
      setServers(response.servers);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch servers';
      setError(errorMessage);
      console.error('Failed to refresh servers:', err);
    } finally {
      setLoading(false);
    }
  }, [client]);

  const executeTool = useCallback(async (request: MCPToolRequest): Promise<MCPResponse> => {
    setError(null);
    try {
      const response = await client.executeTool(request);
      if (response.error) {
        throw new Error(response.error);
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Tool execution failed';
      setError(errorMessage);
      throw err;
    }
  }, [client]);

  const query = useCallback(async (request: MCPQueryRequest): Promise<MCPResponse> => {
    setError(null);
    try {
      const response = await client.query(request);
      if (response.error) {
        throw new Error(response.error);
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Query failed';
      setError(errorMessage);
      throw err;
    }
  }, [client]);

  const chat = useCallback(async (request: MCPChatRequest): Promise<MCPResponse> => {
    setError(null);
    try {
      const response = await client.chat(request);
      if (response.error) {
        throw new Error(response.error);
      }
      return response;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Chat failed';
      setError(errorMessage);
      throw err;
    }
  }, [client]);

  const disconnectServer = useCallback(async (serverId: string): Promise<void> => {
    setError(null);
    try {
      await client.disconnectServer(serverId);
      // Refresh servers to update status
      await refreshServers();
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Disconnect failed';
      setError(errorMessage);
      throw err;
    }
  }, [client, refreshServers]);

  const getServer = useCallback((serverId: string): MCPServer | undefined => {
    return servers.find(server => server.id === serverId);
  }, [servers]);

  const getServerTools = useCallback((serverId: string): string[] => {
    const server = getServer(serverId);
    return server?.tools || [];
  }, [getServer]);

  const getAllTools = useCallback((): Array<{ server: MCPServer; tool: string }> => {
    const tools: Array<{ server: MCPServer; tool: string }> = [];
    
    for (const server of servers) {
      for (const tool of server.tools) {
        tools.push({ server, tool });
      }
    }
    
    return tools;
  }, [servers]);

  // Load servers on mount
  useEffect(() => {
    refreshServers();
  }, [refreshServers]);

  return {
    // State
    servers,
    loading,
    error,
    
    // Actions
    refreshServers,
    executeTool,
    query,
    chat,
    disconnectServer,
    
    // Utilities
    getServer,
    getServerTools,
    getAllTools,
  };
}

export default useMCPGateway;