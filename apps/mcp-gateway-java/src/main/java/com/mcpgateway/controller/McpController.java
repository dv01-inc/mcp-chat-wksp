package com.mcpgateway.controller;

import com.mcpgateway.model.McpRequest;
import com.mcpgateway.model.McpResponse;
import com.mcpgateway.model.UserInfo;
import com.mcpgateway.service.AuthService;
import com.mcpgateway.service.McpClientService;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/api")
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"}, allowCredentials = "true")
public class McpController {
    
    @Autowired
    private McpClientService mcpClientService;
    
    @Autowired
    private AuthService authService;
    
    @GetMapping("/")
    public Map<String, String> root() {
        return Map.of("message", "MCP Gateway Java Service is running");
    }
    
    @GetMapping("/health")
    public Map<String, String> health() {
        return Map.of(
            "status", "healthy",
            "service", "mcp-gateway-java"
        );
    }
    
    @PostMapping("/mcp/query")
    public ResponseEntity<McpResponse> mcpQuery(
            @Valid @RequestBody McpRequest request,
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            UserInfo userInfo = extractUserInfo(authHeader);
            McpResponse response = mcpClientService.executeQuery(request, userInfo);
            return ResponseEntity.ok(response);
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(McpResponse.error("Authentication failed: " + e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(McpResponse.error("Internal server error: " + e.getMessage()));
        }
    }
    
    @PostMapping("/mcp/chat")
    public ResponseEntity<McpResponse> mcpChat(
            @Valid @RequestBody McpRequest request,
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            UserInfo userInfo = extractUserInfo(authHeader);
            McpResponse response = mcpClientService.executeChat(request, userInfo);
            return ResponseEntity.ok(response);
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(McpResponse.error("Authentication failed: " + e.getMessage()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(McpResponse.error("Internal server error: " + e.getMessage()));
        }
    }
    
    @GetMapping("/mcp/servers")
    public ResponseEntity<Map<String, Object>> listMcpServers(
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            UserInfo userInfo = extractUserInfo(authHeader);
            Map<String, Object> servers = mcpClientService.listUserServers(userInfo);
            return ResponseEntity.ok(servers);
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
    }
    
    @DeleteMapping("/mcp/servers/{serverId}")
    public ResponseEntity<Map<String, String>> disconnectMcpServer(
            @PathVariable String serverId,
            @RequestHeader("Authorization") String authHeader) {
        
        try {
            UserInfo userInfo = extractUserInfo(authHeader);
            boolean disconnected = mcpClientService.disconnectServer(serverId, userInfo);
            
            if (disconnected) {
                return ResponseEntity.ok(Map.of("message", "Disconnected from server " + serverId));
            } else {
                return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(Map.of("error", "Server not found"));
            }
        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }
    }
    
    private UserInfo extractUserInfo(String authHeader) {
        if (authHeader == null || !authHeader.startsWith("Bearer ")) {
            throw new SecurityException("Invalid authorization header");
        }
        
        String token = authHeader.substring(7); // Remove "Bearer " prefix
        return authService.verifyToken(token);
    }
}