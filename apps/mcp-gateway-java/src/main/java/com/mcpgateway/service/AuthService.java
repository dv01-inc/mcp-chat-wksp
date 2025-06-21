package com.mcpgateway.service;

import com.mcpgateway.model.UserInfo;
import org.springframework.stereotype.Service;

@Service
public class AuthService {
    
    private static final String DEVELOPMENT_TOKEN = "mock-token";
    
    public UserInfo verifyToken(String token) {
        if (token == null || token.isBlank()) {
            throw new SecurityException("Token is required");
        }
        
        // In development mode, accept mock token
        if (DEVELOPMENT_TOKEN.equals(token)) {
            return new UserInfo("dev-user", "dev@example.com", "Development User");
        }
        
        // TODO: Implement real JWT verification for production
        // For now, return anonymous user for any other token
        return UserInfo.anonymous();
    }
    
    public boolean isValidToken(String token) {
        try {
            verifyToken(token);
            return true;
        } catch (SecurityException e) {
            return false;
        }
    }
}