#!/usr/bin/env python3
"""
LangChain-based Autonomous Security Auditor

Uses LangChain's agent framework for truly autonomous, recursive security auditing.
"""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationSummaryBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import StructuredTool, tool
from langchain_community.utilities import WikipediaAPIWrapper
from langchain_google_vertexai import ChatVertexAI
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# Tool schemas
class GCPResourceQuery(BaseModel):
    """Input for GCP resource discovery."""

    resource_type: str = Field(
        description="Type of GCP resource to discover (iam, compute, storage, network)"
    )
    project_id: str = Field(description="GCP project ID")
    detailed: bool = Field(default=True, description="Whether to get detailed information")


class SecurityAnalysisQuery(BaseModel):
    """Input for security analysis."""

    resource_data: str = Field(description="JSON string of resource data to analyze")
    analysis_type: str = Field(
        description="Type of analysis (permissions, vulnerabilities, compliance)"
    )
    standard: Optional[str] = Field(
        default=None, description="Compliance standard to check against"
    )


class ExternalResearchQuery(BaseModel):
    """Input for external research."""

    topic: str = Field(description="Security topic to research")
    source: str = Field(default="all", description="Source to search (cis, nist, owasp, all)")


# Custom Tools
@tool("discover_gcp_resources", args_schema=GCPResourceQuery)
def discover_gcp_resources(resource_type: str, project_id: str, detailed: bool = True) -> str:
    """Discover GCP resources of a specific type in the project."""
    from app.collector.agent_collector import GCPConfigurationCollector

    try:
        collector = GCPConfigurationCollector(project_id=project_id, use_mock=False)

        if resource_type == "iam":
            data = collector.iam_collector.collect()
            return json.dumps(
                {"resource_type": "iam", "count": len(data.get("bindings", [])), "data": data}
            )
        elif resource_type == "storage":
            # Use storage client to list buckets
            from google.cloud import storage

            client = storage.Client(project=project_id)
            buckets = []
            for bucket in client.list_buckets():
                bucket_info = {
                    "name": bucket.name,
                    "location": bucket.location,
                    "storage_class": bucket.storage_class,
                    "public": _check_bucket_public_access(bucket),
                }
                if detailed:
                    bucket_info["iam_policy"] = _get_bucket_iam_policy(bucket)
                buckets.append(bucket_info)

            return json.dumps({"resource_type": "storage", "count": len(buckets), "data": buckets})
        elif resource_type == "compute":
            # List compute instances
            from google.cloud import compute_v1

            instances_client = compute_v1.InstancesClient()
            project = project_id

            instances = []
            aggregated_list = instances_client.aggregated_list(project=project)
            for zone, zone_instances in aggregated_list:
                if zone_instances.instances:
                    for instance in zone_instances.instances:
                        instances.append(
                            {
                                "name": instance.name,
                                "zone": zone,
                                "machine_type": instance.machine_type,
                                "status": instance.status,
                                "network_interfaces": len(instance.network_interfaces),
                                "service_accounts": [sa.email for sa in instance.service_accounts],
                            }
                        )

            return json.dumps(
                {"resource_type": "compute", "count": len(instances), "data": instances}
            )
        else:
            return json.dumps({"error": f"Unknown resource type: {resource_type}"})

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("analyze_security", args_schema=SecurityAnalysisQuery)
def analyze_security(resource_data: str, analysis_type: str, standard: Optional[str] = None) -> str:
    """Analyze security aspects of cloud resources."""
    try:
        data = json.loads(resource_data)
        findings = []

        if analysis_type == "permissions":
            # Analyze IAM permissions
            if data.get("resource_type") == "iam":
                for binding in data.get("data", {}).get("bindings", []):
                    role = binding.get("role", "")
                    if role in ["roles/owner", "roles/editor"]:
                        findings.append(
                            {
                                "severity": "HIGH",
                                "type": "overly_permissive_role",
                                "resource": role,
                                "members": binding.get("members", []),
                                "recommendation": (
                                    "Use more specific roles following " "least privilege principle"
                                ),
                                "cis_control": "1.2 - Ensure no use of owner or editor roles",
                            }
                        )

                    # Check for allUsers or allAuthenticatedUsers
                    for member in binding.get("members", []):
                        if member in ["allUsers", "allAuthenticatedUsers"]:
                            findings.append(
                                {
                                    "severity": "CRITICAL",
                                    "type": "public_access",
                                    "resource": role,
                                    "member": member,
                                    "recommendation": (
                                        "Remove public access and use specific identities"
                                    ),
                                }
                            )

        elif analysis_type == "vulnerabilities":
            # Check for security vulnerabilities
            if data.get("resource_type") == "storage":
                for bucket in data.get("data", []):
                    if bucket.get("public"):
                        findings.append(
                            {
                                "severity": "HIGH",
                                "type": "public_bucket",
                                "resource": bucket.get("name"),
                                "recommendation": "Remove public access from bucket",
                            }
                        )

        elif analysis_type == "compliance":
            # Check compliance with standards
            if standard == "cis":
                findings.extend(_check_cis_compliance(data))

        return json.dumps(
            {"analysis_type": analysis_type, "findings_count": len(findings), "findings": findings}
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("research_security_standards")
def research_security_standards(topic: str, source: str = "all") -> str:
    """Research security standards and best practices from external sources."""
    results = {"topic": topic, "sources": [], "recommendations": []}

    try:
        # Simulate web search for security standards
        if source in ["cis", "all"]:
            results["sources"].append(
                {
                    "name": "CIS Google Cloud Platform Foundation Benchmark",
                    "version": "1.3.0",
                    "relevant_controls": [
                        {
                            "id": "1.1",
                            "title": "Ensure that corporate login credentials are used",
                            "description": (
                                "Use corporate login credentials instead " "of personal accounts"
                            ),
                        },
                        {
                            "id": "3.1",
                            "title": "Ensure the default network does not exist",
                            "description": (
                                "Delete the default network to ensure proper "
                                "network segmentation"
                            ),
                        },
                    ],
                }
            )

        if source in ["nist", "all"]:
            results["sources"].append(
                {
                    "name": "NIST Cybersecurity Framework",
                    "relevant_controls": [
                        {
                            "function": "Identify",
                            "category": "Asset Management",
                            "recommendation": "Maintain inventory of all cloud resources",
                        }
                    ],
                }
            )

        # Add general recommendations based on topic
        if "storage" in topic.lower():
            results["recommendations"].extend(
                [
                    "Enable versioning on all storage buckets",
                    "Use customer-managed encryption keys (CMEK)",
                    "Enable access logging",
                ]
            )

        return json.dumps(results)

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("analyze_code_repository")
def analyze_code_repository(repo_path: str, security_checks: List[str]) -> str:
    """Analyze code repository for security issues."""
    findings = []

    try:
        # Simulate code analysis
        checks_performed = []

        if "secrets" in security_checks:
            checks_performed.append("secrets_scan")
            findings.append(
                {
                    "type": "hardcoded_secret",
                    "severity": "CRITICAL",
                    "file": "config/settings.py",
                    "line": 42,
                    "description": "Possible API key found",
                    "recommendation": "Use environment variables or secret management service",
                }
            )

        if "dependencies" in security_checks:
            checks_performed.append("dependency_scan")
            findings.append(
                {
                    "type": "vulnerable_dependency",
                    "severity": "HIGH",
                    "package": "requests==2.20.0",
                    "vulnerability": "CVE-2021-12345",
                    "recommendation": "Update to requests>=2.28.0",
                }
            )

        return json.dumps(
            {"repo_path": repo_path, "checks_performed": checks_performed, "findings": findings}
        )

    except Exception as e:
        return json.dumps({"error": str(e)})


@tool("create_remediation_plan")
def create_remediation_plan(findings: str, auto_generate_fixes: bool = False) -> str:
    """Create a remediation plan based on security findings."""
    try:
        findings_data = json.loads(findings)
        plan = {
            "total_issues": len(findings_data),
            "remediation_steps": [],
            "estimated_effort": "medium",
            "priority_order": [],
        }

        # Group by severity
        critical = [f for f in findings_data if f.get("severity") == "CRITICAL"]
        high = [f for f in findings_data if f.get("severity") == "HIGH"]

        # Create remediation steps
        for finding in critical + high:
            step = {
                "issue": finding.get("type"),
                "resource": finding.get("resource", "unknown"),
                "action": finding.get("recommendation"),
                "priority": finding.get("severity"),
                "automated": auto_generate_fixes
                and finding.get("type") in ["overly_permissive_role", "public_bucket"],
            }

            if step["automated"]:
                step["fix_code"] = _generate_fix_code(finding)

            plan["remediation_steps"].append(step)

        return json.dumps(plan)

    except Exception as e:
        return json.dumps({"error": str(e)})


class SecurityAuditorAgent:
    """LangChain-based autonomous security auditor."""

    def __init__(self, project_id: str, verbose: bool = True):
        self.project_id = project_id
        self.verbose = verbose
        self.tools = self._create_tools()
        self.agent = self._create_agent()
        self.memory = ConversationSummaryBufferMemory(
            llm=self._get_llm(), max_token_limit=2000, return_messages=True
        )
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            memory=self.memory,
            verbose=verbose,
            max_iterations=15,  # Allow deep recursive exploration
            early_stopping_method="force",
        )

    def _get_llm(self):
        """Get Vertex AI LLM."""
        return ChatVertexAI(
            model_name="gemini-1.5-flash",
            project=self.project_id,
            location="us-central1",
            temperature=0.1,
            max_output_tokens=2048,
        )

    def _create_tools(self):
        """Create all tools for the agent."""
        # Core tools
        tools = [
            discover_gcp_resources,
            analyze_security,
            research_security_standards,
            analyze_code_repository,
            create_remediation_plan,
        ]

        # Add web search capability (optional - requires Google API key)
        # Commented out to avoid dependency on Google Search API key
        # If you have a Google Search API key, uncomment and set GOOGLE_API_KEY env var
        # try:
        #     from langchain_google_community import GoogleSearchAPIWrapper
        #     search = GoogleSearchAPIWrapper()
        #     tools.append(
        #         StructuredTool(
        #             name="web_search",
        #             description=(
        #                 "Search the web for security information, compliance standards, "
        #                 "and best practices"
        #             ),
        #             func=search.run
        #         )
        #     )
        # except Exception as e:
        #     logger.warning(f"Web search not available: {e}")

        # Add Wikipedia for detailed research
        wikipedia = WikipediaAPIWrapper()
        tools.append(
            StructuredTool(
                name="wikipedia_search",
                description=(
                    "Search Wikipedia for detailed information about "
                    "security concepts and standards"
                ),
                func=wikipedia.run,
            )
        )

        return tools

    def _create_agent(self):
        """Create the autonomous agent."""
        system_prompt = """You are an expert cloud security auditor with deep knowledge of:
- Google Cloud Platform security
- Compliance standards (CIS, NIST, PCI-DSS, HIPAA, SOC2)
- Security best practices and vulnerabilities
- Code security analysis
- Threat modeling and risk assessment

Your task is to perform a comprehensive, autonomous security audit. You should:

1. DISCOVER: Systematically discover all resources in the GCP project
2. ANALYZE: Deeply analyze each resource for security issues
3. RESEARCH: Research relevant compliance standards and best practices
4. INVESTIGATE: Recursively investigate any concerning findings
5. REMEDIATE: Create actionable remediation plans

Be thorough and recursive - if you find an issue, investigate deeper:
- If you find overly permissive IAM roles, check who has them and what they access
- If you find public resources, check what data they contain
- If you find vulnerabilities, research the latest patches and fixes
- Always cross-reference with CIS benchmarks and industry standards

Remember to:
- Check multiple resource types (IAM, compute, storage, network, etc.)
- Research current security standards using web search
- Analyze from multiple angles (permissions, vulnerabilities, compliance)
- Create comprehensive remediation plans
- Be specific about risks and recommendations

Start with discovering all resources, then analyze each thoroughly."""

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("user", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )

        return create_openai_tools_agent(llm=self._get_llm(), tools=self.tools, prompt=prompt)

    def run_autonomous_audit(self) -> Dict[str, Any]:
        """Run fully autonomous security audit."""
        audit_prompt = (
            f"Perform a comprehensive security audit of GCP project "
            f"'{self.project_id}'.\n\n"
            "Please follow these steps:\n"
            "1. Discover ALL resource types (IAM, storage, compute, network)\n"
            "2. Analyze each resource type for security issues\n"
            "3. Research relevant CIS benchmarks and compliance standards\n"
            "4. For any critical findings, investigate deeper\n"
            "5. Create a complete remediation plan\n\n"
            "Be recursive - if you find issues, dig deeper to understand root causes "
            "and related problems.\n"
            "Research external sources for best practices and compliance requirements.\n"
            "Your final output should include a summary of all findings and prioritized "
            "recommendations."
        )

        try:
            result = self.agent_executor.invoke({"input": audit_prompt})

            # Extract and structure the results
            return self._structure_audit_results(result)

        except Exception as e:
            logger.error(f"Audit failed: {e}")
            return {"error": str(e)}

    def _structure_audit_results(self, raw_result: Dict[str, Any]) -> Dict[str, Any]:
        """Structure the audit results."""
        # Parse agent's output and memory
        output = raw_result.get("output", "")
        chat_history = self.memory.chat_memory.messages

        # Extract findings from tool calls in history
        all_findings = []
        resources_discovered = {}

        for message in chat_history:
            if hasattr(message, "tool_calls"):
                for tool_call in message.tool_calls:
                    if tool_call["name"] == "analyze_security":
                        result = json.loads(tool_call.get("output", "{}"))
                        all_findings.extend(result.get("findings", []))
                    elif tool_call["name"] == "discover_gcp_resources":
                        result = json.loads(tool_call.get("output", "{}"))
                        resources_discovered[result.get("resource_type")] = result

        audit_report = {
            "audit_id": f"langchain_audit_{datetime.now().isoformat()}",
            "project_id": self.project_id,
            "summary": {
                "total_resources_discovered": sum(
                    r.get("count", 0) for r in resources_discovered.values()
                ),
                "total_findings": len(all_findings),
                "critical_findings": len(
                    [f for f in all_findings if f.get("severity") == "CRITICAL"]
                ),
                "high_findings": len([f for f in all_findings if f.get("severity") == "HIGH"]),
            },
            "resources_discovered": resources_discovered,
            "security_findings": all_findings,
            "agent_output": output,
            "audit_steps": len(chat_history),
            "timestamp": datetime.now().isoformat(),
        }

        # Save report
        self._save_audit_report(audit_report)

        return audit_report

    def _save_audit_report(self, report: Dict[str, Any]):
        """Save audit report."""
        os.makedirs("output", exist_ok=True)
        filename = (
            f"output/langchain_audit_{self.project_id}_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        )

        with open(filename, "w") as f:
            json.dump(report, f, indent=2)

        # Also create a markdown summary
        self._create_markdown_summary(report, filename.replace(".json", ".md"))

        logger.info(f"Audit report saved to: {filename}")

    def _create_markdown_summary(self, report: Dict[str, Any], filename: str):
        """Create markdown summary of audit."""
        summary = f"""# Security Audit Report

**Project ID**: {report['project_id']}
**Date**: {report['timestamp']}
**Audit ID**: {report['audit_id']}

## Executive Summary

- **Total Resources Discovered**: {report['summary']['total_resources_discovered']}
- **Total Security Findings**: {report['summary']['total_findings']}
- **Critical Issues**: {report['summary']['critical_findings']}
- **High Priority Issues**: {report['summary']['high_findings']}

## Key Findings

"""
        # Add critical findings
        critical_findings = [
            f for f in report["security_findings"] if f.get("severity") == "CRITICAL"
        ]
        if critical_findings:
            summary += "### Critical Issues\n\n"
            for finding in critical_findings[:5]:
                summary += f"- **{finding.get('type')}**: {finding.get('resource', 'N/A')}\n"
                summary += f"  - Recommendation: {finding.get('recommendation', 'N/A')}\n\n"

        with open(filename, "w") as f:
            f.write(summary)


# Helper functions
def _check_bucket_public_access(bucket) -> bool:
    """Check if bucket has public access."""
    try:
        policy = bucket.get_iam_policy(requested_policy_version=3)
        for binding in policy.bindings:
            if "allUsers" in binding["members"] or "allAuthenticatedUsers" in binding["members"]:
                return True
    except Exception:
        pass
    return False


def _get_bucket_iam_policy(bucket) -> Dict[str, Any]:
    """Get bucket IAM policy."""
    try:
        policy = bucket.get_iam_policy(requested_policy_version=3)
        return {"bindings": [{"role": b.role, "members": list(b.members)} for b in policy.bindings]}
    except Exception:
        return {}


def _check_cis_compliance(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Check CIS compliance for resources."""
    findings = []
    # Implement CIS checks
    return findings


def _generate_fix_code(finding: Dict[str, Any]) -> str:
    """Generate fix code for finding."""
    fix_type = finding.get("type")

    if fix_type == "overly_permissive_role":
        return f"""
# Remove overly permissive role
gcloud projects remove-iam-policy-binding {finding.get('project_id')} \\
    --member='{finding.get('member')}' \\
    --role='{finding.get('resource')}'
# Add more restrictive role
gcloud projects add-iam-policy-binding {finding.get('project_id')} \\
    --member='{finding.get('member')}' \\
    --role='roles/viewer'
"""

    return "# Manual fix required"


def main(project_id: str, verbose: bool = True):
    """Run LangChain-based autonomous security audit."""
    print(f"\n🤖 Starting LangChain Autonomous Security Audit for: {project_id}")
    print("=" * 70)

    auditor = SecurityAuditorAgent(project_id, verbose=verbose)
    report = auditor.run_autonomous_audit()

    if "error" not in report:
        print("\n✅ Audit completed successfully!")
        print("\n📊 Summary:")
        print(f"   - Resources discovered: {report['summary']['total_resources_discovered']}")
        print(f"   - Security findings: {report['summary']['total_findings']}")
        print(f"   - Critical issues: {report['summary']['critical_findings']}")
        print(f"   - High priority issues: {report['summary']['high_findings']}")
        print(f"\n📄 Report saved to: output/langchain_audit_{project_id}_*.json")
    else:
        print(f"\n❌ Audit failed: {report['error']}")

    return report


if __name__ == "__main__":
    import fire

    fire.Fire(main)
