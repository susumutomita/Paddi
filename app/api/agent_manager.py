"""Agent Manager for orchestrating Paddi agents in web context."""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from app.collector.agent_collector import main as collector_main
from app.explainer.agent_explainer import main as explainer_main
from app.reporter.agent_reporter import main as reporter_main

logger = logging.getLogger(__name__)


class AuditStatus:
    """Enum-like class for audit statuses."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentManager:
    """Manages the execution of Paddi agents for web integration."""

    def __init__(self, data_dir: str = "data", output_dir: str = "output"):
        """Initialize AgentManager with directories."""
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.audits = {}  # In-memory storage of audit states

        # Ensure directories exist
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)

    def start_audit(
        self,
        project_id: str,
        organization_id: Optional[str] = None,
        use_mock: bool = True,
        location: str = "us-central1",
        ai_provider: Optional[str] = None,
        ollama_model: Optional[str] = None,
        ollama_endpoint: Optional[str] = None,
    ) -> str:
        """Start a new audit and return audit ID."""
        audit_id = f"audit-{uuid.uuid4().hex[:8]}"

        # Create audit record
        audit = {
            "id": audit_id,
            "project_id": project_id,
            "organization_id": organization_id,
            "status": AuditStatus.PENDING,
            "started_at": datetime.utcnow().isoformat(),
            "completed_at": None,
            "error": None,
            "config": {
                "use_mock": use_mock,
                "location": location,
                "ai_provider": ai_provider,
                "ollama_model": ollama_model,
                "ollama_endpoint": ollama_endpoint,
            },
        }

        self.audits[audit_id] = audit
        logger.info(f"Created audit {audit_id} for project {project_id}")

        return audit_id

    def run_audit_sync(self, audit_id: str) -> Dict[str, Any]:
        """Run audit synchronously (for initial implementation)."""
        if audit_id not in self.audits:
            raise ValueError(f"Audit {audit_id} not found")

        audit = self.audits[audit_id]
        audit["status"] = AuditStatus.RUNNING

        try:
            # Step 1: Collect data
            logger.info(f"Running collector for audit {audit_id}")
            self._run_collector(audit)

            # Step 2: Explain findings
            logger.info(f"Running explainer for audit {audit_id}")
            self._run_explainer(audit)

            # Step 3: Generate report
            logger.info(f"Running reporter for audit {audit_id}")
            self._run_reporter(audit)

            # Mark as completed
            audit["status"] = AuditStatus.COMPLETED
            audit["completed_at"] = datetime.utcnow().isoformat()
            logger.info(f"Audit {audit_id} completed successfully")

        except Exception as e:
            logger.error(f"Audit {audit_id} failed: {str(e)}")
            audit["status"] = AuditStatus.FAILED
            audit["error"] = str(e)
            audit["completed_at"] = datetime.utcnow().isoformat()

        return audit

    def _run_collector(self, audit: Dict[str, Any]) -> None:
        """Run the collector agent."""
        try:
            # Call collector main function
            collector_main(
                project_id=audit["project_id"],
                organization_id=audit["organization_id"],
                use_mock=audit["config"]["use_mock"],
                output_dir=str(self.data_dir),
            )
        except Exception as e:
            logger.error(f"Collector failed: {str(e)}")
            raise

    def _run_explainer(self, audit: Dict[str, Any]) -> None:
        """Run the explainer agent."""
        try:
            # Call explainer main function
            explainer_main(
                project_id=audit["project_id"],
                location=audit["config"]["location"],
                use_mock=audit["config"]["use_mock"],
                ai_provider=audit["config"]["ai_provider"],
                ollama_model=audit["config"]["ollama_model"],
                ollama_endpoint=audit["config"]["ollama_endpoint"],
            )
        except Exception as e:
            logger.error(f"Explainer failed: {str(e)}")
            raise

    def _run_reporter(self, audit: Dict[str, Any]) -> None:
        """Run the reporter agent."""
        try:
            # Call reporter main function
            reporter_main(output_dir=str(self.output_dir))
        except Exception as e:
            logger.error(f"Reporter failed: {str(e)}")
            raise

    def get_audit_status(self, audit_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an audit."""
        return self.audits.get(audit_id)

    def get_findings(self) -> Optional[Dict[str, Any]]:
        """Get findings from the latest explained.json file."""
        explained_file = self.data_dir / "explained.json"

        if not explained_file.exists():
            logger.warning("No explained.json file found")
            return None

        try:
            with open(explained_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Format findings for web API
            findings = []
            severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}

            for finding in data:
                severity = finding.get("severity", "MEDIUM").upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1

                findings.append(
                    {
                        "title": finding.get("title", "Unknown Finding"),
                        "severity": severity,
                        "explanation": finding.get("explanation", ""),
                        "recommendation": finding.get("recommendation", ""),
                        "count": 1,  # Can be enhanced to group similar findings
                    }
                )

            return {
                "findings": findings,
                "total": len(findings),
                "severity_distribution": severity_counts,
                "last_updated": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logger.error(f"Error reading findings: {str(e)}")
            return None

    def get_all_audits(self) -> Dict[str, Dict[str, Any]]:
        """Get all audits."""
        return self.audits