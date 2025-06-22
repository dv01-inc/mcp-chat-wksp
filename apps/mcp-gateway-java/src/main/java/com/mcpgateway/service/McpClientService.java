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
    
    @Value("${spring.ai.mcp.client.sse.connections.apollo.url:http://localhost:5000}")
    private String apolloServerUrl;
    
    @Value("${spring.ai.mcp.client.sse.connections.playwright.url:http://localhost:8001}")
    private String playwrightServerUrl;
    
    public McpResponse executeQuery(McpRequest request, UserInfo userInfo) {
        try {
            String clientKey = generateClientKey(request.serverUrl(), userInfo.sub());
            String message = buildMessage(request, userInfo);
            
            // Enhanced mock response with server-specific behavior
            String result = generateMockResponse(request, userInfo);
            
            Map<String, Object> usage = new HashMap<>();
            usage.put("requests", 1);
            usage.put("server_url", request.serverUrl());
            usage.put("user_id", userInfo.sub());
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
            
            // Enhanced mock response for chat
            String result = generateMockChatResponse(request, userInfo);
            
            Map<String, Object> usage = new HashMap<>();
            usage.put("requests", 1);
            usage.put("server_url", request.serverUrl());
            usage.put("user_id", userInfo.sub());
            usage.put("model_name", request.modelName());
            usage.put("total_tokens", message.length());
            
            return McpResponse.success(result, usage);
            
        } catch (Exception e) {
            return McpResponse.error("MCP chat failed: " + e.getMessage());
        }
    }
    
    public Map<String, Object> listUserServers(UserInfo userInfo) {
        Map<String, Object> result = new HashMap<>();
        
        // Mock server list with Apollo and Playwright servers
        Map<String, Object> apolloServer = new HashMap<>();
        apolloServer.put("server_url", apolloServerUrl);
        apolloServer.put("status", "available");
        apolloServer.put("type", "apollo");
        apolloServer.put("tools", java.util.List.of("get_space_data", "search_missions", "get_astronaut_info"));
        
        Map<String, Object> playwrightServer = new HashMap<>();
        playwrightServer.put("server_url", playwrightServerUrl);
        playwrightServer.put("status", "available");
        playwrightServer.put("type", "playwright");
        playwrightServer.put("tools", java.util.List.of("playwright_navigate", "playwright_screenshot", "playwright_click"));
        
        result.put("servers", java.util.List.of(apolloServer, playwrightServer));
        result.put("user_id", userInfo.sub());
        
        return result;
    }
    
    public boolean disconnectServer(String serverId, UserInfo userInfo) {
        String clientKey = generateClientKey(serverId, userInfo.sub());
        // Mock disconnection - always returns true
        return true;
    }
    
    private String generateMockResponse(McpRequest request, UserInfo userInfo) {
        String serverType = getServerType(request.serverUrl());
        
        switch (serverType) {
            case "apollo":
                return generateApolloMockResponse(request);
            case "playwright":
                return generatePlaywrightMockResponse(request);
            default:
                return "Mock MCP response for query: " + request.prompt() + 
                      "\nServer: " + request.serverUrl() + 
                      "\nUser: " + userInfo.sub();
        }
    }
    
    private String generateMockChatResponse(McpRequest request, UserInfo userInfo) {
        String serverType = getServerType(request.serverUrl());
        
        switch (serverType) {
            case "apollo":
                return "Apollo Space Data: Based on your query '" + request.prompt() + 
                      "', here's some space mission information. Current ISS position: Lat 45.2° Long -122.3°. " +
                      "Next visible pass over your location in 2 hours.";
            case "playwright":
                return "Playwright Automation: I can help you automate web interactions for '" + request.prompt() + 
                      "'. Available actions: navigate to pages, take screenshots, click elements, fill forms.";
            default:
                return "Mock MCP chat response for: " + request.prompt() + 
                      "\nServer: " + request.serverUrl() + 
                      "\nUser: " + userInfo.sub() +
                      "\nModel: " + request.modelName();
        }
    }
    
    private String generateApolloMockResponse(McpRequest request) {
        return "Apollo Space Data Response:\n" +
               "Query: " + request.prompt() + "\n" +
               "ISS Current Position: Latitude 51.505°, Longitude -0.09°\n" +
               "Altitude: 408 km\n" +
               "Velocity: 7.66 km/s\n" +
               "Current Crew: 7 astronauts\n" +
               "Next Mission: Artemis III (planned 2026)";
    }
    
    private String generatePlaywrightMockResponse(McpRequest request) {
        return "Playwright Browser Automation Response:\n" +
               "Action: " + request.prompt() + "\n" +
               "Browser: Chromium\n" +
               "Status: Ready\n" +
               "Available Tools: navigate, screenshot, click, type, wait\n" +
               "Current Page: about:blank\n" +
               "Viewport: 1280x720";
    }
    
    private String getServerType(String serverUrl) {
        if (serverUrl.contains("5000") || serverUrl.equals(apolloServerUrl)) {
            return "apollo";
        } else if (serverUrl.contains("8001") || serverUrl.equals(playwrightServerUrl)) {
            return "playwright";
        }
        return "unknown";
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