"""Authentication module for MCP Gateway."""

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
                "sub": "mock-user-id",
                "email": "mock@example.com",
                "exp": datetime.utcnow() + timedelta(hours=1)
            }
        else:
            return verify_token(token)


# Use mock auth in development
if os.getenv("ENVIRONMENT") == "development":
    verify_token = MockAuth.verify_token


def create_user_headers(user_info: Dict[str, Any]) -> Dict[str, str]:
    """Create headers with user information for MCP servers."""
    return {
        "X-User-ID": user_info.get("sub", "anonymous"),
        "X-User-Email": user_info.get("email", ""),
        "X-User-Name": user_info.get("name", ""),
        "Authorization": f"Bearer {user_info.get('token', '')}"
    }