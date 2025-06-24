"use server";

/**
 * Gateway-based MCP actions
 * All MCP operations are now handled through the gateway
 */

import { z } from "zod";

const GATEWAY_URL = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8000';
const AUTH_TOKEN = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';

async function makeGatewayRequest(endpoint: string, method: 'GET' | 'POST' = 'GET', body?: any) {
  const response = await fetch(`${GATEWAY_URL}${endpoint}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${AUTH_TOKEN}`,
    },
    body: body ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Gateway request failed: ${response.status} - ${errorText}`);
  }

  return response.json();
}

export async function selectMcpClientsAction() {
  try {
    const response = await makeGatewayRequest('/mcp/servers');
    
    // Transform gateway response to match expected format
    return response.servers.map((server: any) => ({
      id: server.id,
      name: server.name,
      status: server.status,
      config: {
        url: server.server_url,
        transport: server.transport,
      },
      error: null,
      toolInfo: server.tools.map((tool: string) => ({
        name: tool,
        description: `${tool} from ${server.name}`,
      })),
    }));
  } catch (error) {
    console.error('Failed to select MCP clients:', error);
    return [];
  }
}

export async function selectMcpClientAction(id: string) {
  try {
    const clients = await selectMcpClientsAction();
    const client = clients.find(c => c.id === id);
    
    if (!client) {
      throw new Error("Client not found");
    }
    
    return client;
  } catch (error) {
    console.error('Failed to select MCP client:', error);
    throw error;
  }
}

export async function saveMcpClientAction(server: any) {
  // In gateway mode, servers are managed by the gateway
  // This is a no-op since server configuration is handled at the gateway level
  console.log('Gateway mode: Server configuration managed by gateway');
  return { success: true, message: 'Server management handled by gateway' };
}

export async function deleteMcpClientAction(id: string) {
  try {
    await makeGatewayRequest(`/mcp/servers/${id}`, 'DELETE');
    return { success: true };
  } catch (error) {
    console.error('Failed to delete MCP client:', error);
    throw error;
  }
}

export async function refreshMcpClientAction(id: string) {
  // In gateway mode, refresh is handled by re-fetching server list
  return await selectMcpClientAction(id);
}

// New gateway-specific actions

export async function executeToolAction(serverId: string, toolName: string, parameters?: any) {
  try {
    return await makeGatewayRequest('/mcp/tools/execute', 'POST', {
      server_id: serverId,
      tool_name: toolName,
      parameters: parameters || {},
    });
  } catch (error) {
    console.error('Failed to execute tool:', error);
    throw error;
  }
}

export async function queryServerAction(prompt: string, modelName?: string) {
  try {
    // Gateway handles server selection automatically - no server_url needed!
    return await makeGatewayRequest('/mcp/query', 'POST', {
      prompt,
      model_name: modelName || 'openai:gpt-4',
    });
  } catch (error) {
    console.error('Failed to query:', error);
    throw error;
  }
}

export async function chatWithServerAction(prompt: string, modelName?: string) {
  try {
    // Gateway handles server selection automatically - no server_url needed!
    return await makeGatewayRequest('/mcp/chat', 'POST', {
      prompt,
      model_name: modelName || 'openai:gpt-4',
    });
  } catch (error) {
    console.error('Failed to chat:', error);
    throw error;
  }
}

// Backward compatibility function for voice chat
export async function callMcpToolByServerNameAction(serverId: string, toolName: string, parameters?: any) {
  return executeToolAction(serverId, toolName, parameters);
}