#!/usr/bin/env python3
"""
Autonomous Security Auditor Agent

This agent autonomously explores, investigates, and audits cloud resources
with recursive decision-making capabilities.
"""

import json
import logging
import os
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from google.cloud import aiplatform, compute_v1, iam, resourcemanager_v3, securitycenter_v1, storage

logger = logging.getLogger(__name__)


class InvestigationStatus(Enum):
    """Status of investigation tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    REQUIRES_RESEARCH = "requires_research"


class AuditContext:
    """Maintains context for autonomous audit."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.discovered_resources = {}
        self.security_findings = []
        self.investigation_queue = []
        self.completed_investigations = set()
        self.external_research = {}
        self.compliance_mappings = {}
        self.decision_log = []
        self.code_analysis_results = {}

    def add_investigation(self, task: Dict[str, Any]):
        """Add new investigation task."""
        if task.get("id") not in self.completed_investigations:
            self.investigation_queue.append(task)
            logger.info(f"Added investigation: {task.get('type')} - {task.get('description')}")

    def get_next_investigation(self) -> Optional[Dict[str, Any]]:
        """Get next investigation task."""
        if self.investigation_queue:
            return self.investigation_queue.pop(0)
        return None

    def log_decision(self, decision: str, reasoning: str, evidence: List[str]):
        """Log autonomous decision."""
        self.decision_log.append(
            {
                "timestamp": datetime.now().isoformat(),
                "decision": decision,
                "reasoning": reasoning,
                "evidence": evidence,
            }
        )


