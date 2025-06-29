#!/usr/bin/env python3
"""
Recursive Security Auditor Agent

A truly autonomous agent that recursively explores GCP resources
and makes decisions based on findings.
"""

import json
import logging
import os
import time
from datetime import datetime
from typing import Any, Dict, List

from google.cloud import aiplatform
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

logger = logging.getLogger(__name__)
console = Console()


class RecursiveAuditor:
    """Recursive autonomous security auditor."""

    def __init__(self, project_id: str):
        self.project_id = project_id
        self.findings = []
        self.resources_discovered = {}
        self.investigation_queue = []
        self.completed_investigations = set()
        self.decision_history = []
        self.model = self._init_ai()
        self.max_depth = 10
        self.current_depth = 0

    def _init_ai(self):
        """Initialize AI model."""
        try:
            aiplatform.init(project=self.project_id, location="us-central1")
            return aiplatform.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logger.warning(f"AI not available: {e}")
            return None

    def run_autonomous_audit(self) -> Dict[str, Any]:
        """Run fully autonomous security audit."""
        console.print("\n[bold cyan]🤖 Starting Recursive Autonomous Security Audit[/bold cyan]")
        console.print(f"[dim]Project: {self.project_id}[/dim]\n")

        start_time = time.time()

        # Phase 1: Initial Discovery
        console.print("[bold yellow]Phase 1: Resource Discovery[/bold yellow]")
        with Progress(
            SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console
        ) as progress:
            task = progress.add_task("Discovering resources...", total=None)
            self._discover_initial_resources()
            progress.update(task, completed=True)

        # Phase 2: Recursive Investigation
        console.print("\n[bold yellow]Phase 2: Recursive Investigation[/bold yellow]")
        self._run_recursive_investigation()

        # Phase 3: External Research
        console.print("\n[bold yellow]Phase 3: Compliance & Best Practices Research[/bold yellow]")
        self._research_compliance_standards()

        # Phase 4: Generate Recommendations
        console.print("\n[bold yellow]Phase 4: Generating Recommendations[/bold yellow]")
        recommendations = self._generate_recommendations()

        # Create final report
        report = self._create_final_report(recommendations)

        # Display summary
        self._display_audit_summary(report, time.time() - start_time)

        return report

    def _discover_initial_resources(self):
        """Discover initial set of resources."""
        # Import actual collectors
        from google.cloud import storage

        from app.collector.agent_collector import IAMCollector, SCCCollectorAdapter

        # 1. IAM Discovery
        console.print("  [cyan]→ Discovering IAM policies...[/cyan]")
        try:
            iam_collector = IAMCollector(self.project_id, use_mock=False)
            iam_data = iam_collector.collect()
            self.resources_discovered["iam"] = iam_data

            # Analyze IAM for issues
            for binding in iam_data.get("bindings", []):
                self._analyze_iam_binding(binding)
        except Exception as e:
            console.print(f"    [red]✗ IAM discovery failed: {e}[/red]")

        # 2. Storage Discovery
        console.print("  [cyan]→ Discovering storage buckets...[/cyan]")
        try:
            storage_client = storage.Client(project=self.project_id)
            buckets = []
            for bucket in storage_client.list_buckets():
                bucket_info = {
                    "name": bucket.name,
                    "location": bucket.location,
                    "created": str(bucket.time_created),
                    "public": self._check_bucket_public(bucket),
                }
                buckets.append(bucket_info)

                # Queue investigation if public
                if bucket_info["public"]:
                    self._queue_investigation(
                        f"investigate_public_bucket_{bucket.name}",
                        "public_bucket_deep_dive",
                        {"bucket": bucket_info},
                        priority="critical",
                    )

            self.resources_discovered["storage"] = buckets
            console.print(f"    [green]✓ Found {len(buckets)} buckets[/green]")
        except Exception as e:
            console.print(f"    [red]✗ Storage discovery failed: {e}[/red]")

        # 3. Compute Discovery
        console.print("  [cyan]→ Discovering compute instances...[/cyan]")
        try:
            instances = self._discover_compute_instances()
            self.resources_discovered["compute"] = instances
            console.print(f"    [green]✓ Found {len(instances)} instances[/green]")
        except Exception as e:
            console.print(f"    [red]✗ Compute discovery failed: {e}[/red]")

        # 4. Security Findings
        console.print("  [cyan]→ Checking Security Command Center...[/cyan]")
        try:
            scc_collector = SCCCollectorAdapter(
                organization_id="organizations/123456", use_mock=False  # Would get from project
            )
            scc_findings = scc_collector.collect()
            self.resources_discovered["scc_findings"] = scc_findings

            # Queue investigation for each high/critical finding
            for finding in scc_findings:
                if finding.get("severity") in ["HIGH", "CRITICAL"]:
                    self._queue_investigation(
                        f"investigate_scc_{finding.get('name', 'unknown')}",
                        "scc_finding_analysis",
                        {"finding": finding},
                        priority="high",
                    )

            console.print(f"    [green]✓ Found {len(scc_findings)} security findings[/green]")
        except Exception as e:
            console.print(f"    [red]✗ SCC discovery failed: {e}[/red]")

    def _analyze_iam_binding(self, binding: Dict[str, Any]):
        """Analyze IAM binding for security issues."""
        role = binding.get("role", "")
        members = binding.get("members", [])

        # Check for overly permissive roles
        if role in ["roles/owner", "roles/editor"]:
            self.findings.append(
                {
                    "type": "overly_permissive_role",
                    "severity": "HIGH",
                    "resource": f"IAM Role: {role}",
                    "details": f"Role {role} assigned to {len(members)} members",
                    "members": members,
                    "recommendation": "Apply principle of least privilege",
                    "cis_benchmark": "1.2",
                }
            )

            # Queue deeper investigation
            self._queue_investigation(
                f"investigate_role_{role}",
                "role_usage_analysis",
                {"role": role, "members": members},
                priority="high",
            )

        # Check for public access
        for member in members:
            if member in ["allUsers", "allAuthenticatedUsers"]:
                self.findings.append(
                    {
                        "type": "public_iam_access",
                        "severity": "CRITICAL",
                        "resource": f"IAM Role: {role}",
                        "details": f"Public access granted via {member}",
                        "recommendation": "Remove public access immediately",
                    }
                )

    def _queue_investigation(
        self, task_id: str, task_type: str, context: Dict[str, Any], priority: str = "medium"
    ):
        """Queue a new investigation task."""
        if task_id not in self.completed_investigations:
            self.investigation_queue.append(
                {
                    "id": task_id,
                    "type": task_type,
                    "context": context,
                    "priority": priority,
                    "depth": self.current_depth,
                }
            )

    def _run_recursive_investigation(self):
        """Run recursive investigation on queued tasks."""
        investigation_count = 0

        while self.investigation_queue and self.current_depth < self.max_depth:
            # Sort by priority
            self.investigation_queue.sort(
                key=lambda x: {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(
                    x["priority"], 3
                )
            )

            task = self.investigation_queue.pop(0)
            investigation_count += 1

            console.print(f"\n  [cyan]Investigation #{investigation_count}: {task['type']}[/cyan]")
            console.print(f"    [dim]Context: {task['id']}[/dim]")

            # Execute investigation based on type
            if task["type"] == "public_bucket_deep_dive":
                self._investigate_public_bucket(task["context"])
            elif task["type"] == "role_usage_analysis":
                self._investigate_role_usage(task["context"])
            elif task["type"] == "scc_finding_analysis":
                self._investigate_scc_finding(task["context"])

            self.completed_investigations.add(task["id"])
            self.current_depth = max(self.current_depth, task["depth"] + 1)

            # Use AI to decide next steps
            if self.model:
                self._ai_decision_making(task, investigation_count)

    def _investigate_public_bucket(self, context: Dict[str, Any]):
        """Deep dive into public bucket."""
        bucket_info = context["bucket"]
        console.print(
            f"    [yellow]⚠️  Investigating public bucket: " f"{bucket_info['name']}[/yellow]"
        )

        # Check what's in the bucket
        from google.cloud import storage

        client = storage.Client(project=self.project_id)
        bucket = client.bucket(bucket_info["name"])

        try:
            blobs = list(bucket.list_blobs(max_results=10))

            self.findings.append(
                {
                    "type": "public_bucket_content",
                    "severity": "CRITICAL",
                    "resource": f"Storage Bucket: {bucket_info['name']}",
                    "details": f"Public bucket contains {len(blobs)} objects",
                    "sample_files": [blob.name for blob in blobs[:5]],
                    "recommendation": "Remove public access and audit all files",
                    "impact": "Potential data exposure",
                }
            )

            # Check for sensitive file patterns
            sensitive_patterns = [".env", "key", "secret", "password", "credential", ".pem", ".key"]
            for blob in blobs:
                if any(pattern in blob.name.lower() for pattern in sensitive_patterns):
                    self.findings.append(
                        {
                            "type": "sensitive_file_exposed",
                            "severity": "CRITICAL",
                            "resource": f"File: {blob.name}",
                            "bucket": bucket_info["name"],
                            "recommendation": (
                                "Remove file immediately and rotate any exposed credentials"
                            ),
                        }
                    )

        except Exception as e:
            console.print(f"      [red]Failed to list bucket contents: {e}[/red]")

    def _investigate_role_usage(self, context: Dict[str, Any]):
        """Investigate who is using overly permissive roles."""
        role = context["role"]
        members = context["members"]

        console.print(f"    [yellow]Analyzing usage of {role}[/yellow]")

        for member in members:
            if member.startswith("user:"):
                # Check if it's a personal account
                if not member.endswith((".gserviceaccount.com", "@yourdomain.com")):
                    self.findings.append(
                        {
                            "type": "personal_account_admin",
                            "severity": "HIGH",
                            "resource": role,
                            "member": member,
                            "recommendation": "Use corporate accounts only for admin access",
                            "cis_benchmark": "1.1",
                        }
                    )

            elif member.startswith("serviceAccount:"):
                # Queue investigation of what this service account does
                self._queue_investigation(
                    f"investigate_sa_{member}",
                    "service_account_analysis",
                    {"service_account": member, "role": role},
                    priority="high",
                )

    def _investigate_scc_finding(self, context: Dict[str, Any]):
        """Investigate Security Command Center finding."""
        finding = context["finding"]
        console.print(
            f"    [yellow]Analyzing SCC finding: {finding.get('category', 'Unknown')}[/yellow]"
        )

        # Add enhanced finding with investigation results
        self.findings.append(
            {
                "type": "scc_finding_confirmed",
                "severity": finding.get("severity", "MEDIUM"),
                "resource": finding.get("resourceName", "Unknown"),
                "details": finding.get("description", ""),
                "category": finding.get("category", ""),
                "recommendation": finding.get("recommendation", "Follow security best practices"),
                "source": "Security Command Center",
            }
        )

    def _ai_decision_making(self, completed_task: Dict[str, Any], investigation_count: int):
        """Use AI to decide what to investigate next."""
        if not self.model:
            return

        prompt = f"""
        As a security auditor, I just completed this investigation:
        Task: {completed_task['type']}
        Context: {json.dumps(completed_task['context'], indent=2)}

        Current findings count: {len(self.findings)}
        Investigations completed: {investigation_count}
        Current depth: {self.current_depth}

        Based on this investigation, what related security concerns should I investigate next?
        Consider:
        1. Related resources that might have similar issues
        2. Potential attack vectors from this finding
        3. Compliance implications

        Respond with a JSON object containing:
        - investigate_next: boolean (should we investigate more?)
        - reason: string (why this is important)
        - next_investigation: object with 'type', 'target', and 'priority'
        """

        try:
            response = self.model.generate_content(prompt)
            decision = json.loads(response.text)

            self.decision_history.append(
                {
                    "task": completed_task["id"],
                    "decision": decision,
                    "timestamp": datetime.now().isoformat(),
                }
            )

            if decision.get("investigate_next") and decision.get("next_investigation"):
                next_inv = decision["next_investigation"]
                self._queue_investigation(
                    f"ai_suggested_{investigation_count}_{next_inv['type']}",
                    next_inv["type"],
                    {"target": next_inv.get("target"), "reason": decision.get("reason")},
                    priority=next_inv.get("priority", "medium"),
                )
                console.print(f"      [green]AI: {decision.get('reason')}[/green]")

        except Exception as e:
            logger.error(f"AI decision failed: {e}")

    def _research_compliance_standards(self):
        """Research and check compliance standards."""
        # CIS Benchmarks
        console.print("  [cyan]→ Checking CIS Google Cloud Platform Benchmarks...[/cyan]")
        cis_violations = self._check_cis_compliance()

        # Best practices
        console.print("  [cyan]→ Analyzing against security best practices...[/cyan]")
        best_practice_issues = self._check_best_practices()

        self.findings.extend(cis_violations)
        self.findings.extend(best_practice_issues)

    def _check_cis_compliance(self) -> List[Dict[str, Any]]:
        """Check CIS compliance."""
        violations = []

        # CIS 1.1 - Corporate login credentials
        iam_data = self.resources_discovered.get("iam", {})
        for binding in iam_data.get("bindings", []):
            for member in binding.get("members", []):
                if member.startswith("user:") and "@gmail.com" in member:
                    violations.append(
                        {
                            "type": "cis_violation",
                            "severity": "MEDIUM",
                            "benchmark": "CIS 1.1",
                            "resource": "IAM Policy",
                            "details": f"Personal email account used: {member}",
                            "recommendation": "Use corporate login credentials only",
                        }
                    )

        # CIS 3.1 - Default network
        # Would check for default network existence

        return violations

    def _check_best_practices(self) -> List[Dict[str, Any]]:
        """Check security best practices."""
        issues = []

        # Check for missing monitoring
        if not self.resources_discovered.get("logging_configured"):
            issues.append(
                {
                    "type": "best_practice_violation",
                    "severity": "MEDIUM",
                    "category": "Monitoring",
                    "details": "Cloud audit logging may not be fully configured",
                    "recommendation": "Enable comprehensive audit logging for all services",
                }
            )

        return issues

    def _generate_recommendations(self) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations."""
        recommendations = []

        # Group findings by type and severity
        critical_findings = [f for f in self.findings if f.get("severity") == "CRITICAL"]
        high_findings = [f for f in self.findings if f.get("severity") == "HIGH"]

        # Generate recommendations
        if critical_findings:
            recommendations.append(
                {
                    "priority": "CRITICAL",
                    "title": "Address Critical Security Issues Immediately",
                    "description": (
                        f"Found {len(critical_findings)} critical security issues "
                        f"requiring immediate attention"
                    ),
                    "actions": [
                        "Remove all public access from storage buckets",
                        "Rotate any exposed credentials",
                        "Review and restrict IAM permissions",
                    ],
                    "effort": "1-2 days",
                    "impact": "Prevents immediate security breaches",
                }
            )

        if high_findings:
            recommendations.append(
                {
                    "priority": "HIGH",
                    "title": "Implement Least Privilege Access",
                    "description": f"Found {len(high_findings)} high-severity permission issues",
                    "actions": [
                        "Replace Owner/Editor roles with specific permissions",
                        "Audit service account usage",
                        "Implement regular access reviews",
                    ],
                    "effort": "1 week",
                    "impact": "Reduces attack surface significantly",
                }
            )

        # Always recommend monitoring
        recommendations.append(
            {
                "priority": "MEDIUM",
                "title": "Enhance Security Monitoring",
                "description": "Improve visibility into security events",
                "actions": [
                    "Enable Cloud Audit Logs for all services",
                    "Set up alerts for suspicious activities",
                    "Implement regular security assessments",
                ],
                "effort": "2-3 days",
                "impact": "Early detection of security incidents",
            }
        )

        return recommendations

    def _create_final_report(self, recommendations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create final audit report."""
        report = {
            "audit_id": f"recursive_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "project_id": self.project_id,
            "summary": {
                "total_resources": sum(
                    len(v) if isinstance(v, list) else 1 for v in self.resources_discovered.values()
                ),
                "total_findings": len(self.findings),
                "critical_findings": len(
                    [f for f in self.findings if f.get("severity") == "CRITICAL"]
                ),
                "high_findings": len([f for f in self.findings if f.get("severity") == "HIGH"]),
                "investigations_completed": len(self.completed_investigations),
                "ai_decisions_made": len(self.decision_history),
            },
            "resources_discovered": self.resources_discovered,
            "security_findings": self.findings,
            "recommendations": recommendations,
            "investigation_history": list(self.completed_investigations),
            "ai_decision_log": self.decision_history,
            "timestamp": datetime.now().isoformat(),
        }

        # Save report
        self._save_report(report)

        return report

    def _save_report(self, report: Dict[str, Any]):
        """Save report to file."""
        os.makedirs("output", exist_ok=True)

        # JSON report
        json_file = (
            f"output/recursive_audit_{self.project_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(json_file, "w") as f:
            json.dump(report, f, indent=2)

        # Markdown report
        md_file = json_file.replace(".json", ".md")
        self._create_markdown_report(report, md_file)

        console.print("\n[green]📄 Reports saved:[/green]")
        console.print(f"   - JSON: {json_file}")
        console.print(f"   - Markdown: {md_file}")

    def _create_markdown_report(self, report: Dict[str, Any], filename: str):
        """Create markdown report."""
        md_content = f"""# Recursive Security Audit Report

**Project**: {report['project_id']}
**Date**: {report['timestamp']}
**Audit ID**: {report['audit_id']}

## Executive Summary

This autonomous security audit discovered **{report['summary']['total_resources']}** resources and \
identified **{report['summary']['total_findings']}** security findings through \
**{report['summary']['investigations_completed']}** recursive investigations.

### Key Metrics
- 🔴 **Critical Issues**: {report['summary']['critical_findings']}
- 🟠 **High Priority Issues**: {report['summary']['high_findings']}
- 🤖 **AI Decisions Made**: {report['summary']['ai_decisions_made']}

## Top Recommendations

"""
        for i, rec in enumerate(report["recommendations"][:3], 1):
            md_content += f"""### {i}. {rec['title']} ({rec['priority']})

{rec['description']}

**Actions Required:**
"""
            for action in rec["actions"]:
                md_content += f"- {action}\n"
            md_content += f"\n**Effort**: {rec['effort']}  \n**Impact**: {rec['impact']}\n\n"

        # Add critical findings
        critical = [f for f in report["security_findings"] if f.get("severity") == "CRITICAL"]
        if critical:
            md_content += "## Critical Security Findings\n\n"
            for finding in critical[:5]:
                md_content += f"""### {finding.get('type', 'Unknown Issue')}

**Resource**: {finding.get('resource', 'N/A')}
**Details**: {finding.get('details', 'N/A')}
**Recommendation**: {finding.get('recommendation', 'N/A')}

---

"""

        with open(filename, "w") as f:
            f.write(md_content)

    def _display_audit_summary(self, report: Dict[str, Any], duration: float):
        """Display audit summary."""
        # Create summary table
        table = Table(title="Audit Summary", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Resources Discovered", str(report["summary"]["total_resources"]))
        table.add_row("Security Findings", str(report["summary"]["total_findings"]))
        table.add_row("Critical Issues", f"[red]{report['summary']['critical_findings']}[/red]")
        table.add_row(
            "High Priority Issues", f"[yellow]{report['summary']['high_findings']}[/yellow]"
        )
        table.add_row(
            "Investigations Completed", str(report["summary"]["investigations_completed"])
        )
        table.add_row("AI Decisions", str(report["summary"]["ai_decisions_made"]))
        table.add_row("Audit Duration", f"{duration:.2f} seconds")

        console.print("\n")
        console.print(table)

        # Show top findings
        if report["security_findings"]:
            console.print("\n[bold red]Top Security Findings:[/bold red]")
            for i, finding in enumerate(report["security_findings"][:3], 1):
                console.print(
                    f"\n{i}. [red]{finding.get('type', 'Unknown')}[/red] "
                    f"({finding.get('severity', 'UNKNOWN')})"
                )
                console.print(f"   Resource: {finding.get('resource', 'N/A')}")
                console.print(f"   Impact: {finding.get('details', 'N/A')}")

    def _check_bucket_public(self, bucket) -> bool:
        """Check if bucket is publicly accessible."""
        try:
            policy = bucket.get_iam_policy(requested_policy_version=3)
            for binding in policy.bindings:
                if any(
                    member in ["allUsers", "allAuthenticatedUsers"] for member in binding["members"]
                ):
                    return True
        except Exception:
            pass
        return False

    def _discover_compute_instances(self) -> List[Dict[str, Any]]:
        """Discover compute instances."""
        from google.cloud import compute_v1

        instances = []
        try:
            instances_client = compute_v1.InstancesClient()

            # List all zones first
            zones_client = compute_v1.ZonesClient()
            request = compute_v1.ListZonesRequest(project=self.project_id)

            for zone in zones_client.list(request=request):
                try:
                    zone_instances = instances_client.list(project=self.project_id, zone=zone.name)

                    for instance in zone_instances:
                        instance_info = {
                            "name": instance.name,
                            "zone": zone.name,
                            "status": instance.status,
                            "machine_type": instance.machine_type.split("/")[-1],
                            "network_interfaces": len(instance.network_interfaces),
                            "service_accounts": [sa.email for sa in instance.service_accounts],
                            "public_ip": any(
                                nic.access_configs for nic in instance.network_interfaces
                            ),
                        }
                        instances.append(instance_info)

                        # Queue investigation if instance has public IP
                        if instance_info["public_ip"]:
                            self._queue_investigation(
                                f"investigate_public_instance_{instance.name}",
                                "public_instance_analysis",
                                {"instance": instance_info},
                                priority="high",
                            )

                except Exception as e:
                    logger.debug(f"No instances in zone {zone.name}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover compute instances: {e}")

        return instances


def main(project_id: str):
    """Run recursive autonomous security audit."""
    auditor = RecursiveAuditor(project_id)
    report = auditor.run_autonomous_audit()

    console.print("\n[bold green]✅ Autonomous Audit Complete![/bold green]")

    return report


if __name__ == "__main__":
    import fire

    fire.Fire(main)
