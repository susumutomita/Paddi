#!/usr/bin/env python3
"""
Main entry point for Paddi Python agents orchestration.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta

import fire

from app.collector.agent_collector import main as collector_main
from app.explainer.agent_explainer import main as explainer_main
from app.reporter.agent_reporter import main as reporter_main
from app.safety.safety_check import SafetyCheck
from app.safety.models import ApprovalStatus

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class PaddiCLI:
    """Paddi CLI for cloud security audit automation."""
    
    def __init__(self):
        """Initialize Paddi CLI with safety system."""
        self.safety_check = SafetyCheck(audit_log_dir="audit_logs")

    def init(self, skip_run: bool = False, output: str = "output"):
        """
        Initialize Paddi with sample data for quick demonstration.

        Args:
            skip_run: Skip automatic pipeline execution
            output: Output directory for reports
        """
        logger.info("🚀 Welcome to Paddi!")

        # Ensure directories exist
        Path("data").mkdir(exist_ok=True)
        Path(output).mkdir(exist_ok=True)

        # Create sample data if it doesn't exist
        sample_data_path = Path("data/sample_collected.json")
        if not sample_data_path.exists():
            sample_data = {
                "project_id": "example-project-123",
                "timestamp": "2025-06-23T10:00:00Z",
                "iam_policies": [
                    {
                        "resource": "projects/example-project-123",
                        "bindings": [
                            {"role": "roles/owner", "members": ["user:admin@example.com"]}
                        ],
                    }
                ],
                "scc_findings": [
                    {
                        "name": "organizations/123/sources/456/findings/789",
                        "category": "PUBLIC_BUCKET",
                        "severity": "HIGH",
                    }
                ],
            }
            sample_data_path.write_text(json.dumps(sample_data, indent=2), encoding="utf-8")
            logger.info("✅ Created sample data")

        if not skip_run:
            logger.info("Running full audit pipeline with sample data...")
            self.audit(use_mock=True, output_dir=output)
        else:
            logger.info("✅ Paddi initialized. Run 'python main.py audit' to start.")

    def audit(
        self,
        project_id: str = "example-project-123",
        organization_id: Optional[str] = None,
        use_mock: bool = True,
        location: str = "us-central1",
        output_dir: str = "output",
        verbose: bool = False,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
    ):
        """
        Run complete audit pipeline.

        Args:
            project_id: GCP project ID
            organization_id: Optional organization ID
            use_mock: Use mock data instead of real GCP APIs
            location: GCP location for Vertex AI
            output_dir: Output directory for reports
            verbose: Enable verbose logging
            ai_provider: AI provider to use ('gemini' or 'ollama')
            ollama_model: Ollama model name (default: gemma3:latest)
            ollama_endpoint: Ollama API endpoint (default: http://localhost:11434)
        """
        if verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        try:
            # Step 1: Collect
            logger.info("🔍 Starting security audit...")
            self.collect(project_id, organization_id, use_mock)

            # Step 2: Analyze
            self.analyze(project_id, location, use_mock, ai_provider, ollama_model, ollama_endpoint)

            # Step 3: Report
            self.report(output_dir=output_dir)

            logger.info("✅ Audit completed successfully!")
            logger.info("📊 Reports generated in: %s/", output_dir)

        except Exception as e:
            logger.error("❌ Audit pipeline failed: %s", e)
            if verbose:
                logger.exception("Full error trace:")
            sys.exit(1)

    def collect(
        self,
        project_id: str = "example-project-123",
        organization_id: Optional[str] = None,
        use_mock: bool = True,
    ):
        """
        Collect cloud configuration data.

        Args:
            project_id: GCP project ID
            organization_id: Optional organization ID
            use_mock: Use mock data instead of real GCP APIs
        """
        logger.info("✓ Collecting IAM policies and SCC findings...")

        try:
            collector_main(
                project_id=project_id,
                organization_id=organization_id,
                use_mock=use_mock,
            )

            # Load and display summary
            collected_path = Path("data/collected.json")
            if collected_path.exists():
                data = json.loads(collected_path.read_text(encoding="utf-8"))
                iam_count = len(data.get("iam_policies", []))
                scc_count = len(data.get("scc_findings", []))
                logger.info("  └─ Found %d IAM policies", iam_count)
                logger.info("  └─ Found %d SCC findings", scc_count)

        except Exception as e:
            logger.error("❌ Collection failed: %s", e)
            raise

    def analyze(
        self,
        project_id: str = "example-project-123",
        location: str = "us-central1",
        use_mock: bool = True,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
    ):
        """
        Analyze collected data with AI.

        Args:
            project_id: GCP project ID
            location: GCP location for Vertex AI
            use_mock: Use mock AI responses
            ai_provider: AI provider to use ('gemini' or 'ollama')
            ollama_model: Ollama model name (default: gemma3:latest)
            ollama_endpoint: Ollama API endpoint (default: http://localhost:11434)
        """
        import os

        provider = ai_provider or os.getenv("AI_PROVIDER", "gemini")
        logger.info("✓ Analyzing with %s AI...", provider.capitalize())

        try:
            explainer_main(
                project_id=project_id,
                location=location,
                use_mock=use_mock,
                ai_provider=ai_provider,
                ollama_model=ollama_model,
                ollama_endpoint=ollama_endpoint,
            )

            # Load and display summary
            explained_path = Path("data/explained.json")
            if explained_path.exists():
                data = json.loads(explained_path.read_text(encoding="utf-8"))
                findings = data if isinstance(data, list) else []

                severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
                for finding in findings:
                    severity = finding.get("severity", "LOW")
                    if severity in severity_counts:
                        severity_counts[severity] += 1

                for severity, count in severity_counts.items():
                    if count > 0:
                        logger.info("  ├─ %s: %d issues", severity, count)

        except Exception as e:
            logger.error("❌ Analysis failed: %s", e)
            raise

    def report(
        self,
        formats: Optional[List[str]] = None,
        input_dir: str = "data",
        output_dir: str = "output",
        template_dir: str = "app/templates",
    ):
        """
        Generate audit reports.

        Args:
            formats: Report formats (markdown, html, honkit)
            input_dir: Input data directory
            output_dir: Output directory
            template_dir: Template directory
        """
        if formats is None:
            formats = ["markdown", "html"]

        logger.info("✓ Generating reports in formats: %s", ", ".join(formats))

        try:
            reporter_main(
                template_dir=template_dir,
                formats=formats,
                input_dir=input_dir,
                output_dir=output_dir,
            )

            logger.info("✓ Reports generated:")
            for fmt in formats:
                if fmt == "markdown":
                    logger.info("  • Markdown: %s/audit.md", output_dir)
                elif fmt == "html":
                    logger.info("  • HTML: %s/audit.html", output_dir)
                elif fmt == "honkit":
                    logger.info("  • HonKit: docs/")

        except Exception as e:
            logger.error("❌ Report generation failed: %s", e)
            raise
    
    def validate_command(
        self,
        command: str,
        user: str = "cli-user",
        dry_run: bool = True,
        force_approval: bool = False
    ):
        """
        Validate a command for safety risks before execution.
        
        Args:
            command: The command to validate
            user: Username executing the command
            dry_run: Whether to simulate execution only
            force_approval: Force manual approval even for low-risk commands
        """
        logger.info("🛡️ Validating command safety...")
        
        is_safe, message, approval_request = self.safety_check.validate_command(
            command, user, dry_run, force_approval
        )
        
        print("\n" + message)
        
        if approval_request and approval_request.status == ApprovalStatus.PENDING:
            print(f"\n📋 Approval Request ID: {approval_request.id}")
            print("Use 'python main.py approve <request-id>' to approve this command")
        
        return is_safe
    
    def execute_remediation(
        self,
        command: str,
        user: str = "cli-user",
        approval_id: Optional[str] = None,
        dry_run: bool = True
    ):
        """
        Execute a remediation command with safety checks.
        
        Args:
            command: The remediation command to execute
            user: Username executing the command
            approval_id: Pre-approval ID if command was already approved
            dry_run: Whether to simulate execution only (default: True for safety)
        """
        logger.info("⚡ Executing remediation command...")
        
        if not dry_run:
            confirm = input("⚠️  WARNING: This will execute the command. Continue? (yes/no): ")
            if confirm.lower() != "yes":
                logger.info("Execution cancelled by user")
                return
        
        success, result = self.safety_check.execute_command(
            command, user, approval_id, dry_run
        )
        
        if success:
            logger.info("✅ Command execution completed")
        else:
            logger.error("❌ Command execution failed")
        
        print("\n" + result)
    
    def approve(self, request_id: str, approver: str = "admin"):
        """
        Approve a pending remediation command.
        
        Args:
            request_id: The approval request ID
            approver: Username of the approver
        """
        approval = self.safety_check.approve_command(request_id, approver)
        
        if approval:
            logger.info("✅ Command approved by %s", approver)
            print(self.safety_check.approval_workflow.format_approval_request(approval))
        else:
            logger.error("❌ Approval request not found: %s", request_id)
    
    def reject(self, request_id: str, reason: str, rejector: str = "admin"):
        """
        Reject a pending remediation command.
        
        Args:
            request_id: The approval request ID
            reason: Reason for rejection
            rejector: Username of the rejector
        """
        approval = self.safety_check.reject_command(request_id, rejector, reason)
        
        if approval:
            logger.info("❌ Command rejected by %s", rejector)
            print(self.safety_check.approval_workflow.format_approval_request(approval))
        else:
            logger.error("❌ Approval request not found: %s", request_id)
    
    def list_approvals(self, status: str = "pending"):
        """
        List approval requests.
        
        Args:
            status: Filter by status (pending, all)
        """
        if status == "pending":
            approvals = self.safety_check.get_pending_approvals()
            logger.info("📋 Pending approval requests: %d", len(approvals))
        else:
            # Get all from history
            approvals = (
                self.safety_check.get_pending_approvals() +
                self.safety_check.approval_workflow.approval_history
            )
            logger.info("📋 Total approval requests: %d", len(approvals))
        
        if not approvals:
            print("No approval requests found")
            return
        
        for approval in approvals:
            print("\n" + "-" * 60)
            print(f"ID: {approval.id}")
            print(f"Status: {approval.status.value}")
            print(f"Command: {approval.command[:80]}...")
            print(f"Risk: {approval.validation.risk_level.value}")
            print(f"Requested by: {approval.requested_by}")
            print(f"Requested at: {approval.requested_at.strftime('%Y-%m-%d %H:%M:%S')}")
    
    def audit_log(
        self,
        days: int = 7,
        user: Optional[str] = None,
        risk_level: Optional[str] = None
    ):
        """
        View audit logs for command executions.
        
        Args:
            days: Number of days to look back
            user: Filter by user
            risk_level: Filter by risk level (low, medium, high, critical)
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        if user or risk_level:
            # Use search with filters
            logs = self.safety_check.search_audit_logs(
                user=user,
                risk_level=risk_level,
                start_time=start_time,
                end_time=end_time
            )
            
            logger.info("📜 Found %d audit log entries", len(logs))
            
            for log in logs[-20:]:  # Show last 20
                print("\n" + "-" * 60)
                print(f"Timestamp: {log['timestamp']}")
                print(f"User: {log['executed_by']}")
                print(f"Command: {log['command'][:80]}...")
                print(f"Risk: {log['validation_result']['risk_level']}")
                print(f"Dry Run: {log['dry_run']}")
                if log.get('execution_error'):
                    print(f"Error: {log['execution_error']}")
        else:
            # Generate full report
            report = self.safety_check.get_audit_report(start_time, end_time)
            print(report)
    
    def safety_demo(self):
        """
        Demonstrate the safety system with example commands.
        """
        logger.info("🎯 Running safety system demonstration...")
        
        demo_commands = [
            {
                "description": "Safe read-only command",
                "command": "gcloud projects list"
            },
            {
                "description": "Medium risk - stopping a service",
                "command": "systemctl stop nginx"
            },
            {
                "description": "High risk - removing IAM binding",
                "command": "gcloud projects remove-iam-policy-binding my-project --member='serviceAccount:app@my-project.iam.gserviceaccount.com' --role='roles/editor'"
            },
            {
                "description": "Critical risk - deleting storage bucket",
                "command": "gsutil rm -r gs://production-backup-bucket/"
            },
            {
                "description": "Critical risk - removing firewall rules",
                "command": "firewall-cmd --permanent --remove-port=443/tcp"
            }
        ]
        
        print("\n" + "=" * 80)
        print("SAFETY SYSTEM DEMONSTRATION")
        print("=" * 80)
        
        for demo in demo_commands:
            print(f"\n🔍 Testing: {demo['description']}")
            print(f"Command: {demo['command']}")
            print("-" * 80)
            
            self.validate_command(demo['command'], user="demo-user", dry_run=True)
            
            input("\nPress Enter to continue to next example...")
        
        print("\n✅ Safety demonstration completed!")
        print("\nThe safety system helps prevent:")
        print("• Accidental deletion of critical resources")
        print("• Disruption of production services")
        print("• Security misconfigurations")
        print("• Irreversible changes without approval")


def main():
    """Main entry point."""
    fire.Fire(PaddiCLI)


if __name__ == "__main__":
    main()
