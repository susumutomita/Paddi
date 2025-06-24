"""Basic tests for Paddi Web Dashboard."""

import json
import sys
from pathlib import Path

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from web.app import app  # noqa: E402


@pytest.fixture
def client():
    """Create a test client for the Flask app."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_index_route(client):
    """Test that the index route returns the dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"Paddi Security Dashboard" in response.data


def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert "timestamp" in data


def test_get_findings(client):
    """Test getting findings returns mock data."""
    response = client.get("/api/findings")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "findings" in data
    assert "total" in data
    assert "last_updated" in data


def test_severity_distribution(client):
    """Test getting severity distribution data."""
    response = client.get("/api/findings/severity-distribution")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "labels" in data
    assert "data" in data
    assert "colors" in data
    assert len(data["labels"]) == len(data["data"])


def test_timeline_data(client):
    """Test getting timeline data."""
    response = client.get("/api/findings/timeline")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, list)
    assert len(data) == 7  # Should return 7 days of data
    if data:
        assert "date" in data[0]
        assert "critical" in data[0]
        assert "high" in data[0]
        assert "medium" in data[0]
        assert "low" in data[0]


def test_start_audit(client):
    """Test starting a new audit."""
    response = client.post(
        "/api/audit/start", json={"project_id": "test-project"}, content_type="application/json"
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["success"] is True
    assert "audit_id" in data
    assert "message" in data


def test_chat_endpoint(client):
    """Test the chat endpoint."""
    response = client.post(
        "/api/chat",
        json={"question": "What are the main security issues?"},
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "response" in data
    assert "timestamp" in data


def test_export_valid_format(client):
    """Test export with valid format."""
    for format in ["pdf", "markdown", "html"]:
        response = client.get(f"/api/export/{format}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["success"] is True
        assert "message" in data
        assert "download_url" in data


def test_export_invalid_format(client):
    """Test export with invalid format."""
    response = client.get("/api/export/invalid")
    assert response.status_code == 400
    data = json.loads(response.data)
    assert "error" in data


def test_audit_status_not_found(client):
    """Test getting status of non-existent audit."""
    response = client.get("/api/audit/status/non-existent")
    assert response.status_code == 404
    data = json.loads(response.data)
    assert "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
