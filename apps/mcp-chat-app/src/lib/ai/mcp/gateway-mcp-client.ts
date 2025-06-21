import { type MCPServerInfo, type MCPServerConfig, type MCPToolInfo } from "app-types/mcp";
import { jsonSchema, Tool, tool, ToolExecutionOptions } from "ai";
import logger from "logger";
import type { ConsolaInstance } from "consola";
import { colorize } from "consola/utils";
import { createDebounce, errorToString, toAny } from "lib/utils";

type GatewayClientOptions = {
  autoDisconnectSeconds?: number;
  gatewayUrl?: string;
  authToken?: string;
};

/**
 * Gateway MCP Client that routes through the MCP Gateway instead of direct connections
 */
export class GatewayMCPClient {
  private error?: unknown;
  private isConnected = false;
  private log: ConsolaInstance;
  private gatewayUrl: string;
  private authToken: string;
  
  // Information about available tools from the server
  toolInfo: MCPToolInfo[] = [];
  // Tool instances that can be used for AI functions
  tools: { [key: string]: Tool } = {};

  constructor(
    private name: string,
    private serverConfig: MCPServerConfig,
    private options: GatewayClientOptions = {},
    private disconnectDebounce = createDebounce(),
  ) {
    this.log = logger.withDefaults({
      message: colorize("cyan", `Gateway MCP Client ${this.name}: `),
    });
    
    // Default to Java gateway, fallback to Python gateway
    this.gatewayUrl = options.gatewayUrl || 'http://localhost:8002/api';
    this.authToken = options.authToken || 'mock-token';
  }

  getInfo(): MCPServerInfo {
    return {
      name: this.name,
      config: this.serverConfig,
      status: this.isConnected ? "connected" : "disconnected",
      error: this.error,
      toolInfo: this.toolInfo,
    };
  }

  private scheduleAutoDisconnect() {
    if (this.options.autoDisconnectSeconds) {
      this.disconnectDebounce(() => {
        this.disconnect();
      }, this.options.autoDisconnectSeconds * 1000);
    }
  }

