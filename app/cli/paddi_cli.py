"""Refactored Paddi CLI using command pattern."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional

from app.cli.base import CommandContext
from app.cli.registry import registry
from app.safety.safety_check import SafetyCheck

logger = logging.getLogger(__name__)


class PaddiCLI:
    """Refactored Paddi CLI with command pattern."""
    
    def __init__(self):
        """Initialize Paddi CLI with safety system."""
        self.safety_check = SafetyCheck(audit_log_dir="audit_logs")
        self.registry = registry
    
    def _create_context(self, **kwargs) -> CommandContext:
        """Create command context from kwargs."""
        return CommandContext(**kwargs)
    
    def init(self, skip_run: bool = False, output: str = "output", **kwargs):
        """Initialize Paddi with sample data."""
        context = self._create_context(skip_run=skip_run, output_dir=output, **kwargs)
        command = self.registry.get_command("init")()
        command.execute(context)
    
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
        **kwargs
    ):
        """Run complete audit pipeline."""
        context = self._create_context(
            project_id=project_id,
            organization_id=organization_id,
            use_mock=use_mock,
            location=location,
            output_dir=output_dir,
            verbose=verbose,
            ai_provider=ai_provider,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            **kwargs
        )
        command = self.registry.get_command("audit")()
        command.execute(context)
    
    def collect(
        self,
        project_id: str = "example-project-123",
        organization_id: Optional[str] = None,
        use_mock: bool = True,
        verbose: bool = False,
        collect_all: bool = False,
        aws_account_id: Optional[str] = None,
        aws_region: str = "us-east-1",
        azure_subscription_id: Optional[str] = None,
        azure_tenant_id: Optional[str] = None,
        github_owner: Optional[str] = None,
        github_repo: Optional[str] = None,
        **kwargs
    ):
        """Collect GCP configuration."""
        context = self._create_context(
            project_id=project_id,
            organization_id=organization_id,
            use_mock=use_mock,
            verbose=verbose,
            collect_all=collect_all,
            aws_account_id=aws_account_id,
            aws_region=aws_region,
            azure_subscription_id=azure_subscription_id,
            azure_tenant_id=azure_tenant_id,
            github_owner=github_owner,
            github_repo=github_repo,
            **kwargs
        )
        command = self.registry.get_command("collect")()
        command.execute(context)
    
    def analyze(
        self,
        project_id: str = "example-project-123",
        location: str = "us-central1",
        use_mock: bool = True,
        verbose: bool = False,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
        **kwargs
    ):
        """Analyze security risks (alias for explain)."""
        self.explain(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
            verbose=verbose,
            ai_provider=ai_provider,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            **kwargs
        )
    
    def explain(
        self,
        project_id: str = "example-project-123",
        location: str = "us-central1",
        use_mock: bool = True,
        verbose: bool = False,
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
        **kwargs
    ):
        """Analyze security risks using AI."""
        context = self._create_context(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
            verbose=verbose,
            ai_provider=ai_provider,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
            **kwargs
        )
        command = self.registry.get_command("explain")()
        command.execute(context)
    
    def report(self, output_dir: str = "output", verbose: bool = False, **kwargs):
        """Generate audit report."""
        context = self._create_context(output_dir=output_dir, verbose=verbose, **kwargs)
        command = self.registry.get_command("report")()
        command.execute(context)
    
    def list_commands(self):
        """List available commands."""
        print("\n📋 Available Paddi Commands:")
        print("=" * 60)
        
        commands = self.registry.list_commands()
        for name, description in sorted(commands.items()):
            print(f"  {name:<15} - {description}")
        
        print("\n💡 Use 'python main.py <command> --help' for more info")
    
    # Safety-related methods
    def validate_command(
        self,
        command: str,
        user: str = "unknown",
        dry_run: bool = True,
        require_approval: bool = True,
        **kwargs
    ):
        """Validate a command for safety risks."""
        from app.common.models import ExecutionContext
        
        context = ExecutionContext(
            command=command, user=user, dry_run=dry_run, timestamp=datetime.utcnow()
        )
        
        validation_result = self.safety_check.validate_command(context)
        
        print(f"\n🔍 Command Validation Report")
        print("=" * 60)
        print(f"Command: {command}")
        print(f"Risk Level: {validation_result.risk_level.value}")
        print(f"Impact Score: {validation_result.impact_score}")
        print(f"Safe to Execute: {'✅ Yes' if validation_result.is_safe else '❌ No'}")
        
        if validation_result.risks:
            print("\n⚠️  Identified Risks:")
            for risk in validation_result.risks:
                print(f"  • {risk}")
        
        if validation_result.recommendations:
            print("\n💡 Recommendations:")
            for rec in validation_result.recommendations:
                print(f"  • {rec}")
        
        if dry_run:
            print("\n🔒 Running in DRY RUN mode - no actual changes will be made")
        
        if not validation_result.is_safe and require_approval:
            print("\n⚠️  This command requires approval due to high risk!")
            approval_id = self.safety_check.request_approval(context, validation_result)
            print(f"Approval ID: {approval_id}")
            print("Please get approval from an authorized person before proceeding.")
        
        return validation_result
    
    def approve_command(self, approval_id: str, approver: str = "admin", notes: str = ""):
        """Approve a pending command."""
        approval_granted = self.safety_check.process_approval(
            approval_id=approval_id, approver=approver, approved=True, notes=notes
        )
        
        if approval_granted:
            print(f"✅ Command approved by {approver}")
            print(f"Approval ID: {approval_id}")
            if notes:
                print(f"Notes: {notes}")
        else:
            print(f"❌ Failed to approve command {approval_id}")
    
    def audit_logs(
        self,
        days: int = 7,
        user: Optional[str] = None,
        risk_level: Optional[str] = None,
        **kwargs
    ):
        """View audit logs for executed commands."""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=days)
        
        if user or risk_level:
            # Use search with filters
            logs = self.safety_check.search_audit_logs(
                user=user, risk_level=risk_level, start_time=start_time, end_time=end_time
            )
            
            logger.info("📜 Found %d audit log entries", len(logs))
            
            for log in logs[-20:]:  # Show last 20
                print("\n" + "-" * 60)
                print(f"Timestamp: {log['timestamp']}")
                print(f"User: {log['executed_by']}")
                print(f"Command: {log['command'][:80]}...")
                print(f"Risk: {log['validation_result']['risk_level']}")
                print(f"Dry Run: {log['dry_run']}")
                if log.get("execution_error"):
                    print(f"Error: {log['execution_error']}")
        else:
            # Generate full report
            report = self.safety_check.get_audit_report(start_time, end_time)
            print(report)
    
    def safety_demo(self):
        """Demonstrate the safety system with example commands."""
        logger.info("🎯 Running safety system demonstration...")
        
        demo_commands = [
            {"description": "Safe read-only command", "command": "gcloud projects list"},
            {"description": "Medium risk - stopping a service", "command": "systemctl stop nginx"},
            {
                "description": "High risk - removing IAM binding",
                "command": (
                    "gcloud projects remove-iam-policy-binding my-project "
                    "--member='serviceAccount:app@my-project.iam.gserviceaccount.com' "
                    "--role='roles/editor'"
                ),
            },
            {
                "description": "Critical risk - deleting storage bucket",
                "command": "gsutil rm -r gs://production-backup-bucket/",
            },
            {
                "description": "Critical risk - removing firewall rules",
                "command": "firewall-cmd --permanent --remove-port=443/tcp",
            },
        ]
        
        print("\n" + "=" * 80)
        print("SAFETY SYSTEM DEMONSTRATION")
        print("=" * 80)
        
        for demo in demo_commands:
            print(f"\n🔍 Testing: {demo['description']}")
            print(f"Command: {demo['command']}")
            print("-" * 80)
            
            self.validate_command(demo["command"], user="demo-user", dry_run=True)
            
            input("\nPress Enter to continue to next example...")
        
        print("\n✅ Safety demonstration completed!")
        print("\nThe safety system helps prevent:")
        print("• Accidental deletion of critical resources")
        print("• Disruption of production services")
        print("• Security misconfigurations")
        print("• Irreversible changes without approval")