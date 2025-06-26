import { MCPClient, MCPServerInfo } from "./mcp-client.js";
import { MCPServerConfig } from "../types/mcp.js";
import { db } from "../db/connection.js";
import { McpServerSchema } from "../db/schema.js";
import { eq } from "drizzle-orm";
import { Tool } from "ai";

export interface MCPConfigStorage {
  init(manager: MCPClientsManager): Promise<void>;
  loadAll(): Promise<Array<{ id: string; name: string; config: MCPServerConfig }>>;
  save(server: { name: string; config: MCPServerConfig }): Promise<{ id: string; name: string; config: MCPServerConfig }>;
  delete(id: string): Promise<void>;
  has(id: string): Promise<boolean>;
  get(id: string): Promise<{ id: string; name: string; config: MCPServerConfig } | null>;
}

export class DatabaseMCPStorage implements MCPConfigStorage {
  async init(manager: MCPClientsManager): Promise<void> {
    // Database is already initialized
  }

  async loadAll() {
    const servers = await db
      .select()
      .from(McpServerSchema)
      .where(eq(McpServerSchema.enabled, true));

    return servers.map(server => ({
      id: server.id,
      name: server.name,
      config: server.config,
    }));
  }

  async save(server: { name: string; config: MCPServerConfig }) {
    const [result] = await db
      .insert(McpServerSchema)
      .values({
        name: server.name,
        config: server.config,
      })
      .returning();

    return {
      id: result.id,
      name: result.name,
      config: result.config,
    };
  }

  async delete(id: string): Promise<void> {
    await db
      .delete(McpServerSchema)
      .where(eq(McpServerSchema.id, id));
  }

  async has(id: string): Promise<boolean> {
    const [result] = await db
      .select({ id: McpServerSchema.id })
      .from(McpServerSchema)
      .where(eq(McpServerSchema.id, id));
    return !!result;
  }

  async get(id: string) {
    const [result] = await db
      .select()
      .from(McpServerSchema)
      .where(eq(McpServerSchema.id, id));

    if (!result) return null;

    return {
      id: result.id,
      name: result.name,
      config: result.config,
    };
  }
}

export class MCPClientsManager {
  private clients = new Map<string, { client: MCPClient; name: string }>();
  private initialized = false;

  constructor(
    private storage?: MCPConfigStorage,
    private autoDisconnectSeconds: number = 60 * 30, // 30 minutes
  ) {
    // Clean up on process exit
    process.on("SIGINT", this.cleanup.bind(this));
    process.on("SIGTERM", this.cleanup.bind(this));
  }

  async init(): Promise<void> {
    if (this.initialized) return;

    try {
      await this.cleanup();

      if (this.storage) {
        await this.storage.init(this);
        const configs = await this.storage.loadAll();
        
        // Connect to all servers in parallel
        await Promise.all(
          configs.map(({ id, name, config }) =>
            this.addClient(id, name, config)
          )
        );
      }

      this.initialized = true;
      console.log(`🚀 MCP Manager initialized with ${this.clients.size} clients`);
    } catch (error) {
      console.error("❌ Failed to initialize MCP Manager:", error);
      throw error;
    }
  }

  /**
   * Returns all tools from all clients as a flat object
   */
  tools(): Record<string, Tool> {
    const allTools: Record<string, Tool> = {};

    for (const [id, { client }] of this.clients.entries()) {
      if (client.isReady()) {
        for (const [toolName, tool] of Object.entries(client.tools)) {
          // Create unique tool ID: serverName:toolName
          const toolId = `${client.getInfo().name}:${toolName}`;
          allTools[toolId] = {
            ...tool,
            // Add metadata for tracking
            _originToolName: toolName,
            _mcpServerName: client.getInfo().name,
            _mcpServerId: id,
          } as any;
        }
      }
    }

    return allTools;
  }

  /**
   * Add a new client instance to memory only
   */
  async addClient(id: string, name: string, serverConfig: MCPServerConfig): Promise<void> {
    // Remove existing client if it exists
    if (this.clients.has(id)) {
      const { client } = this.clients.get(id)!;
      await client.disconnect();
    }

    const client = new MCPClient(name, serverConfig);
    const connected = await client.connect();

    if (connected) {
      this.clients.set(id, { client, name });
      console.log(`✅ Added MCP client: ${name} (${id})`);
    } else {
      console.error(`❌ Failed to add MCP client: ${name} (${id})`);
      throw new Error(`Failed to connect to MCP server: ${name}`);
    }
  }

  /**
   * Persist a new client configuration and add to memory
   */
  async persistClient(server: { name: string; config: MCPServerConfig }): Promise<string> {
    if (!this.storage) {
      throw new Error("No storage configured for MCP manager");
    }

    const entity = await this.storage.save(server);
    await this.addClient(entity.id, server.name, server.config);
    return entity.id;
  }

  /**
   * Remove a client by ID
   */
  async removeClient(id: string): Promise<void> {
    if (this.storage && await this.storage.has(id)) {
      await this.storage.delete(id);
    }

    const clientEntry = this.clients.get(id);
    if (clientEntry) {
      await clientEntry.client.disconnect();
      this.clients.delete(id);
      console.log(`🗑️ Removed MCP client: ${clientEntry.name} (${id})`);
    }
  }

  /**
   * Refresh an existing client
   */
  async refreshClient(id: string): Promise<void> {
    const clientEntry = this.clients.get(id);
    if (!clientEntry) {
      throw new Error(`Client ${id} not found`);
    }

    if (this.storage) {
      const server = await this.storage.get(id);
      if (!server) {
        throw new Error(`Client ${id} not found in storage`);
      }
      await this.addClient(id, server.name, server.config);
    } else {
      const currentConfig = clientEntry.client.getInfo().config;
      await this.addClient(id, clientEntry.name, currentConfig);
    }
  }

  /**
   * Get all client information
   */
  async getClients(): Promise<Array<{ id: string; client: MCPClient }>> {
    return Array.from(this.clients.entries()).map(([id, { client }]) => ({
      id,
      client,
    }));
  }

  /**
   * Get a specific client
   */
  async getClient(id: string): Promise<{ client: MCPClient; name: string } | undefined> {
    return this.clients.get(id);
  }

  /**
   * Get server info for all connected clients
   */
  getServerInfo(): MCPServerInfo[] {
    return Array.from(this.clients.values()).map(({ client }) => client.getInfo());
  }

  /**
   * Clean up all connections
   */
  async cleanup(): Promise<void> {
    const clients = Array.from(this.clients.values());
    this.clients.clear();

    await Promise.allSettled(
      clients.map(({ client }) => client.disconnect())
    );

    console.log(`🧹 Cleaned up ${clients.length} MCP clients`);
  }

  /**
   * Check if manager is ready
   */
  isReady(): boolean {
    return this.initialized;
  }

  /**
   * Get ready clients count
   */
  getReadyClientsCount(): number {
    return Array.from(this.clients.values()).filter(({ client }) => client.isReady()).length;
  }
}

// Global instance
let mcpManager: MCPClientsManager | null = null;

export function createMCPClientsManager(storage?: MCPConfigStorage): MCPClientsManager {
  if (!mcpManager) {
    mcpManager = new MCPClientsManager(storage);
  }
  return mcpManager;
}

export function getMCPClientsManager(): MCPClientsManager | null {
  return mcpManager;
}