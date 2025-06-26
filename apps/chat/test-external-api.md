# Testing External Chat API Integration

## Quick Test Setup

### 1. Start both services

Terminal 1 - Start the chat-api service:
```bash
npx nx dev chat-api
```

Terminal 2 - Start the Next.js chat app:
```bash
npx nx dev chat
```

### 2. Test internal API (default)

Visit `http://localhost:3000` - should work as normal using internal API routes.

### 3. Test external API

Create `.env.local` in `apps/chat/`:
```bash
NEXT_PUBLIC_USE_EXTERNAL_CHAT_API=true
NEXT_PUBLIC_CHAT_API_URL=http://localhost:3001
```

Restart the chat app and visit `http://localhost:3000` - now it will use the external API.

### 4. Usage Examples

Replace existing chat usage:

**Before:**
```typescript
import { useChat } from '@ai-sdk/react';

const { messages, input, handleSubmit } = useChat({
  api: '/api/chat',
  // ...options
});
```

**After (automatic switching):**
```typescript
import { useEnhancedChat } from '@/hooks/use-enhanced-chat';

const { messages, input, handleSubmit } = useEnhancedChat({
  token: session?.accessToken, // Add auth token
  // ...options
});
```

**Manual API calls:**
```typescript
import { useChatApi } from '@/hooks/use-chat-api';

function MyComponent() {
  const api = useChatApi({ token: session?.accessToken });
  
  const handleChat = async () => {
    const response = await api.chat({
      id: threadId,
      message: userMessage,
      chatModel: selectedModel,
    });
  };
}
```

### 5. Feature Parity Checklist

- ✅ Basic HTTP client created
- ✅ Authentication middleware ready
- ✅ Environment-based switching
- ⏳ Stream handling for chat responses
- ⏳ Error handling integration
- ⏳ Complete API endpoint implementation
- ⏳ Database/MCP integration in chat-api

## Benefits

1. **Gradual Migration**: Switch with env variable
2. **Service Independence**: Chat API can be deployed separately
3. **Scalability**: API service can be scaled independently
4. **Testing**: Easier to test API logic in isolation
5. **Multi-client**: Other clients can use the same API