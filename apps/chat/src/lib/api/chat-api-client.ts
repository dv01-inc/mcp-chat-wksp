/**
 * HTTP client for the standalone chat-api service
 * Replaces internal Next.js API routes with HTTP requests
 */

interface ChatApiConfig {
  baseUrl: string;
  token?: string;
}

interface ChatRequest {
  id: string;
  message: any;
  chatModel: any;
  toolChoice?: string;
  allowedAppDefaultToolkit?: string[];
  allowedMcpServers?: string[];
  projectId?: string;
}

interface AuthRequest {
  email: string;
}

interface McpRequest {
  action: string;
  [key: string]: any;
}

export class ChatApiClient {
  private config: ChatApiConfig;

  constructor(config: ChatApiConfig) {
    this.config = config;
  }

  private async request(endpoint: string, options: RequestInit = {}): Promise<Response> {
    const url = `${this.config.baseUrl}${endpoint}`;
    
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    if (this.config.token) {
      headers['Authorization'] = `Bearer ${this.config.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response;
  }

  // Health check
  async health() {
    const response = await this.request('/health');
    return response.json();
  }

  // Chat endpoints
  async chat(data: ChatRequest) {
    const response = await this.request('/api/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.body; // Return stream for streaming responses
  }

  async getChatModels() {
    const response = await this.request('/api/chat/models');
    return response.json();
  }

  async summarizeChat(data: any) {
    const response = await this.request('/api/chat/summarize', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async temporaryChat(data: any) {
    const response = await this.request('/api/chat/temporary', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async chatWithThread(threadId: string, data: any) {
    const response = await this.request(`/api/chat/${threadId}`, {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  // Auth endpoints
  async checkEmailExists(data: AuthRequest) {
    const response = await this.request('/api/auth/exists-by-email', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  // MCP endpoints
  async mcpAction(data: McpRequest) {
    const response = await this.request('/api/mcp/actions', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async getServerCustomizations(server: string) {
    const response = await this.request(`/api/mcp/server-customizations/${server}`);
    return response.json();
  }

  async saveServerCustomizations(server: string, customizations: any) {
    const response = await this.request(`/api/mcp/server-customizations/${server}`, {
      method: 'POST',
      body: JSON.stringify(customizations),
    });
    return response.json();
  }

  async getToolCustomizations(server: string, tool?: string) {
    const endpoint = tool 
      ? `/api/mcp/tool-customizations/${server}/${tool}`
      : `/api/mcp/tool-customizations/${server}`;
    const response = await this.request(endpoint);
    return response.json();
  }

  async saveToolCustomizations(server: string, tool: string, customizations: any) {
    const response = await this.request(`/api/mcp/tool-customizations/${server}/${tool}`, {
      method: 'POST',
      body: JSON.stringify(customizations),
    });
    return response.json();
  }

  // Thread endpoints
  async getThread(id: string) {
    const response = await this.request(`/api/thread/${id}`);
    return response.json();
  }

  async createThread(data: { title: string; projectId?: string }) {
    const response = await this.request('/api/thread', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return response.json();
  }

  async updateThread(id: string, updates: any) {
    const response = await this.request(`/api/thread/${id}`, {
      method: 'PUT',
      body: JSON.stringify(updates),
    });
    return response.json();
  }

  async deleteThread(id: string) {
    const response = await this.request(`/api/thread/${id}`, {
      method: 'DELETE',
    });
    return response.json();
  }

  // User endpoints
  async getUserPreferences() {
    const response = await this.request('/api/user/preferences');
    return response.json();
  }

  async updateUserPreferences(preferences: any) {
    const response = await this.request('/api/user/preferences', {
      method: 'POST',
      body: JSON.stringify(preferences),
    });
    return response.json();
  }

  async getUserProfile() {
    const response = await this.request('/api/user/profile');
    return response.json();
  }
}

// Create a singleton instance
const chatApiClient = new ChatApiClient({
  baseUrl: process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:3001',
  // Token will be set dynamically based on authentication
});

export { chatApiClient };