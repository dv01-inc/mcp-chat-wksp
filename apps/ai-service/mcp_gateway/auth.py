"""Authentication module for AI Service.

This module provides multiple authentication strategies:
- JWT-based authentication for direct API access
- Kong gateway authentication for DV01 integration
- Development mock authentication for testing

Features:
- JWT token creation and verification
- Kong header parsing for DV01 auth
- Password hashing with bcrypt
- Development mock authentication
- Automatic environment detection
- User information extraction from tokens/headers

The authentication system automatically switches between:
- Production mode: Full JWT validation with secret keys
- Kong mode: Parse user info from Kong headers (USE_KONG_AUTH=true)
- Development mode: Mock tokens accepted for testing (ENVIRONMENT=development)

Kong Authentication:
When USE_KONG_AUTH=true, the system extracts user info from Kong headers:
- currentuser: Base64 encoded user JSON or plain user ID
- accesstoken: OAuth access token
- currentorg: Current organization ID
"""

import os
from typing import Dict, Any
from fastapi import HTTPException, status
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext


# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: timedelta = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        return payload

    except JWTError:
        raise credentials_exception


class MockAuth:
    """Mock authentication for development/testing."""

    @staticmethod
    def verify_token(token: str) -> Dict[str, Any]:
        """Mock token verification - accepts any token in development."""
        if token == "mock-token" or os.getenv("ENVIRONMENT") == "development":
            return {
                "sub": "550e8400-e29b-41d4-a716-446655440000",  # Mock UUID
                "email": "mock@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1),
            }
        else:
            return verify_token(token)


class KongAuth:
    """Kong gateway authentication for DV01 integration."""

    @staticmethod
    def extract_user_from_headers(headers: Dict[str, str]) -> Dict[str, Any]:
        """Extract user info from Kong headers."""
        current_user = headers.get("currentuser")
        access_token = headers.get("accesstoken")
        current_org = headers.get("currentorg")

        if current_user:
            # Parse currentuser header (usually base64 encoded JSON)
            try:
                import json
                import base64

                user_data = json.loads(base64.b64decode(current_user).decode())
                return {
                    "sub": user_data.get("id")
                    or user_data.get("sub")
                    or user_data.get("userId"),
                    "email": user_data.get("email"),
                    "name": user_data.get("name") or user_data.get("fullName"),
                    "org": current_org,
                    "access_token": access_token,
                }
            except Exception:
                # Fallback if header format is different - treat as plain user ID
                return {
                    "sub": current_user,
                    "email": f"{current_user}@dv01.co",
                    "name": current_user,
                    "org": current_org,
                    "access_token": access_token,
                }

        return None


# Use mock auth in development
if os.getenv("ENVIRONMENT") == "development":
    verify_token = MockAuth.verify_token


def create_user_headers(user_info: Dict[str, Any]) -> Dict[str, str]:
    """Create headers with user information for MCP servers."""
    return {
        "X-User-ID": user_info.get("sub", "anonymous"),
        "X-User-Email": user_info.get("email", ""),
        "X-User-Name": user_info.get("name", ""),
        "Authorization": f"Bearer {user_info.get('token', '')}",
    }
