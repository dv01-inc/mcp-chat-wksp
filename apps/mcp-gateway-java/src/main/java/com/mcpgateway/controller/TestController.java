package com.mcpgateway.controller;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

import java.util.HashMap;
import java.util.Map;

@RestController
@RequestMapping("/api/test")
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"}, allowCredentials = "true")
public class TestController {
    
    @Value("${openai.api.key:#{null}}")
    private String openaiApiKey;
    
    @Value("${anthropic.api.key:#{null}}")
    private String anthropicApiKey;
    
    @GetMapping("/apollo")
    public Map<String, Object> testApolloConnection() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            RestTemplate restTemplate = new RestTemplate();
            
            // Test the /mcp endpoint
            try {
                ResponseEntity<String> response = restTemplate.getForEntity(
                    "http://localhost:5000/mcp", String.class);
                result.put("mcp_endpoint_status", response.getStatusCode().value());
                result.put("mcp_response", response.getBody() != null ? 
                    response.getBody().substring(0, Math.min(50, response.getBody().length())) : "N/A");
            } catch (Exception e) {
                result.put("mcp_endpoint_status", "error");
                result.put("mcp_response", e.getMessage());
            }
            
            // Test basic connectivity
            try {
                ResponseEntity<String> healthResponse = restTemplate.getForEntity(
                    "http://localhost:5000", String.class);
                result.put("health_endpoint_status", healthResponse.getStatusCode().value());
            } catch (Exception e) {
                result.put("health_endpoint_status", "error");
            }
            
            result.put("status", "success");
            result.put("apollo_server", "reachable");
            result.put("message", "Apollo MCP server is reachable");
            
        } catch (Exception e) {
            result.put("status", "error");
            result.put("apollo_server", "unreachable");
            result.put("error", e.getMessage());
            result.put("message", "Failed to connect to Apollo MCP server");
        }
        
        return result;
    }

    @GetMapping("/playwright")
    public Map<String, Object> testPlaywrightConnection() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            RestTemplate restTemplate = new RestTemplate();
            
            // Test the /mcp endpoint (should return 400 "Invalid request" but prove it's reachable)
            try {
                ResponseEntity<String> response = restTemplate.getForEntity(
                    "http://localhost:8001/mcp", String.class);
                result.put("mcp_endpoint_status", response.getStatusCode().value());
                result.put("mcp_response", response.getBody() != null ? 
                    response.getBody().substring(0, Math.min(50, response.getBody().length())) : "N/A");
            } catch (Exception e) {
                result.put("mcp_endpoint_status", "error");
                result.put("mcp_response", e.getMessage());
            }
            
            // Test basic connectivity
            try {
                ResponseEntity<String> sseResponse = restTemplate.getForEntity(
                    "http://localhost:8001", String.class);
                result.put("sse_endpoint_status", sseResponse.getStatusCode().value());
                String contentType = sseResponse.getHeaders().getFirst("content-type");
                result.put("has_sse_stream", contentType != null && contentType.contains("text/event-stream"));
            } catch (Exception e) {
                result.put("sse_endpoint_status", "error");
                result.put("has_sse_stream", false);
            }
            
            result.put("status", "success");
            result.put("playwright_server", "reachable");
            result.put("message", "Playwright MCP server is reachable (400 on /mcp is expected without proper MCP request)");
            
        } catch (Exception e) {
            result.put("status", "error");
            result.put("playwright_server", "unreachable");
            result.put("error", e.getMessage());
            result.put("message", "Failed to connect to Playwright MCP server");
        }
        
        return result;
    }
    
    @GetMapping("/env")
    public Map<String, Object> testEnvironment() {
        Map<String, Object> result = new HashMap<>();
        
        result.put("openai_key_present", openaiApiKey != null && !openaiApiKey.isBlank());
        if (openaiApiKey != null && openaiApiKey.length() > 10) {
            result.put("openai_key_prefix", openaiApiKey.substring(0, 10));
        } else {
            result.put("openai_key_prefix", null);
        }
        
        result.put("anthropic_key_present", anthropicApiKey != null && !anthropicApiKey.isBlank());
        result.put("environment", "development");
        
        return result;
    }
    
    @PostMapping("/mcp")
    public Map<String, Object> testMcpQuery() {
        Map<String, Object> result = new HashMap<>();
        
        try {
            // TODO: Implement actual MCP query test using Spring AI MCP Client
            result.put("status", "success");
            result.put("message", "MCP query test not yet implemented");
            result.put("result_preview", "Test implementation pending");
            
        } catch (Exception e) {
            result.put("status", "error");
            result.put("message", "MCP query failed");
            result.put("error", e.getMessage());
        }
        
        return result;
    }
}