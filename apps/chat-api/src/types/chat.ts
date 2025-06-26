import { z } from "zod";

export type ChatModel = {
  provider: string;
  model: string;
};

export type ChatThread = {
  id: string;
  title: string;
  userId: string;
  createdAt: Date;
  projectId: string | null;
};

export type Project = {
  id: string;
  name: string;
  userId: string;
  instructions: {
    systemPrompt: string;
  };
  createdAt: Date;
  updatedAt: Date;
};

export type ChatMessage = {
  id: string;
  threadId: string;
  role: "user" | "assistant" | "system";
  parts: any[];
  annotations?: ChatMessageAnnotation[];
  attachments?: unknown[];
  model: string | null;
  createdAt: Date;
};

export type ChatMention =
  | {
      type: "tool";
      name: string;
      serverName?: string;
      serverId: string;
    }
  | {
      type: "mcpServer";
      name: string;
      serverId: string;
    };

export type ChatMessageAnnotation = {
  type: string;
  data?: any;
  mentions?: ChatMention[];
};

// Zod schemas for validation
export const chatApiSchemaRequestBodySchema = z.object({
  id: z.string(),
  message: z.any(),
  chatModel: z.object({
    provider: z.string(),
    model: z.string(),
  }),
  toolChoice: z.string().optional(),
  allowedAppDefaultToolkit: z.array(z.string()).optional(),
  allowedMcpServers: z.array(z.string()).optional(),
  projectId: z.string().optional(),
});

export type ChatApiSchemaRequestBody = z.infer<typeof chatApiSchemaRequestBodySchema>;