class AutonomousAuditor:
    """Fully autonomous security auditor with recursive investigation capabilities."""

    def __init__(self, project_id: str, max_depth: int = 10):
        self.project_id = project_id
        self.max_depth = max_depth
        self.context = AuditContext(project_id)
        self.model = self._initialize_ai()

        # Initialize GCP clients
        self.resource_manager = resourcemanager_v3.ProjectsClient()
        self.scc_client = securitycenter_v1.SecurityCenterClient()
        self.compute_client = compute_v1.InstancesClient()
        self.storage_client = storage.Client()
        self.iam_client = iam.IAMClient()

    def _initialize_ai(self):
        """Initialize AI model for reasoning."""
        try:
            aiplatform.init(project=self.project_id, location="us-central1")
            return aiplatform.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logger.warning(f"AI initialization failed: {e}")
            return None

    def start_autonomous_audit(self) -> Dict[str, Any]:
        """Start fully autonomous security audit."""
        logger.info(f"🤖 Starting autonomous audit for project: {self.project_id}")

        # Initial investigation tasks
        self._initialize_investigations()

        # Main autonomous loop
        depth = 0
        while self.context.investigation_queue and depth < self.max_depth:
            depth += 1
            investigation = self.context.get_next_investigation()

            logger.info(f"\n🔍 Investigation #{depth}: {investigation.get('type')}")

            # Execute investigation
            results = self._execute_investigation(investigation)

            # AI reasoning on results
            new_investigations = self._reason_about_findings(results, investigation)

            # Add new investigations based on findings
            for new_task in new_investigations:
                self.context.add_investigation(new_task)

            # Check if we need external research
            if self._needs_external_research(results):
                self._conduct_external_research(results)

        # Generate comprehensive report
        return self._generate_final_report()

    def _initialize_investigations(self):
        """Initialize base investigation tasks."""
        base_tasks = [
            {
                "id": "iam_discovery",
                "type": "resource_discovery",
                "description": "Discover all IAM policies and analyze permissions",
                "resource_type": "iam",
                "priority": "high",
            },
            {
                "id": "compute_discovery",
                "type": "resource_discovery",
                "description": "Discover compute instances and analyze security",
                "resource_type": "compute",
                "priority": "high",
            },
            {
                "id": "storage_discovery",
                "type": "resource_discovery",
                "description": "Discover storage buckets and check access controls",
                "resource_type": "storage",
                "priority": "high",
            },
            {
                "id": "network_discovery",
                "type": "resource_discovery",
                "description": "Discover network configurations and firewall rules",
                "resource_type": "network",
                "priority": "medium",
            },
            {
                "id": "scc_findings",
                "type": "security_findings",
                "description": "Analyze Security Command Center findings",
                "priority": "critical",
            },
        ]

        for task in base_tasks:
            self.context.add_investigation(task)

    def _execute_investigation(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a specific investigation."""
        investigation_type = investigation.get("type")

        if investigation_type == "resource_discovery":
            return self._discover_resources(investigation)
        elif investigation_type == "security_findings":
            return self._analyze_security_findings()
        elif investigation_type == "permission_analysis":
            return self._analyze_permissions(investigation)
        elif investigation_type == "code_analysis":
            return self._analyze_code(investigation)
        elif investigation_type == "compliance_check":
            return self._check_compliance(investigation)
        else:
            return {"status": "unknown_type", "data": {}}

    def _discover_resources(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Discover and analyze cloud resources."""
        resource_type = investigation.get("resource_type")
        results = {"type": resource_type, "resources": [], "issues": []}

        try:
            if resource_type == "iam":
                # Get IAM policy
                policy = self._get_iam_policy()
                results["resources"] = policy.get("bindings", [])

                # Analyze each binding
                for binding in results["resources"]:
                    if self._is_risky_role(binding.get("role")):
                        results["issues"].append(
                            {
                                "severity": "HIGH",
                                "type": "overly_permissive_role",
                                "role": binding.get("role"),
                                "members": binding.get("members"),
                                "recommendation": "Apply principle of least privilege",
                            }
                        )

                        # Queue deeper investigation
                        self.context.add_investigation(
                            {
                                "id": f"analyze_{binding.get('role')}",
                                "type": "permission_analysis",
                                "description": f"Deep dive into {binding.get('role')} usage",
                                "role": binding.get("role"),
                                "members": binding.get("members"),
                            }
                        )

            elif resource_type == "compute":
                # List all compute instances
                instances = self._list_compute_instances()
                results["resources"] = instances

                for instance in instances:
                    # Check for security issues
                    issues = self._analyze_instance_security(instance)
                    results["issues"].extend(issues)

                    # Queue code analysis if custom images
                    if instance.get("custom_image"):
                        self.context.add_investigation(
                            {
                                "id": f"analyze_image_{instance.get('name')}",
                                "type": "code_analysis",
                                "description": f"Analyze custom image for {instance.get('name')}",
                                "instance": instance,
                            }
                        )

            elif resource_type == "storage":
                # List storage buckets
                buckets = self._list_storage_buckets()
                results["resources"] = buckets

                for bucket in buckets:
                    # Check bucket permissions
                    if self._is_public_bucket(bucket):
                        results["issues"].append(
                            {
                                "severity": "CRITICAL",
                                "type": "public_bucket",
                                "bucket": bucket.get("name"),
                                "recommendation": "Remove public access",
                            }
                        )

        except Exception as e:
            logger.error(f"Error discovering {resource_type}: {e}")
            results["error"] = str(e)

        return results

    def _reason_about_findings(
        self, results: Dict[str, Any], investigation: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use AI to reason about findings and determine next steps."""
        new_investigations = []

        if not self.model or not results.get("issues"):
            return new_investigations

        # Prepare context for AI
        prompt = f"""
        As a security auditor, analyze these findings and determine what to investigate next:

        Investigation: {investigation.get('description')}
        Findings: {json.dumps(results.get('issues', []), indent=2)}

        Based on these findings, what should we investigate next? Consider:
        1. Root causes of security issues
        2. Related resources that might have similar problems
        3. Compliance requirements (CIS, PCI-DSS, etc.)
        4. Need for external research or documentation

        Respond with a JSON array of investigation tasks with fields:
        - id: unique identifier
        - type: investigation type
        - description: what to investigate
        - priority: critical/high/medium/low
        - reasoning: why this is important
        """

        try:
            response = self.model.generate_content(prompt)
            ai_suggestions = json.loads(response.text)

            for suggestion in ai_suggestions:
                new_investigations.append(suggestion)
                self.context.log_decision(
                    decision=f"Investigate: {suggestion.get('description')}",
                    reasoning=suggestion.get("reasoning", "AI-suggested investigation"),
                    evidence=[str(issue) for issue in results.get("issues", [])],
                )

        except Exception as e:
            logger.error(f"AI reasoning failed: {e}")

        return new_investigations

    def _needs_external_research(self, results: Dict[str, Any]) -> bool:
        """Determine if external research is needed."""
        # Check if we have compliance-related issues
        for issue in results.get("issues", []):
            if any(
                keyword in str(issue).lower()
                for keyword in ["compliance", "cis", "pci", "hipaa", "standard"]
            ):
                return True
        return False

    def _conduct_external_research(self, results: Dict[str, Any]):
        """Conduct external research using web resources."""
        logger.info("🌐 Conducting external compliance research...")

        # Research CIS benchmarks
        cis_research = self._research_cis_benchmarks(results)
        self.context.external_research["cis"] = cis_research

        # Research best practices
        best_practices = self._research_best_practices(results)
        self.context.external_research["best_practices"] = best_practices

        # Add compliance checks based on research
        for standard in ["cis", "pci-dss", "hipaa"]:
            self.context.add_investigation(
                {
                    "id": f"compliance_check_{standard}",
                    "type": "compliance_check",
                    "description": f"Check compliance with {standard.upper()} standards",
                    "standard": standard,
                    "priority": "high",
                }
            )

    def _research_cis_benchmarks(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Research CIS benchmarks for GCP."""
        # In a real implementation, this would fetch from CIS website or API
        return {
            "source": "CIS Google Cloud Platform Foundation Benchmark v1.3.0",
            "relevant_controls": [
                {
                    "id": "1.1",
                    "title": "Ensure that corporate login credentials are used",
                    "applies_to": ["iam"],
                },
                {
                    "id": "3.1",
                    "title": "Ensure that the default network does not exist",
                    "applies_to": ["network"],
                },
            ],
        }

    def _analyze_code(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code in repositories or images."""
        logger.info("💻 Analyzing code for security issues...")

        # This would integrate with code analysis tools
        # For now, return sample results
        return {
            "type": "code_analysis",
            "vulnerabilities": [
                {
                    "type": "hardcoded_credentials",
                    "severity": "CRITICAL",
                    "file": "config.py",
                    "line": 42,
                    "description": "Hardcoded API key found",
                }
            ],
        }

    def _check_compliance(self, investigation: Dict[str, Any]) -> Dict[str, Any]:
        """Check compliance with specific standards."""
        standard = investigation.get("standard")
        logger.info(f"📋 Checking compliance with {standard.upper()}...")

        # Map findings to compliance requirements
        compliance_results = {
            "standard": standard,
            "compliant": False,
            "violations": [],
            "recommendations": [],
        }

        # Check against known requirements
        if standard == "cis":
            # Check CIS controls
            for control in self.context.external_research.get("cis", {}).get(
                "relevant_controls", []
            ):
                # Check if control is satisfied
                violation = self._check_cis_control(control)
                if violation:
                    compliance_results["violations"].append(violation)

        return compliance_results

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive autonomous audit report."""
        report = {
            "audit_id": f"autonomous_audit_{datetime.now().isoformat()}",
            "project_id": self.project_id,
            "summary": {
                "total_resources_discovered": len(self.context.discovered_resources),
                "total_issues_found": len(self.context.security_findings),
                "critical_issues": sum(
                    1 for f in self.context.security_findings if f.get("severity") == "CRITICAL"
                ),
                "investigations_completed": len(self.context.completed_investigations),
                "autonomous_decisions_made": len(self.context.decision_log),
            },
            "discovered_resources": self.context.discovered_resources,
            "security_findings": self.context.security_findings,
            "compliance_status": self.context.compliance_mappings,
            "external_research": self.context.external_research,
            "decision_log": self.context.decision_log,
            "recommendations": self._generate_recommendations(),
        }

        # Save detailed report
        self._save_report(report)

        return report

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations based on all findings."""
        recommendations = []

        # Use AI to synthesize recommendations
        if self.model and self.context.security_findings:
            prompt = f"""
            Based on the security audit findings, generate prioritized recommendations:

            Findings: {json.dumps(self.context.security_findings[:10], indent=2)}
            Compliance gaps: {json.dumps(self.context.compliance_mappings, indent=2)}

            Generate top 5 actionable recommendations with:
            - priority (critical/high/medium/low)
            - action (specific steps)
            - impact (security improvement)
            - effort (implementation effort)
            """

            try:
                response = self.model.generate_content(prompt)
                # Parse AI recommendations
                recommendations = self._parse_ai_recommendations(response.text)
            except Exception as e:
                logger.error(f"Failed to generate AI recommendations: {e}")

        return recommendations

    def _save_report(self, report: Dict[str, Any]):
        """Save detailed audit report."""
        output_file = (
            f"output/autonomous_audit_{self.project_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        os.makedirs("output", exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Detailed report saved to: {output_file}")

    # Helper methods
    def _get_iam_policy(self) -> Dict[str, Any]:
        """Get IAM policy for project."""
        try:
            from google.iam.v1 import iam_policy_pb2

            request = iam_policy_pb2.GetIamPolicyRequest(resource=f"projects/{self.project_id}")
            policy = self.resource_manager.get_iam_policy(request=request)

            bindings = []
            for binding in policy.bindings:
                bindings.append({"role": binding.role, "members": list(binding.members)})
            return {"bindings": bindings}
        except Exception as e:
            logger.error(f"Failed to get IAM policy: {e}")
            return {"bindings": []}

    def _is_risky_role(self, role: str) -> bool:
        """Check if role is overly permissive."""
        risky_roles = ["roles/owner", "roles/editor", "roles/iam.securityAdmin"]
        return role in risky_roles

    def _list_compute_instances(self) -> List[Dict[str, Any]]:
        """List compute instances."""
        # Simplified - would use actual compute API
        return []

    def _list_storage_buckets(self) -> List[Dict[str, Any]]:
        """List storage buckets."""
        try:
            buckets = []
            for bucket in self.storage_client.list_buckets():
                buckets.append(
                    {
                        "name": bucket.name,
                        "location": bucket.location,
                        "created": bucket.time_created.isoformat() if bucket.time_created else None,
                    }
                )
            return buckets
        except Exception as e:
            logger.error(f"Failed to list buckets: {e}")
            return []

    def _is_public_bucket(self, bucket: Dict[str, Any]) -> bool:
        """Check if bucket is publicly accessible."""
        # Would check actual IAM policy
        return False

    def _analyze_instance_security(self, instance: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Analyze compute instance security."""
        issues = []
        # Would perform actual security checks
        return issues

    def _check_cis_control(self, control: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Check specific CIS control."""
        # Would implement actual control checks
        return None

    def _research_best_practices(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Research security best practices."""
        return {
            "source": "Google Cloud Security Best Practices",
            "recommendations": [
                "Enable VPC Flow Logs",
                "Use Cloud KMS for encryption",
                "Enable Cloud Asset Inventory",
            ],
        }

    def _parse_ai_recommendations(self, ai_response: str) -> List[Dict[str, Any]]:
        """Parse AI-generated recommendations."""
        # Would parse the AI response
        return []


def main(project_id: str):
    """Run autonomous security audit."""
    auditor = AutonomousAuditor(project_id)
    report = auditor.start_autonomous_audit()

    print("\n🤖 Autonomous Audit Complete!")
    print(f"📊 Summary: {json.dumps(report['summary'], indent=2)}")
    print("\n💡 Top Recommendations:")
    for i, rec in enumerate(report.get("recommendations", [])[:3], 1):
        print(f"{i}. {rec.get('action')} (Priority: {rec.get('priority')})")

    return report


if __name__ == "__main__":
    import fire

    fire.Fire(main)
