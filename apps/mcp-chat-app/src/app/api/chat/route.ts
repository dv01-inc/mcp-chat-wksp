/**
 * AI Service chat route
 * All LLM processing is handled by the AI Service
 */

import { getSession } from "auth/server";
import logger from "logger";
import { chatApiSchemaRequestBodySchema } from "app-types/chat";

const AI_SERVICE_URL = process.env.NEXT_PUBLIC_AI_SERVICE_URL || process.env.NEXT_PUBLIC_MCP_GATEWAY_URL || 'http://localhost:8000';
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

    // Get or create thread via gateway
    let thread;
    try {
      const threadResponse = await fetch(`${GATEWAY_URL}/chat/threads/${id}`, {
        headers: {
          'Authorization': `Bearer ${AUTH_TOKEN}`,
        },
      });
      
      if (threadResponse.ok) {
        thread = await threadResponse.json();
      } else if (threadResponse.status === 404) {
        // Create new thread
        const title = `Chat ${new Date().toLocaleDateString()}`;
        const createResponse = await fetch(`${GATEWAY_URL}/chat/threads`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${AUTH_TOKEN}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            thread_id: id,
            title,
            project_id: projectId ?? null,
          }),
        });
        
        if (!createResponse.ok) {
          throw new Error(`Failed to create thread: ${createResponse.status}`);
        }
        
        thread = await createResponse.json();
      } else {
        throw new Error(`Failed to get thread: ${threadResponse.status}`);
      }
    } catch (error: any) {
      logger.error('Failed to handle thread:', error);
      return new Response("Failed to handle thread", { status: 500 });
    }

    if (thread.user_id !== session.user.id) {
      return new Response("Forbidden", { status: 403 });
    }

    // Extract user message text
    const userMessageText = message.parts
      .filter((part: any) => part.type === 'text')
      .map((part: any) => part.text)
      .join(' ');

    // Map model names to proper format for Pydantic AI
    const modelMapping: Record<string, string> = {
      'gpt-4': 'openai:gpt-4',
      'gpt-4o': 'openai:gpt-4o',
      'gpt-4o-mini': 'openai:gpt-4o-mini',
      '4o-mini': 'openai:gpt-4o-mini',
      'gpt-3.5-turbo': 'openai:gpt-3.5-turbo',
      'claude-3-5-sonnet-20241022': 'anthropic:claude-3-5-sonnet-20241022',
      'claude-3-haiku-20240307': 'anthropic:claude-3-haiku-20240307',
    };

    const rawModel = chatModel?.model || 'gpt-4';
    const mappedModel = modelMapping[rawModel] || `openai:${rawModel}`;

    // Send to intelligent MCP Gateway - it handles all tool selection and orchestration
    const gatewayResponse = await fetch(`${GATEWAY_URL}/mcp/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${AUTH_TOKEN}`,
      },
      body: JSON.stringify({
        prompt: userMessageText,
        model_name: mappedModel,
        thread_id: id,
        message_id: message.id,
        // AI Service handles everything: LLM processing, server selection, tool choice, and chat history!
      }),
    });

    if (!aiServiceResponse.ok) {
      const errorText = await aiServiceResponse.text();
      throw new Error(`AI Service request failed: ${aiServiceResponse.status} - ${errorText}`);
    }

    const aiServiceResult = await aiServiceResponse.json();

    if (aiServiceResult.error) {
      throw new Error(aiServiceResult.error);
    }

    // AI Service has saved both user and assistant messages
    // We just need to return the streaming response with the assistant message content

    // Return AI SDK compatible streaming response
    // We need to format the response so useChat can process it
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        try {
          const text = aiServiceResult.result;
          
          // Send text in chunks (simulating streaming)
          const chunkSize = 10;
          for (let i = 0; i < text.length; i += chunkSize) {
            const chunk = text.slice(i, i + chunkSize);
            // Format: "0:{\"type\":\"text-delta\",\"textDelta\":\"chunk\"}\n"
            const data = JSON.stringify({
              type: 'text-delta',
              textDelta: chunk,
            });
            controller.enqueue(encoder.encode(`0:${data}\n`));
          }

          // Send finish event
          const finishData = JSON.stringify({
            type: 'finish',
            finishReason: 'stop',
            usage: {
              promptTokens: aiServiceResult.usage?.prompt_tokens || 0,
              completionTokens: aiServiceResult.usage?.completion_tokens || 0,
            },
          });
          controller.enqueue(encoder.encode(`0:${finishData}\n`));

          controller.close();
        } catch (error) {
          controller.error(error);
        }
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