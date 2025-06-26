import { z } from "zod";

export type MCPServerConfig = {
  name: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  stdio?: boolean;
  [key: string]: any;
};

export type MCPServer = {
  id: string;
  name: string;
  config: MCPServerConfig;
  enabled: boolean;
  createdAt: Date;
  updatedAt: Date;
};

export type MCPToolCustomization = {
  id: string;
  userId: string;
  toolName: string;
  mcpServerId: string;
  prompt: string | null;
  createdAt: Date;
  updatedAt: Date;
};

export type MCPServerCustomization = {
  id: string;
  userId: string;
  mcpServerId: string;
  prompt: string | null;
  createdAt: Date;
  updatedAt: Date;
};

// Zod schemas
export const AllowedMCPServerZodSchema = z.object({
  serverId: z.string(),
  serverName: z.string(),
});

export type AllowedMCPServer = z.infer<typeof AllowedMCPServerZodSchema>;