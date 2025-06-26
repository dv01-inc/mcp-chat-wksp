import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { MCPServerConfig } from "../types/mcp.js";
import { tool, Tool } from "ai";

export interface MCPToolInfo {
  name: string;
  description?: string;
  inputSchema: any;
}

export interface MCPServerInfo {
  name: string;
  config: MCPServerConfig;
  toolInfo: MCPToolInfo[];
}

export class MCPClient {
  private client?: Client;
  private error?: unknown;
  private isConnected = false;
  
  // Information about available tools from the server
  toolInfo: MCPToolInfo[] = [];
  // Tool instances that can be used for AI functions
  tools: { [key: string]: Tool } = {};

  constructor(
    private name: string,
    private serverConfig: MCPServerConfig,
  ) {}

  async connect(): Promise<boolean> {
    try {
      let transport;

      // Determine transport based on config
      if (this.serverConfig.command) {
        // Stdio transport
        transport = new StdioClientTransport({
          command: this.serverConfig.command,
          args: this.serverConfig.args || [],
          env: this.serverConfig.env,
        });
      } else if (this.serverConfig.name && this.serverConfig.name.includes('http')) {
        // SSE transport (simplified detection)
        transport = new SSEClientTransport(new URL(this.serverConfig.name));
      } else {
        throw new Error(`Unsupported MCP server config: ${JSON.stringify(this.serverConfig)}`);
      }

      this.client = new Client(
        {
          name: "chat-api-client",
          version: "1.0.0",
        },
        {
          capabilities: {
            tools: {},
          },
        }
      );

      await this.client.connect(transport);
      this.isConnected = true;

      // Get available tools
      await this.loadTools();

      console.log(`✅ Connected to MCP server: ${this.name}`);
      return true;
    } catch (error) {
      this.error = error;
      console.error(`❌ Failed to connect to MCP server ${this.name}:`, error);
      return false;
    }
  }

  private async loadTools(): Promise<void> {
    if (!this.client) return;

    try {
      const response = await this.client.listTools();
      this.toolInfo = response.tools.map((tool: any) => ({
        name: tool.name,
        description: tool.description,
        inputSchema: tool.inputSchema,
      }));

      // Create AI tool instances
      this.tools = {};
      for (const toolInfo of this.toolInfo) {
        this.tools[toolInfo.name] = tool({
          description: toolInfo.description || `Tool: ${toolInfo.name}`,
          parameters: toolInfo.inputSchema,
          execute: async (parameters) => {
            return await this.callTool(toolInfo.name, parameters);
          },
        });
      }

      console.log(`📦 Loaded ${this.toolInfo.length} tools from ${this.name}`);
    } catch (error) {
      console.error(`❌ Failed to load tools from ${this.name}:`, error);
    }
  }

  async callTool(name: string, parameters: any): Promise<any> {
    if (!this.client || !this.isConnected) {
      throw new Error(`MCP client not connected: ${this.name}`);
    }

    try {
      const response = await this.client.callTool({
        name,
        arguments: parameters,
      });

      return response.content;
    } catch (error) {
      console.error(`❌ Tool call failed ${this.name}:${name}:`, error);
      throw error;
    }
  }

  async disconnect(): Promise<void> {
    if (this.client) {
      await this.client.close();
      this.isConnected = false;
      console.log(`🔌 Disconnected from MCP server: ${this.name}`);
    }
  }

  getInfo(): MCPServerInfo {
    return {
      name: this.name,
      config: this.serverConfig,
      toolInfo: this.toolInfo,
    };
  }

  isReady(): boolean {
    return this.isConnected && !this.error;
  }
}