"""Database models and setup for MCP Gateway using SQLAlchemy.

This module defines the database schema and repository classes for the MCP Gateway.
It provides a complete data layer for chat history, user management, and MCP server
configurations using PostgreSQL as the primary database.

Key Components:
- SQLAlchemy models for all data entities
- Repository pattern for data access
- Database connection management with retry logic
- Support for both SQLite (development) and PostgreSQL (production)

Models:
- User: User accounts and authentication
- Session: JWT session management
- Project: Optional chat organization
- ChatThread: Chat conversation containers
- ChatMessage: Individual messages with rich content
- MCPServer: MCP server configurations

The database automatically handles:
- UUID primary keys for all entities
- Timestamps for creation and updates
- Foreign key relationships and cascading deletes
- JSON columns for flexible data storage
"""

import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    JSON,
    String,
    Text,
    create_engine,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func

# Database URL from environment - default to SQLite for development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mcp_gateway.db")

# SQLAlchemy setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Database Models


class User(Base):
    """User model."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    password = Column(String)
    image = Column(String)
    preferences = Column(JSON, default={})
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    threads = relationship(
        "ChatThread", back_populates="user", cascade="all, delete-orphan"
    )
    projects = relationship(
        "Project", back_populates="user", cascade="all, delete-orphan"
    )
    sessions = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )


class Session(Base):
    """Session model for authentication."""

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="sessions")


class Project(Base):
    """Project model."""

    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    instructions = Column(JSON)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationships
    user = relationship("User", back_populates="projects")
    threads = relationship(
        "ChatThread", back_populates="project", cascade="all, delete-orphan"
    )


class ChatThread(Base):
    """Chat thread model."""

    __tablename__ = "chat_threads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    project_id = Column(
        UUID(as_uuid=True), ForeignKey("projects.id", ondelete="SET NULL")
    )

    # Relationships
    user = relationship("User", back_populates="threads")
    project = relationship("Project", back_populates="threads")
    messages = relationship(
        "ChatMessage", back_populates="thread", cascade="all, delete-orphan"
    )


class ChatMessage(Base):
    """Chat message model."""

    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True)
    role = Column(String, nullable=False)  # 'user' or 'assistant'
    parts = Column(JSON, nullable=False)  # Array of message parts
    attachments = Column(JSON)  # Array of attachments
    annotations = Column(JSON)  # Array of annotations
    model = Column(String)  # Model used for generation
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Foreign keys
    thread_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_threads.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    thread = relationship("ChatThread", back_populates="messages")


class MCPServer(Base):
    """MCP Server configuration model."""

    __tablename__ = "mcp_servers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, nullable=False)
    config = Column(JSON, nullable=False)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all database tables."""
    Base.metadata.drop_all(bind=engine)


# Repository Functions


