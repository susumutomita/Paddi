"""Tests for AgentManager."""

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.api.agent_manager import AgentManager, AuditStatus


class TestAgentManager(unittest.TestCase):
    """Test cases for AgentManager."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.data_dir = Path(self.temp_dir) / "data"
        self.output_dir = Path(self.temp_dir) / "output"
        self.agent_manager = AgentManager(
            data_dir=str(self.data_dir), output_dir=str(self.output_dir)
        )

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir)

    def test_init_creates_directories(self):
        """Test that initialization creates required directories."""
        self.assertTrue(self.data_dir.exists())
        self.assertTrue(self.output_dir.exists())

    def test_start_audit(self):
        """Test starting a new audit."""
        audit_id = self.agent_manager.start_audit(
            project_id="test-project",
            organization_id="test-org",
            use_mock=True,
            location="us-central1",
        )

        self.assertIsNotNone(audit_id)
        self.assertTrue(audit_id.startswith("audit-"))

        audit = self.agent_manager.get_audit_status(audit_id)
        self.assertEqual(audit["project_id"], "test-project")
        self.assertEqual(audit["organization_id"], "test-org")
        self.assertEqual(audit["status"], AuditStatus.PENDING)
        self.assertIsNotNone(audit["started_at"])

    @patch("app.api.agent_manager.collector_main")
    @patch("app.api.agent_manager.explainer_main")
    @patch("app.api.agent_manager.reporter_main")
    def test_run_audit_sync_success(
        self, mock_reporter, mock_explainer, mock_collector
    ):
        """Test successful synchronous audit execution."""
        # Start audit
        audit_id = self.agent_manager.start_audit(
            project_id="test-project", use_mock=True
        )

        # Run audit
        result = self.agent_manager.run_audit_sync(audit_id)

        # Verify all agents were called
        mock_collector.assert_called_once()
        mock_explainer.assert_called_once()
        mock_reporter.assert_called_once()

        # Verify audit status
        self.assertEqual(result["status"], AuditStatus.COMPLETED)
        self.assertIsNotNone(result["completed_at"])
        self.assertIsNone(result["error"])

    @patch("app.api.agent_manager.collector_main")
    def test_run_audit_sync_failure(self, mock_collector):
        """Test audit execution with failure."""
        # Make collector fail
        mock_collector.side_effect = Exception("Collection failed")

        # Start audit
        audit_id = self.agent_manager.start_audit(
            project_id="test-project", use_mock=True
        )

        # Run audit
        result = self.agent_manager.run_audit_sync(audit_id)

        # Verify audit failed
        self.assertEqual(result["status"], AuditStatus.FAILED)
        self.assertEqual(result["error"], "Collection failed")
        self.assertIsNotNone(result["completed_at"])

    def test_get_findings_no_file(self):
        """Test getting findings when no file exists."""
        findings = self.agent_manager.get_findings()
        self.assertIsNone(findings)

    def test_get_findings_with_data(self):
        """Test getting findings from explained.json."""
        # Create sample explained.json
        sample_findings = [
            {
                "title": "Test Finding 1",
                "severity": "HIGH",
                "explanation": "This is a test",
                "recommendation": "Fix it",
            },
            {
                "title": "Test Finding 2",
                "severity": "LOW",
                "explanation": "Minor issue",
                "recommendation": "Consider fixing",
            },
        ]

        explained_file = self.data_dir / "explained.json"
        with open(explained_file, "w", encoding="utf-8") as f:
            json.dump(sample_findings, f)

        # Get findings
        result = self.agent_manager.get_findings()

        self.assertIsNotNone(result)
        self.assertEqual(len(result["findings"]), 2)
        self.assertEqual(result["total"], 2)
        self.assertEqual(result["severity_distribution"]["HIGH"], 1)
        self.assertEqual(result["severity_distribution"]["LOW"], 1)
        self.assertIn("last_updated", result)

    def test_get_audit_status_not_found(self):
        """Test getting status of non-existent audit."""
        status = self.agent_manager.get_audit_status("non-existent")
        self.assertIsNone(status)


if __name__ == "__main__":
    unittest.main()