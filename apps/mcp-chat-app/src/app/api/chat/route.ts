/**
 * Gateway-only chat route
 * All LLM processing is handled by the MCP Gateway
 */

import { getSession } from "auth/server";
import { chatRepository } from "lib/db/repository";
import logger from "logger";
import { chatApiSchemaRequestBodySchema } from "app-types/chat";

const GATEWAY_URL = process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8000';
const AUTH_TOKEN = process.env.NEXT_PUBLIC_MCP_AUTH_TOKEN || 'mock-token';

export async function POST(request: Request) {
  try {
    const json = await request.json();
    const session = await getSession();

    if (!session?.user.id) {
      return new Response("Unauthorized", { status: 401 });
    }

    const {
      id,
      message,
      chatModel,
      allowedMcpServers,
      projectId,
    } = chatApiSchemaRequestBodySchema.parse(json);

    // Get or create thread
    let thread = await chatRepository.selectThreadDetails(id);
    
    if (!thread) {
      // Create new thread with simple title
      const title = `Chat ${new Date().toLocaleDateString()}`;
      const newThread = await chatRepository.insertThread({
        id,
        projectId: projectId ?? null,
        title,
        userId: session.user.id,
      });
      thread = await chatRepository.selectThreadDetails(newThread.id);
    }

    if (thread!.userId !== session.user.id) {
      return new Response("Forbidden", { status: 403 });
    }

    // Extract user message text
    const userMessageText = message.parts
      .filter((part: any) => part.type === 'text')
      .map((part: any) => part.text)
      .join(' ');

    // Save user message to database
    await chatRepository.insertMessage({
      threadId: thread!.id,
      model: chatModel?.model ?? null,
      role: "user",
      parts: message.parts,
      attachments: message.experimental_attachments,
      id: message.id,
      annotations: [],
    });

    // Determine which MCP server to use based on the message
    let serverUrl = 'http://localhost:8001/sse'; // Default to Playwright
    let serverId = 'playwright';

    // Simple keyword detection for server selection
    if (userMessageText.toLowerCase().includes('space') || 
        userMessageText.toLowerCase().includes('astronaut') ||
        userMessageText.toLowerCase().includes('mission') ||
        userMessageText.toLowerCase().includes('launch')) {
      serverUrl = 'http://localhost:5001/mcp';
      serverId = 'apollo';
    }

    // Send to MCP Gateway
    const gatewayResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${AUTH_TOKEN}`,
      },
      body: JSON.stringify({
        prompt: userMessageText,
        server_url: serverUrl,
        model_name: chatModel?.model || 'gpt-4',
      }),
    });

    if (!gatewayResponse.ok) {
      const errorText = await gatewayResponse.text();
      throw new Error(`Gateway request failed: ${gatewayResponse.status} - ${errorText}`);
    }

    const gatewayResult = await gatewayResponse.json();

    if (gatewayResult.error) {
      throw new Error(gatewayResult.error);
    }

    // Create assistant message
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage = {
      id: assistantMessageId,
      role: 'assistant' as const,
      parts: [
        {
          type: 'text' as const,
          text: gatewayResult.result,
        }
      ],
      experimental_attachments: [],
      annotations: [
        {
          type: 'gateway-response',
          server_id: serverId,
          server_url: serverUrl,
          usage: gatewayResult.usage,
        }
      ],
    };

    // Save assistant message to database
    await chatRepository.upsertMessage({
      model: chatModel?.model ?? null,
      threadId: thread!.id,
      role: assistantMessage.role,
      id: assistantMessage.id,
      parts: assistantMessage.parts,
      attachments: assistantMessage.experimental_attachments,
      annotations: assistantMessage.annotations,
    });

    // Return streaming response format expected by the UI
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        // Send the assistant message
        const messageData = JSON.stringify({
          type: 'text-delta',
          textDelta: gatewayResult.result,
        });
        controller.enqueue(encoder.encode(`0:${messageData}\n`));

        // Send finish event
        const finishData = JSON.stringify({
          type: 'finish',
          finishReason: 'stop',
          usage: gatewayResult.usage || { promptTokens: 0, completionTokens: 0 },
        });
        controller.enqueue(encoder.encode(`0:${finishData}\n`));

        controller.close();
      },
    });

    return new Response(stream, {
      headers: {
        'Content-Type': 'text/plain; charset=utf-8',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });

  } catch (error: any) {
    logger.error('Gateway chat error:', error);
    return new Response(error.message, { status: 500 });
  }
}