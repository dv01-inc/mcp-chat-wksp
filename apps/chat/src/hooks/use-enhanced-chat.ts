import { useChat, UseChatOptions } from '@ai-sdk/react';
import { getChatApiEndpoint, getChatApiConfig } from '../lib/api/chat-config';
import { useMemo } from 'react';

export interface UseEnhancedChatOptions extends Omit<UseChatOptions, 'api'> {
  api?: string;
  token?: string;
}

export function useEnhancedChat(options: UseEnhancedChatOptions = {}) {
  const config = getChatApiConfig();
  
  // Prepare headers for external API
  const headers = useMemo(() => {
    if (!config.useExternalApi) {
      return options.headers;
    }

    const externalHeaders: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Add auth token if available
    if (options.token) {
      externalHeaders['Authorization'] = `Bearer ${options.token}`;
    }

    return externalHeaders;
  }, [config.useExternalApi, options.headers, options.token]);

  // Determine API endpoint
  const apiEndpoint = options.api || getChatApiEndpoint();

  // Use the enhanced useChat hook
  return useChat({
    ...options,
    api: apiEndpoint,
    headers,
  });
}

// For backward compatibility - components can gradually migrate
export { useEnhancedChat as useChat };