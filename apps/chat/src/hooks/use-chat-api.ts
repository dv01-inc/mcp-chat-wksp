import { useMemo } from 'react';
import { ChatApiClient } from '../lib/api/chat-api-client';

interface UseChatApiOptions {
  token?: string;
  baseUrl?: string;
}

export function useChatApi(options: UseChatApiOptions = {}) {
  const client = useMemo(() => {
    return new ChatApiClient({
      baseUrl: options.baseUrl || process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:3001',
      token: options.token,
    });
  }, [options.baseUrl, options.token]);

  return client;
}

// For server-side usage
export function createChatApiClient(options: UseChatApiOptions = {}) {
  return new ChatApiClient({
    baseUrl: options.baseUrl || process.env.CHAT_API_URL || 'http://localhost:3001',
    token: options.token,
  });
}