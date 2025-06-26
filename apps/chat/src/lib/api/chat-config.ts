/**
 * Configuration for chat API - can switch between internal Next.js API and external service
 */

export interface ChatApiConfig {
  useExternalApi: boolean;
  externalApiUrl: string;
  token?: string;
}

export function getChatApiConfig(): ChatApiConfig {
  const useExternalApi = process.env.NEXT_PUBLIC_USE_EXTERNAL_CHAT_API === 'true';
  const externalApiUrl = process.env.NEXT_PUBLIC_CHAT_API_URL || 'http://localhost:3001';
  
  return {
    useExternalApi,
    externalApiUrl,
  };
}

export function getChatApiEndpoint(): string {
  const config = getChatApiConfig();
  
  if (config.useExternalApi) {
    return `${config.externalApiUrl}/api/chat`;
  }
  
  // Use internal Next.js API route
  return '/api/chat';
}

export function getApiEndpoint(path: string): string {
  const config = getChatApiConfig();
  
  if (config.useExternalApi) {
    return `${config.externalApiUrl}${path}`;
  }
  
  // Use internal Next.js API route
  return path;
}