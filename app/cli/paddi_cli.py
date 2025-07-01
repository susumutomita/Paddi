"""Refactored Paddi CLI using command pattern."""

import logging
import os
from typing import Optional

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
        **kwargs,
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
            **kwargs,
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
        **kwargs,
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
            **kwargs,
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
        **kwargs,
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
            **kwargs,
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
        **kwargs,
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
            **kwargs,
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
    ):
        """Validate a command for safety risks."""
        is_safe, message, approval_request = self.safety_check.validate_command(
            command=command, user=user, dry_run=dry_run, force_approval=require_approval
        )

        print("\n🔍 Command Validation Report")
        print("=" * 60)
        print(message)
        print("=" * 60)

        if approval_request:
            print(f"\nApproval Status: {approval_request.status.value}")
            if approval_request.status.value == "pending":
                print(f"Approval ID: {approval_request.id}")
                print("⚠️  This command requires approval before execution.")

        return is_safe

    def approve_command(self, approval_id: str, approver: str = "admin", notes: str = ""):
        """Approve a pending command."""
        approval_request = self.safety_check.approve_command(approval_id, approver)

        if approval_request:
            print(f"✅ Command approved by {approver}")
            print(f"Approval ID: {approval_id}")
            if notes:
                print(f"Notes: {notes}")
        else:
            print(f"❌ Failed to approve command {approval_id}")

    def execute_remediation(self, command: str, user: str = "test-user", dry_run: bool = True):
        """Execute a remediation command with safety checks."""
        success, result = self.safety_check.execute_command(
            command=command, user=user, dry_run=dry_run
        )

        if dry_run:
            print("\n🔒 DRY-RUN MODE - Command not executed")

        print(result)

        if not dry_run and success:
            if input("\nProceed with execution? (yes/no): ").lower() != "yes":
                print("Execution cancelled by user")

    def approve(self, approval_id: str, approver: str = "admin"):
        """Approve a pending command."""
        approval = self.safety_check.approve_command(approval_id, approver)
        if approval:
            print(f"\n✅ Approval Request: {approval_id}")
            print(f"Status: {approval.status.value.upper()}")
            print(f"Decided by: {approver}")
            print(self.safety_check.approval_workflow.format_approval_request(approval))

    def reject(self, approval_id: str, reason: str, rejector: str = "admin"):
        """Reject a pending command."""
        approval = self.safety_check.reject_command(approval_id, rejector, reason)
        if approval:
            print(f"\n❌ Approval Request: {approval_id}")
            print(f"Status: {approval.status.value.upper()}")
            print(f"Decided by: {rejector}")
            print(f"Reason: {reason}")
            print(self.safety_check.approval_workflow.format_approval_request(approval))

    def list_approvals(self, status: str = "pending"):
        """List approval requests."""
        if status == "pending":
            approvals = self.safety_check.get_pending_approvals()
        else:
            # Get all from history
            approvals = self.safety_check.approval_workflow.approval_history

        if not approvals:
            print("No approval requests found")
            return

        for approval in approvals:
            print(f"\n📋 Approval Request: {approval.id}")
            print(f"Status: {approval.status.value}")
            print(f"Command: {approval.command}")
            print(f"Risk: {approval.validation.risk_level.value}")
            print(f"Requested by: {approval.requested_by}")

    def chat(self, web: bool = False):
        """Start AI conversational interface.

        Args:
            web: Launch web interface instead of CLI (requires streamlit)
        """
        from app.agents.conversation import ConversationalInterface

        interface = ConversationalInterface()
        if web:
            interface.start_web_interface()
        else:
            interface.start_cli_interface()

    def ai_agent(self, prompt: str, project_id: str = None):
        """Execute AI agent commands.

        Args:
            prompt: Natural language command or question
            project_id: GCP project ID
        """
        from app.agents.orchestrator import MultiAgentCoordinator

        coordinator = MultiAgentCoordinator(project_id=project_id)
        response = coordinator.process_complex_request(prompt)

        if response.get("success"):
            print(f"\n✅ {response.get('message', 'Command processed successfully')}")
            if "summary" in response:
                print(f"\n{response['summary']}")
            if "report_path" in response:
                print(f"\nReport saved to: {response['report_path']}")
        else:
            print(f"\n❌ {response.get('message', 'Command failed')}")

    def ai_audit(self, project_id: str, use_mock: bool = False, auto_fix: bool = False):
        """Execute autonomous security audit using AI agents.

        This command performs a complete security audit autonomously:
        1. Collects real GCP configuration data
        2. Analyzes findings with AI
        3. Generates comprehensive reports
        4. Optionally creates fixes (if auto_fix=True)

        Args:
            project_id: GCP project ID to audit
            use_mock: Use mock data (default: False for real data)
            auto_fix: Automatically create PRs for fixes
        """
        print(f"\n🤖 Starting AI-powered autonomous security audit for project: {project_id}")
        print("=" * 70)

        from app.agents.orchestrator import MultiAgentCoordinator

        # Force real data collection
        os.environ["USE_MOCK"] = "false" if not use_mock else "true"

        coordinator = MultiAgentCoordinator(project_id=project_id)

        # Execute autonomous audit
        print("\n📊 Phase 1: Initiating security audit...")
        response = coordinator.process_complex_request(
            f"Perform a comprehensive security audit of GCP project {project_id}"
        )

        if response.get("success"):
            print(f"\n✅ {response.get('message', 'Audit completed successfully')}")

            # Display summary
            if "summary" in response:
                print("\n📋 Audit Summary:")
                print(response["summary"])

            # Display report location
            if "report_path" in response:
                print(f"\n📄 Detailed report available at: {response['report_path']}")

                # Also show key findings
                results = response.get("results", {})
                analyze_result = results.get("analyze", {})
                if analyze_result.get("findings"):
                    print(f"\n⚠️  Security Issues Found: {analyze_result.get('total', 0)}")
                    print(f"   - Critical: {analyze_result.get('critical', 0)}")
                    print(f"   - High: {analyze_result.get('high', 0)}")

            # Auto-fix if requested
            if auto_fix and analyze_result.get("findings"):
                print("\n🔧 Phase 2: Creating automated fixes...")
                fix_response = coordinator.process_complex_request(
                    "Create pull requests to fix the detected security issues"
                )
                if fix_response.get("success"):
                    print(f"✅ {fix_response.get('message', 'Fixes created')}")
                    if "pull_requests" in fix_response:
                        print(f"   Pull requests: {fix_response['pull_requests']}")
        else:
            print(f"\n❌ Audit failed: {response.get('message', 'Unknown error')}")

    def langchain_audit(self, project_id: str, verbose: bool = True):
        """Execute autonomous security audit using LangChain AI agent.

        This uses LangChain's agent framework for truly autonomous, recursive auditing:
        - Self-directed resource discovery
        - Recursive investigation of findings
        - External research (CIS, NIST, etc.)
        - Code analysis
        - Automated remediation planning

        Args:
            project_id: GCP project ID to audit
            verbose: Show detailed agent reasoning (default: True)
        """
        from app.agents.langchain_auditor import main as langchain_main

        return langchain_main(project_id=project_id, verbose=verbose)

    def recursive_audit(self, project_id: str):
        """Execute recursive autonomous security audit.

        This performs a truly autonomous audit that:
        - Recursively discovers and investigates resources
        - Makes AI-driven decisions about what to investigate next
        - Checks compliance with CIS benchmarks
        - Generates comprehensive findings and recommendations

        No external API keys required - uses only GCP APIs and Vertex AI.

        Args:
            project_id: GCP project ID to audit
        """
        from app.agents.recursive_auditor import main as recursive_main

        return recursive_main(project_id=project_id)

    def audit_log(self, user: Optional[str] = None):
        """View audit logs."""
        logs = self.safety_check.search_audit_logs(user=user)

        if logs:
            print(f"\n📜 Found {len(logs)} audit log entries")
            for log in logs:
                print(f"\n- Command: {log['command']}")
                print(f"  User: {log['executed_by']}")
                print(f"  Risk: {log['validation_result']['risk_level']}")
                print(f"  Timestamp: {log['timestamp']}")
        else:
            print("\n📜 No audit logs found")

    def safety_demo(self):
        """Run safety system demonstration."""
        print("\n🛡️  SAFETY SYSTEM DEMONSTRATION")
        print("=" * 60)

        demos = [
            {"command": "gcloud projects list", "desc": "Safe read-only command"},
            {"command": "systemctl stop nginx", "desc": "Medium risk - service disruption"},
            {
                "command": (
                    "gcloud projects remove-iam-policy-binding prod "
                    "--member='user:admin@example.com' --role='roles/owner'"
                ),
                "desc": "High risk - permission removal",
            },
            {
                "command": "firewall-cmd --permanent --remove-port=443/tcp",
                "desc": "Critical risk - firewall change",
            },
        ]

        for demo in demos:
            print(f"\n📝 Testing: {demo['desc']}")
            print(f"Command: {demo['command']}")
            self.validate_command(demo["command"], user="demo-user", dry_run=True)
            input("\nPress Enter to continue...")

        print("\n✅ Safety demonstration completed!")

    def audit_logs(self, **kwargs):
        """Alias for audit_log method."""
        self.audit_log(**kwargs)

    def natural(self):
        """Start natural language interface for Paddi.

        This provides a gemini-cli style autonomous interface that accepts
        natural language commands in both Japanese and English.
        """
        from app.agents.autonomous_cli import AutonomousCLI

        cli = AutonomousCLI()
        cli.start_interactive()
