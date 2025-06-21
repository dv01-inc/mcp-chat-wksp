package com.mcpgateway.model;

import java.util.Map;

public record McpResponse(
    String result,
    Map<String, Object> usage,
    String error
) {
    public static McpResponse success(String result, Map<String, Object> usage) {
        return new McpResponse(result, usage, null);
    }
    
    public static McpResponse error(String error) {
        return new McpResponse(null, null, error);
    }
}