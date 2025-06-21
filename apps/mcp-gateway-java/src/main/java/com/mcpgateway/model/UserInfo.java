package com.mcpgateway.model;

public record UserInfo(
    String sub,
    String email,
    String name
) {
    public static UserInfo anonymous() {
        return new UserInfo("anonymous", "", "Anonymous User");
    }
}