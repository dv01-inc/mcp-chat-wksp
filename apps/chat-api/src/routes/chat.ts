import { Router } from 'express';
import { asyncHandler, createError } from '../middleware/error-handler.js';
import {
  appendResponseMessages,
  createDataStreamResponse,
  smoothStream,
  streamText,
  type UIMessage,
  formatDataStreamPart,
  appendClientMessage,
  Message,
} from "ai";
import { anthropic } from '@ai-sdk/anthropic';
import { openai } from '@ai-sdk/openai';
import { google } from '@ai-sdk/google';
import { xai } from '@ai-sdk/xai';
import { chatRepository } from '../lib/repositories.js';
import type { MCPClientsManager } from '../lib/mcp-manager.js';

const router = Router();

// POST /api/chat - Main chat endpoint
router.post('/', asyncHandler(async (req, res) => {
  const session = req.user;
  
  if (!session?.id) {
    throw createError('Unauthorized', 401);
  }

  const {
    messages,
    model = 'claude-3-5-sonnet-20241022',
    threadId,
    projectId,
    allowedMcpServers = [],
  } = req.body;

  if (!messages || !Array.isArray(messages)) {
    throw createError('Messages array is required', 400);
  }

  // Get MCP manager from app locals
  const mcpManager = req.app.locals.mcpManager as MCPClientsManager;
  
  // Get available tools from MCP clients
  const mcpTools = mcpManager.isReady() ? mcpManager.tools() : {};

  // Select model provider
  let modelProvider;
  if (model.startsWith('claude-')) {
    modelProvider = anthropic(model);
  } else if (model.startsWith('gpt-')) {
    modelProvider = openai(model);
  } else if (model.startsWith('gemini-')) {
    modelProvider = google(model);
  } else if (model.startsWith('grok-')) {
    modelProvider = xai(model);
  } else {
    modelProvider = anthropic('claude-3-5-sonnet-20241022'); // fallback
  }

  try {
    const result = await streamText({
      model: modelProvider,
      messages: messages as Message[],
      tools: mcpTools,
      onStepFinish: async (step) => {
        // Log tool calls for debugging
        if (step.toolCalls?.length > 0) {
          console.log('🔧 Tool calls:', step.toolCalls.map(t => t.toolName));
        }
      },
      onFinish: async (result) => {
        // Save conversation to database if threadId provided
        if (threadId) {
          try {
            // Save user message
            const lastMessage = messages[messages.length - 1];
            if (lastMessage) {
              await chatRepository.createMessage({
                threadId,
                content: typeof lastMessage.content === 'string' ? lastMessage.content : JSON.stringify(lastMessage.content),
                role: 'user',
                userId: session.id,
              });
            }

            // Save assistant response
            await chatRepository.createMessage({
              threadId,
              content: result.text,
              role: 'assistant',
              userId: session.id,
              toolInvocations: result.toolCalls || [],
            });
          } catch (error) {
            console.error('Failed to save chat messages:', error);
          }
        }
      },
    });

    // Set up streaming response headers
    res.setHeader('Content-Type', 'text/plain; charset=utf-8');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    // Stream the response
    for await (const chunk of result.textStream) {
      res.write(chunk);
    }
    
    res.end();
  } catch (error) {
    console.error('Chat streaming error:', error);
    res.status(500).json({ error: 'Failed to generate response' });
  }
}));

// GET /api/chat/models - Get available models
router.get('/models', asyncHandler(async (req, res) => {
  // Implementation for models endpoint
  res.json({ models: [] });
}));

// POST /api/chat/summarize - Summarize chat
router.post('/summarize', asyncHandler(async (req, res) => {
  // Implementation for summarize endpoint
  res.json({ summary: 'Not implemented' });
}));

// POST /api/chat/temporary - Temporary chat
router.post('/temporary', asyncHandler(async (req, res) => {
  // Implementation for temporary chat endpoint
  res.json({ message: 'Temporary chat - not implemented' });
}));

// POST /api/chat/:threadId - Chat with specific thread
router.post('/:threadId', asyncHandler(async (req, res) => {
  const { threadId } = req.params;
  // Implementation for thread-specific chat
  res.json({ threadId, message: 'Thread chat - not implemented' });
}));

export { router as chatRoutes };