class ChatRepository:
    """Repository for chat operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_thread(self, thread_id: str, user_id: str) -> Optional[ChatThread]:
        """Get a chat thread by ID for a specific user."""
        return (
            self.db.query(ChatThread)
            .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
            .first()
        )

    def get_thread_with_messages(
        self, thread_id: str, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get a chat thread with its messages for a specific user."""
        thread = (
            self.db.query(ChatThread)
            .filter(ChatThread.id == thread_id, ChatThread.user_id == user_id)
            .first()
        )

        if not thread:
            return None

        messages = (
            self.db.query(ChatMessage)
            .filter(ChatMessage.thread_id == thread_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

        return {
            "id": str(thread.id),
            "title": thread.title,
            "user_id": str(thread.user_id),
            "project_id": str(thread.project_id) if thread.project_id else None,
            "created_at": thread.created_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "parts": msg.parts,
                    "attachments": msg.attachments,
                    "annotations": msg.annotations,
                    "model": msg.model,
                    "created_at": msg.created_at.isoformat(),
                }
                for msg in messages
            ],
        }

    def get_user_threads(self, user_id: str) -> List[Dict[str, Any]]:
        """Get all threads for a user with last message timestamp."""
        from sqlalchemy import desc, func

        # Get threads with last message timestamp
        threads = (
            self.db.query(
                ChatThread, func.max(ChatMessage.created_at).label("last_message_at")
            )
            .outerjoin(ChatMessage, ChatThread.id == ChatMessage.thread_id)
            .filter(ChatThread.user_id == user_id)
            .group_by(ChatThread.id)
            .order_by(desc("last_message_at"))
            .all()
        )

        return [
            {
                "id": str(thread.ChatThread.id),
                "title": thread.ChatThread.title,
                "user_id": str(thread.ChatThread.user_id),
                "project_id": str(thread.ChatThread.project_id)
                if thread.ChatThread.project_id
                else None,
                "created_at": thread.ChatThread.created_at.isoformat(),
                "last_message_at": thread.last_message_at.isoformat()
                if thread.last_message_at
                else None,
            }
            for thread in threads
        ]

    def create_thread(
        self,
        user_id: str,
        title: str,
        project_id: Optional[str] = None,
        thread_id: Optional[str] = None,
    ) -> ChatThread:
        """Create a new chat thread."""
        thread = ChatThread(
            id=thread_id if thread_id else uuid4(),
            title=title,
            user_id=user_id,
            project_id=project_id,
        )
        self.db.add(thread)
        self.db.commit()
        self.db.refresh(thread)
        return thread

    def update_thread(
        self, thread_id: str, user_id: str, **updates
    ) -> Optional[ChatThread]:
        """Update a chat thread."""
        thread = self.get_thread(thread_id, user_id)
        if not thread:
            return None

        for key, value in updates.items():
            if hasattr(thread, key):
                setattr(thread, key, value)

        self.db.commit()
        self.db.refresh(thread)
        return thread

    def delete_thread(self, thread_id: str, user_id: str) -> bool:
        """Delete a chat thread and all its messages."""
        thread = self.get_thread(thread_id, user_id)
        if not thread:
            return False

        self.db.delete(thread)
        self.db.commit()
        return True

    def add_message(
        self,
        thread_id: str,
        message_id: str,
        role: str,
        parts: List[Any],
        attachments: Optional[List[Any]] = None,
        annotations: Optional[List[Any]] = None,
        model: Optional[str] = None,
    ) -> ChatMessage:
        """Add a message to a chat thread."""
        message = ChatMessage(
            id=message_id,
            thread_id=thread_id,
            role=role,
            parts=parts,
            attachments=attachments or [],
            annotations=annotations or [],
            model=model,
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def upsert_message(
        self,
        thread_id: str,
        message_id: str,
        role: str,
        parts: List[Any],
        attachments: Optional[List[Any]] = None,
        annotations: Optional[List[Any]] = None,
        model: Optional[str] = None,
    ) -> ChatMessage:
        """Insert or update a message."""
        existing = (
            self.db.query(ChatMessage).filter(ChatMessage.id == message_id).first()
        )

        if existing:
            existing.parts = parts
            existing.attachments = attachments or []
            existing.annotations = annotations or []
            existing.model = model
            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            return self.add_message(
                thread_id, message_id, role, parts, attachments, annotations, model
            )


class UserRepository:
    """Repository for user operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()

    def create_user(self, name: str, email: str, id: str = None, **kwargs) -> User:
        """Create a new user."""
        user_data = {"name": name, "email": email, **kwargs}
        if id:
            user_data["id"] = id

        user = User(**user_data)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


class MCPServerRepository:
    """Repository for MCP server operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_servers(self) -> List[MCPServer]:
        """Get all MCP servers."""
        return self.db.query(MCPServer).filter(MCPServer.enabled == True).all()

    def get_server_by_id(self, server_id: str) -> Optional[MCPServer]:
        """Get MCP server by ID."""
        return self.db.query(MCPServer).filter(MCPServer.id == server_id).first()

    def get_server_by_name(self, name: str) -> Optional[MCPServer]:
        """Get MCP server by name."""
        return self.db.query(MCPServer).filter(MCPServer.name == name).first()

    def create_server(
        self, name: str, config: Dict[str, Any], enabled: bool = True
    ) -> MCPServer:
        """Create a new MCP server configuration."""
        server = MCPServer(name=name, config=config, enabled=enabled)
        self.db.add(server)
        self.db.commit()
        self.db.refresh(server)
        return server

    def update_server(self, server_id: str, **updates) -> Optional[MCPServer]:
        """Update an MCP server configuration."""
        server = self.get_server_by_id(server_id)
        if not server:
            return None

        for key, value in updates.items():
            if hasattr(server, key):
                setattr(server, key, value)

        self.db.commit()
        self.db.refresh(server)
        return server

    def delete_server(self, server_id: str) -> bool:
        """Delete an MCP server configuration."""
        server = self.get_server_by_id(server_id)
        if not server:
            return False

        self.db.delete(server)
        self.db.commit()
        return True

    def enable_server(self, server_id: str) -> bool:
        """Enable an MCP server."""
        return self.update_server(server_id, enabled=True) is not None

    def disable_server(self, server_id: str) -> bool:
        """Disable an MCP server."""
        return self.update_server(server_id, enabled=False) is not None
