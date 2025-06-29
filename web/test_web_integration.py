"""Integration tests for Web API with real agents."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.append(str(Path(__file__).parent.parent))

from web.app import app  # noqa: E402


class TestWebIntegration(unittest.TestCase):
    """Test Web API integration with agents."""

    def setUp(self):
        """Set up test client."""
        self.app = app
        self.app.config["TESTING"] = True
        self.client = self.app.test_client()

        # Create temp directories for test data
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.output_dir = Path(self.temp_dir) / "output"
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "healthy")

    @patch("web.app.agent_manager")
    @patch("web.app.async_executor")
    def test_start_audit(self, mock_executor, mock_manager):
        """Test starting an audit."""
        # Mock the agent manager response
        mock_manager.start_audit.return_value = "audit-12345"

        # Start audit
        response = self.client.post(
            "/api/audit/start",
            json={"project_id": "test-project", "use_mock": True},
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertTrue(data["success"])
        self.assertEqual(data["audit_id"], "audit-12345")

        # Verify agent manager was called
        mock_manager.start_audit.assert_called_once()
        mock_executor.submit_audit.assert_called_once()

    @patch("web.app.agent_manager")
    def test_get_audit_status(self, mock_manager):
        """Test getting audit status."""
        # Mock audit status
        mock_audit = {
            "id": "audit-12345",
            "project_id": "test-project",
            "status": "completed",
            "started_at": "2025-01-01T00:00:00",
            "completed_at": "2025-01-01T00:05:00",
        }
        mock_manager.get_audit_status.return_value = mock_audit

        # Get status
        response = self.client.get("/api/audit/status/audit-12345")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["id"], "audit-12345")
        self.assertEqual(data["status"], "completed")

    @patch("web.app.agent_manager")
    def test_get_findings_with_data(self, mock_manager):
        """Test getting findings when data exists."""
        # Mock findings data
        mock_findings = {
            "findings": [
                {
                    "title": "Test Finding",
                    "severity": "HIGH",
                    "explanation": "Test explanation",
                    "recommendation": "Test recommendation",
                }
            ],
            "total": 1,
            "severity_distribution": {"HIGH": 1, "MEDIUM": 0, "LOW": 0},
            "last_updated": "2025-01-01T00:00:00",
        }
        mock_manager.get_findings.return_value = mock_findings

        # Get findings
        response = self.client.get("/api/findings")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["findings"]), 1)

    @patch("web.app.agent_manager")
    def test_get_findings_no_data(self, mock_manager):
        """Test getting findings when no data exists."""
        # Mock no findings
        mock_manager.get_findings.return_value = None

        # Get findings - should return mock data
        response = self.client.get("/api/findings")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertGreater(data["total"], 0)  # Should have mock findings

    @patch("web.app.agent_manager")
    def test_severity_distribution(self, mock_manager):
        """Test getting severity distribution."""
        # Mock findings with distribution
        mock_findings = {
            "severity_distribution": {
                "CRITICAL": 2,
                "HIGH": 5,
                "MEDIUM": 10,
                "LOW": 15,
            }
        }
        mock_manager.get_findings.return_value = mock_findings

        # Get distribution
        response = self.client.get("/api/findings/severity-distribution")
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["data"], [2, 5, 10, 15])

    def test_chat_endpoint(self):
        """Test chat endpoint."""
        response = self.client.post(
            "/api/chat", json={"question": "What are the main security issues?"}
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn("response", data)
        self.assertIn("timestamp", data)


if __name__ == "__main__":
    unittest.main()
