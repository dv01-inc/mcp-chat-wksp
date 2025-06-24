"use server";

import {
  generateObject,
  generateText,
  jsonSchema,
  LanguageModel,
  type Message,
} from "ai";

import {
  CREATE_THREAD_TITLE_PROMPT,
  generateExampleToolSchemaPrompt,
} from "lib/ai/prompts";

import type { ChatModel, ChatThread, Project } from "app-types/chat";

// Gateway-based chat actions - all database operations moved to gateway
import { customModelProvider } from "lib/ai/models";
import { toAny } from "lib/utils";
import { McpServerCustomizationsPrompt, MCPToolInfo } from "app-types/mcp";
import { getSession } from "auth/server";
import logger from "logger";
import { redirect } from "next/navigation";

const GATEWAY_URL = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8000';
const AUTH_TOKEN = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';

async function makeGatewayRequest(endpoint: string, method: 'GET' | 'POST' | 'PUT' | 'DELETE' = 'GET', body?: any) {
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

export async function getUserId() {
  const session = await getSession();
  const userId = session?.user?.id;
  if (!userId) {
    throw new Error("User not found");
  }
  return userId;
}

export async function generateTitleFromUserMessageAction({
  message,
  model,
}: { message: Message; model: LanguageModel }) {
  await getSession();
  const prompt = toAny(message.parts?.at(-1))?.text || "unknown";

  const { text: title } = await generateText({
    model,
    system: CREATE_THREAD_TITLE_PROMPT,
    prompt,
    maxTokens: 200,
  });

  return title.trim();
}

export async function selectThreadWithMessagesAction(threadId: string) {
  const session = await getSession();
  
  try {
    const thread = await makeGatewayRequest(`/chat/threads/${threadId}`);
    
    if (thread.user_id !== session?.user.id) {
      return redirect("/");
    }
    
    return {
      id: thread.id,
      title: thread.title,
      userId: thread.user_id,
      projectId: thread.project_id,
      createdAt: new Date(thread.created_at),
      messages: thread.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        parts: msg.parts,
        attachments: msg.attachments,
        annotations: msg.annotations,
        model: msg.model,
        createdAt: new Date(msg.created_at),
        threadId: thread.id
      }))
    };
  } catch (error: any) {
    logger.error("Thread not found", threadId, error);
    return redirect("/");
  }
}

export async function deleteMessageAction(messageId: string) {
  // TODO: Implement message deletion in gateway
  throw new Error("Message deletion not yet implemented in gateway");
}

export async function deleteThreadAction(threadId: string) {
  try {
    await makeGatewayRequest(`/chat/threads/${threadId}`, 'DELETE');
  } catch (error: any) {
    logger.error("Failed to delete thread", threadId, error);
    throw error;
  }
}

export async function deleteMessagesByChatIdAfterTimestampAction(
  messageId: string,
) {
  "use server";
  // TODO: Implement message deletion after timestamp in gateway
  throw new Error("Message deletion after timestamp not yet implemented in gateway");
}

export async function selectThreadListByUserIdAction() {
  try {
    const response = await makeGatewayRequest('/chat/threads');
    return response.threads.map((thread: any) => ({
      id: thread.id,
      title: thread.title,
      userId: thread.user_id,
      projectId: thread.project_id,
      createdAt: new Date(thread.created_at),
      lastMessageAt: thread.last_message_at ? new Date(thread.last_message_at).getTime() : 0
    }));
  } catch (error: any) {
    logger.error("Failed to get threads", error);
    return [];
  }
}

export async function selectMessagesByThreadIdAction(threadId: string) {
  try {
    const thread = await makeGatewayRequest(`/chat/threads/${threadId}`);
    return thread.messages.map((msg: any) => ({
      id: msg.id,
      role: msg.role,
      parts: msg.parts,
      attachments: msg.attachments,
      annotations: msg.annotations,
      model: msg.model,
      createdAt: new Date(msg.created_at),
      threadId: threadId
    }));
  } catch (error: any) {
    logger.error("Failed to get messages", threadId, error);
    return [];
  }
}

export async function updateThreadAction(
  id: string,
  thread: Partial<Omit<ChatThread, "createdAt" | "updatedAt" | "userId">>,
) {
  try {
    await makeGatewayRequest(`/chat/threads/${id}`, 'PUT', {
      title: thread.title,
      project_id: thread.projectId
    });
  } catch (error: any) {
    logger.error("Failed to update thread", id, error);
    throw error;
  }
}

export async function deleteThreadsAction() {
  try {
    const response = await makeGatewayRequest('/chat/threads');
    // Delete all threads one by one
    await Promise.all(
      response.threads.map((thread: any) => 
        makeGatewayRequest(`/chat/threads/${thread.id}`, 'DELETE')
      )
    );
  } catch (error: any) {
    logger.error("Failed to delete all threads", error);
    throw error;
  }
}

export async function generateExampleToolSchemaAction(options: {
  model?: ChatModel;
  toolInfo: MCPToolInfo;
  prompt?: string;
}) {
  const model = customModelProvider.getModel(options.model);

  const schema = jsonSchema(
    toAny({
      ...options.toolInfo.inputSchema,
      properties: options.toolInfo.inputSchema?.properties ?? {},
      additionalProperties: false,
    }),
  );
  const { object } = await generateObject({
    model,
    schema,
    prompt: generateExampleToolSchemaPrompt({
      toolInfo: options.toolInfo,
      prompt: options.prompt,
    }),
  });

  return object;
}

export async function selectProjectListByUserIdAction() {
  // TODO: Implement projects in gateway
  return [];
}

// Project-related functions - TODO: Implement in gateway when needed
export async function insertProjectAction({
  name,
  instructions,
}: {
  name: string;
  instructions?: Project["instructions"];
}) {
  // TODO: Implement projects in gateway
  throw new Error("Projects not yet implemented in gateway");
}

export async function insertProjectWithThreadAction({
  name,
  instructions,
  threadId,
}: {
  name: string;
  instructions?: Project["instructions"];
  threadId: string;
}) {
  // TODO: Implement projects in gateway
  throw new Error("Projects not yet implemented in gateway");
}

export async function selectProjectByIdAction(id: string) {
  // TODO: Implement projects in gateway
  return null;
}

export async function updateProjectAction(
  id: string,
  project: Partial<Pick<Project, "name" | "instructions">>,
) {
  // TODO: Implement projects in gateway
  throw new Error("Projects not yet implemented in gateway");
}

export async function deleteProjectAction(id: string) {
  // TODO: Implement projects in gateway
  throw new Error("Projects not yet implemented in gateway");
}

export async function rememberProjectInstructionsAction(
  projectId: string,
): Promise<Project["instructions"] | null> {
  // TODO: Implement projects in gateway
  return null;
}

export async function rememberThreadAction(threadId: string) {
  try {
    const thread = await makeGatewayRequest(`/chat/threads/${threadId}`);
    return {
      id: thread.id,
      title: thread.title,
      userId: thread.user_id,
      projectId: thread.project_id,
      createdAt: new Date(thread.created_at)
    };
  } catch (error: any) {
    return null;
  }
}

export async function updateProjectNameAction(id: string, name: string) {
  // TODO: Implement projects in gateway
  throw new Error("Projects not yet implemented in gateway");
}

export async function rememberMcpServerCustomizationsAction(userId: string) {
  // TODO: Implement MCP customizations in gateway
  return {};
}
