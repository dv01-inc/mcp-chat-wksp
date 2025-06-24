"""MCP Gateway unit test module."""

from fastapi.testclient import TestClient
from mcp_gateway.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "mcp-gateway"}


def test_root_endpoint():
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "MCP Gateway Service is running" in response.json()["message"]