  /**
   * Connect to the MCP server via gateway
   */
  async connect() {
    if (this.isConnected) {
      return true;
    }

    try {
      const startedAt = Date.now();
      this.log.info("Connecting to MCP server via gateway...");

      // Get server URL from config
      const serverUrl = this.getServerUrl();
      
      // Test gateway connection and get available tools
      const response = await fetch(`${this.gatewayUrl}/mcp/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({
          prompt: "list_tools",
          serverUrl: serverUrl,
          modelName: "gpt-4",
        }),
      });

      if (!response.ok) {
        throw new Error(`Gateway connection failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`Gateway error: ${result.error}`);
      }

      // Mock tool info based on known MCP servers
      this.toolInfo = this.getMockToolInfo(serverUrl);
      
      // Create AI SDK tool wrappers for each tool
      this.tools = this.toolInfo.reduce((prev, toolInfo) => {
        const parameters = jsonSchema(
          toAny({
            ...toolInfo.inputSchema,
            properties: toolInfo.inputSchema?.properties ?? {},
            additionalProperties: false,
          }),
        );
        
        prev[toolInfo.name] = tool({
          parameters,
          description: toolInfo.description,
          execute: (params, options: ToolExecutionOptions) => {
            options?.abortSignal?.throwIfAborted();
            return this.callTool(toolInfo.name, params);
          },
        });
        return prev;
      }, {});

      this.log.info(
        `Connected to MCP server via gateway in ${((Date.now() - startedAt) / 1000).toFixed(2)}s`,
      );
      
      this.isConnected = true;
      this.error = undefined;
      this.scheduleAutoDisconnect();
      
      return true;
    } catch (error) {
      this.log.error("Gateway connection failed:", error);
      this.isConnected = false;
      this.error = error;
      return false;
    }
  }

  async disconnect() {
    this.log.info("Disconnecting from gateway");
    this.isConnected = false;
  }

  async callTool(toolName: string, input?: unknown) {
    try {
      this.log.info("Gateway tool call:", toolName);
      
      if (this.error) {
        throw new Error("Gateway MCP Client is in an error state");
      }

      await this.connect(); // Ensure connected
      
      const serverUrl = this.getServerUrl();
      
      // Make the tool call through the gateway
      const response = await fetch(`${this.gatewayUrl}/mcp/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.authToken}`,
        },
        body: JSON.stringify({
          prompt: this.buildToolPrompt(toolName, input),
          serverUrl: serverUrl,
          modelName: "gpt-4",
        }),
      });

      if (!response.ok) {
        throw new Error(`Gateway request failed: ${response.status} ${response.statusText}`);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(result.error);
      }

      this.scheduleAutoDisconnect();
      
      return {
        content: [
          {
            type: "text",
            text: result.result,
          },
        ],
        isError: false,
      };
      
    } catch (error) {
      this.log.error("Gateway tool call failed:", toolName, error);
      
      return {
        content: [
          {
            type: "text",
            text: JSON.stringify({
              error: {
                message: errorToString(error),
                name: error?.name,
              },
            }),
          },
        ],
        isError: true,
      };
    }
  }

  private getServerUrl(): string {
    // Extract URL from server config
    if ('url' in this.serverConfig) {
      return this.serverConfig.url;
    }
    
    // Default URLs for known servers
    if (this.name.includes('apollo')) {
      return 'http://localhost:5000/mcp';
    }
    if (this.name.includes('playwright')) {
      return 'http://localhost:8001/mcp';
    }
    
    // Fallback
    return 'http://localhost:8001/mcp';
  }

  private buildToolPrompt(toolName: string, input?: unknown): string {
    const inputStr = input ? JSON.stringify(input) : '';
    return `Use the ${toolName} tool${inputStr ? ` with parameters: ${inputStr}` : ''}`;
  }

  private getMockToolInfo(serverUrl: string): MCPToolInfo[] {
    // Return mock tool info based on server URL
    if (serverUrl.includes('5000') || serverUrl.includes('apollo')) {
      return [
        {
          name: "ExploreCelestialBodies",
          description: "Search planets, moons, and stars",
          inputSchema: {
            type: "object",
            properties: {
              query: { type: "string", description: "Search query for celestial bodies" },
            },
            required: ["query"],
          },
        },
        {
          name: "GetAstronautDetails",
          description: "Get info about specific astronauts",
          inputSchema: {
            type: "object",
            properties: {
              astronautId: { type: "string", description: "ID of the astronaut" },
            },
            required: ["astronautId"],
          },
        },
        {
          name: "GetAstronautsCurrentlyInSpace",
          description: "See who's in space right now",
          inputSchema: {
            type: "object",
            properties: {},
          },
        },
        {
          name: "SearchUpcomingLaunches",
          description: "Find upcoming rocket launches",
          inputSchema: {
            type: "object",
            properties: {
              limit: { type: "number", description: "Number of launches to return" },
            },
          },
        },
      ];
    }
    
    if (serverUrl.includes('8001') || serverUrl.includes('playwright')) {
      return [
        {
          name: "navigate_to",
          description: "Navigate to a URL",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string", description: "URL to navigate to" },
            },
            required: ["url"],
          },
        },
        {
          name: "screenshot",
          description: "Take a screenshot of the current page",
          inputSchema: {
            type: "object",
            properties: {
              name: { type: "string", description: "Name for the screenshot" },
            },
          },
        },
        {
          name: "click",
          description: "Click on an element",
          inputSchema: {
            type: "object",
            properties: {
              selector: { type: "string", description: "CSS selector for the element" },
            },
            required: ["selector"],
          },
        },
      ];
    }
    
    return [];
  }
}

/**
 * Factory function to create a new Gateway MCP client
 */
export const createGatewayMCPClient = (
  name: string,
  serverConfig: MCPServerConfig,
  options: GatewayClientOptions = {},
): GatewayMCPClient => new GatewayMCPClient(name, serverConfig, options);