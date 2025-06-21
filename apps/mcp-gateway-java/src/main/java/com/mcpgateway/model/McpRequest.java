package com.mcpgateway.model;

import jakarta.validation.constraints.NotBlank;
import java.util.Map;

public record McpRequest(
    @NotBlank(message = "Prompt is required")
    String prompt,
    
    @NotBlank(message = "Server URL is required")
    String serverUrl,
    
    Map<String, String> serverAuth,
    String modelName,
    String systemPrompt
) {
    public McpRequest {
        if (modelName == null || modelName.isBlank()) {
            modelName = "openai:gpt-4.1";
        }
    }
}