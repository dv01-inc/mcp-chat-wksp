package com.mcpgateway.service;

import com.mcpgateway.model.McpRequest;
import com.mcpgateway.model.McpResponse;
import com.mcpgateway.model.UserInfo;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Service
public class McpClientService {
    
    private final Map<String, Object> mcpClients = new ConcurrentHashMap<>();
    
    @Value("${openai.api.key:#{null}}")
    private String openaiApiKey;
    
    @Value("${anthropic.api.key:#{null}}")
    private String anthropicApiKey;
    
    public McpResponse executeQuery(McpRequest request, UserInfo userInfo) {
        try {
            // For now, return a mock response since Spring AI MCP Client is not available
            // TODO: Implement actual MCP client integration when Spring AI MCP Client is available
            
            String clientKey = generateClientKey(request.serverUrl(), userInfo.sub());
            String message = buildMessage(request, userInfo);
            
            // Mock response for demonstration
            String result = "Mock MCP response for query: " + request.prompt() + 
                          "\nServer: " + request.serverUrl() + 
                          "\nUser: " + userInfo.sub();
            
            Map<String, Object> usage = new HashMap<>();
            usage.put("requests", 1);
            usage.put("total_tokens", message.length());
            
            return McpResponse.success(result, usage);
            
        } catch (Exception e) {
            return McpResponse.error("MCP query failed: " + e.getMessage());
        }
    }
    
    public McpResponse executeChat(McpRequest request, UserInfo userInfo) {
        try {
            String clientKey = generateClientKey(request.serverUrl(), userInfo.sub());
            String message = buildMessage(request, userInfo);
            
            // Mock response for demonstration
            String result = "Mock MCP chat response for: " + request.prompt() + 
                          "\nServer: " + request.serverUrl() + 
                          "\nUser: " + userInfo.sub() +
                          "\nModel: " + request.modelName();
            
            Map<String, Object> usage = new HashMap<>();
            usage.put("requests", 1);
            usage.put("total_tokens", message.length());
            
            return McpResponse.success(result, usage);
            
        } catch (Exception e) {
            return McpResponse.error("MCP chat failed: " + e.getMessage());
        }
    }
    
    public Map<String, Object> listUserServers(UserInfo userInfo) {
        Map<String, Object> servers = new HashMap<>();
        
        // Mock server list for demonstration
        Map<String, String> mockServer = new HashMap<>();
        mockServer.put("server_url", "http://localhost:8001/mcp");
        mockServer.put("status", "connected");
        
        servers.put("servers", java.util.List.of(mockServer));
        return servers;
    }
    
    public boolean disconnectServer(String serverId, UserInfo userInfo) {
        String clientKey = generateClientKey(serverId, userInfo.sub());
        // Mock disconnection
        return true;
    }
    
    private String buildMessage(McpRequest request, UserInfo userInfo) {
        StringBuilder message = new StringBuilder();
        
        if (request.systemPrompt() != null && !request.systemPrompt().isBlank()) {
            message.append("System: ").append(request.systemPrompt()).append("\n\n");
        }
        
        message.append("User: ").append(request.prompt());
        
        // Add user context
        message.append("\n\nContext: User ID: ").append(userInfo.sub());
        if (userInfo.email() != null && !userInfo.email().isBlank()) {
            message.append(", Email: ").append(userInfo.email());
        }
        
        return message.toString();
    }
    
    private String generateClientKey(String serverUrl, String userId) {
        return serverUrl + ":" + userId;
    }
}