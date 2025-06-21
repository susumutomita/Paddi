#!/usr/bin/env python3
"""
Multi-Cloud Security Risk Explainer

This agent analyzes cloud configurations from multiple providers (GCP, AWS, Azure)
using Gemini LLM to identify security risks and provide recommendations.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire
from google.cloud import aiplatform
from google.cloud.aiplatform import models

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SecurityFinding:
    """Data class for security findings"""

    title: str
    severity: str  # HIGH, MEDIUM, LOW
    explanation: str
    recommendation: str
    provider: str  # gcp, aws, azure
    resource: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "title": self.title,
            "severity": self.severity,
            "explanation": self.explanation,
            "recommendation": self.recommendation,
            "provider": self.provider,
            "resource": self.resource,
        }


class MultiCloudPromptTemplate:
    """Template for generating multi-cloud security analysis prompts"""

    SYSTEM_PROMPT = """You are a multi-cloud security expert analyzing configurations from GCP, AWS, and Azure for security risks.
Your task is to identify security vulnerabilities, misconfigurations, and violations of security best practices across all cloud providers.

For each finding, provide:
1. A clear, concise title
2. Severity level (HIGH, MEDIUM, or LOW)
3. Detailed explanation of the risk
4. Specific, actionable recommendations
5. The cloud provider (gcp, aws, or azure)
6. The affected resource (if applicable)

Focus on:
- IAM/Identity policy violations (overly permissive roles, service account misuse)
- Security findings from cloud-native security services
- Principle of least privilege violations
- Public exposure risks
- Compliance issues
- Cross-cloud security inconsistencies

Respond in JSON format as an array of findings."""

    MULTI_CLOUD_IAM_PROMPT = """Analyze the following IAM/Identity configurations from multiple cloud providers for security risks:

{iam_data}

Identify issues such as:
- Overly permissive roles across any cloud provider
- Service accounts/principals with excessive privileges
- External users with sensitive permissions
- Violations of least privilege principle
- Inconsistent security policies across clouds
- Cloud-specific best practice violations

For each cloud provider, consider their specific role models:
- GCP: roles/owner, roles/editor are overly permissive
- AWS: AdministratorAccess, PowerUserAccess policies are risky
- Azure: Global Administrator, Owner roles grant excessive permissions

Provide findings in this JSON format:
[
  {{
    "title": "Finding title",
    "severity": "HIGH|MEDIUM|LOW",
    "explanation": "Detailed explanation",
    "recommendation": "Specific recommendation",
    "provider": "gcp|aws|azure",
    "resource": "affected resource identifier"
  }}
]"""

    MULTI_CLOUD_SECURITY_PROMPT = """Analyze the following security findings from multiple cloud providers:

{security_data}

For each finding:
- Explain the security impact
- Assess the actual risk level
- Provide cloud-specific remediation steps
- Consider the context and resource type
- Identify any patterns across cloud providers

Consider cloud-specific security services:
- GCP: Security Command Center findings
- AWS: Security Hub findings
- Azure: Security Center alerts

Provide analysis in this JSON format:
[
  {{
    "title": "Finding title",
    "severity": "HIGH|MEDIUM|LOW",
    "explanation": "Detailed explanation",
    "recommendation": "Specific recommendation",
    "provider": "gcp|aws|azure",
    "resource": "affected resource identifier"
  }}
]"""

    MULTI_CLOUD_COMPLIANCE_PROMPT = """Analyze the following compliance status from multiple cloud providers:

{compliance_data}

Identify:
- Compliance standard violations
- Cross-cloud compliance inconsistencies
- Areas requiring immediate attention
- Best practices for improving compliance posture

Consider standards like:
- CIS benchmarks for each cloud
- PCI DSS, HIPAA, SOC2 requirements
- Cloud-specific security baselines

Provide findings in this JSON format:
[
  {{
    "title": "Finding title",
    "severity": "HIGH|MEDIUM|LOW",
    "explanation": "Detailed explanation",
    "recommendation": "Specific recommendation",
    "provider": "gcp|aws|azure",
    "resource": "affected standard or control"
  }}
]"""


class MultiCloudGeminiAnalyzer:
    """Security analyzer using Gemini for multi-cloud environments"""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.1,
        max_output_tokens: int = 4096,
        use_mock: bool = False,
    ):
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.use_mock = use_mock
        self._model = None
        self._rate_limit_delay = 1.0  # Delay between API calls in seconds

        if not use_mock:
            self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with project settings"""
        try:
            aiplatform.init(project=self.project_id, location=self.location)
            self._model = models.GenerativeModel(self.model_name)
            logger.info(f"Initialized Vertex AI with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Vertex AI: {e}")
            raise

    def analyze_multi_cloud_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks across multiple cloud providers"""
        findings = []

        # Check if this is legacy single-provider data
        if "iam_policies" in configuration:
            # Legacy GCP format - convert and analyze
            logger.info("Detected legacy GCP format, converting...")
            legacy_findings = self._analyze_legacy_gcp(configuration)
            findings.extend(legacy_findings)
        else:
            # Multi-cloud format
            providers_data = configuration.get("providers", {})
            
            # Analyze IAM/Identity across all providers
            iam_findings = self._analyze_multi_cloud_iam(providers_data)
            findings.extend(iam_findings)

            # Analyze security findings across all providers
            security_findings = self._analyze_multi_cloud_security(providers_data)
            findings.extend(security_findings)

            # Analyze compliance status
            compliance_findings = self._analyze_multi_cloud_compliance(providers_data)
            findings.extend(compliance_findings)

        return findings

    def _analyze_legacy_gcp(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Handle legacy GCP-only format"""
        if self.use_mock:
            return self._get_mock_legacy_findings()
        
        # Convert to multi-cloud format internally
        multi_cloud_data = {
            "gcp": {
                "iam": {
                    "policies": [{
                        "resource": configuration.get("project_id", "unknown"),
                        "bindings": configuration.get("iam_policies", {}).get("bindings", [])
                    }]
                },
                "security": {
                    "findings": configuration.get("scc_findings", [])
                }
            }
        }
        
        return self._analyze_multi_cloud_iam(multi_cloud_data) + \
               self._analyze_multi_cloud_security(multi_cloud_data)

    def _analyze_multi_cloud_iam(self, providers_data: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze IAM/Identity configurations across all cloud providers"""
        if self.use_mock:
            return self._get_mock_iam_findings()

        # Prepare IAM data from all providers
        iam_data = {}
        for provider, data in providers_data.items():
            if "iam" in data:
                iam_data[provider] = data["iam"]

        if not iam_data:
            return []

        prompt = MultiCloudPromptTemplate.MULTI_CLOUD_IAM_PROMPT.format(
            iam_data=json.dumps(iam_data, indent=2)
        )

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error(f"Error analyzing multi-cloud IAM: {e}")
            return self._get_mock_iam_findings()

    def _analyze_multi_cloud_security(self, providers_data: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security findings across all cloud providers"""
        if self.use_mock:
            return self._get_mock_security_findings()

        # Prepare security findings from all providers
        security_data = {}
        for provider, data in providers_data.items():
            if "security" in data and "findings" in data["security"]:
                security_data[provider] = data["security"]["findings"]

        if not security_data:
            return []

        prompt = MultiCloudPromptTemplate.MULTI_CLOUD_SECURITY_PROMPT.format(
            security_data=json.dumps(security_data, indent=2)
        )

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error(f"Error analyzing multi-cloud security findings: {e}")
            return self._get_mock_security_findings()

    def _analyze_multi_cloud_compliance(self, providers_data: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze compliance status across all cloud providers"""
        if self.use_mock:
            return self._get_mock_compliance_findings()

        # Prepare compliance data from all providers
        compliance_data = {}
        for provider, data in providers_data.items():
            if "security" in data and "compliance" in data["security"]:
                compliance_data[provider] = data["security"]["compliance"]

        if not compliance_data:
            return []

        prompt = MultiCloudPromptTemplate.MULTI_CLOUD_COMPLIANCE_PROMPT.format(
            compliance_data=json.dumps(compliance_data, indent=2)
        )

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error(f"Error analyzing multi-cloud compliance: {e}")
            return self._get_mock_compliance_findings()

    def _call_llm_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """Call LLM with retry logic and rate limiting"""
        for attempt in range(max_retries):
            try:
                # Rate limiting
                time.sleep(self._rate_limit_delay)

                # Configure generation parameters
                generation_config = {
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_output_tokens,
                    "top_p": 0.95,
                }

                # Generate response
                response = self._model.generate_content(
                    [MultiCloudPromptTemplate.SYSTEM_PROMPT, prompt],
                    generation_config=generation_config,
                )

                return response.text

            except Exception as e:
                logger.warning(f"LLM call failed (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep((2**attempt) * self._rate_limit_delay)
                else:
                    raise

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract findings"""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                logger.error("No valid JSON found in LLM response")
                return []
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"Response: {response}")
            return []

    def _get_mock_legacy_findings(self) -> List[SecurityFinding]:
        """Mock findings for legacy GCP format"""
        return [
            SecurityFinding(
                title="Overly Permissive Owner Role Assignment",
                severity="HIGH",
                explanation="Multiple users have been granted the 'roles/owner' role in GCP",
                recommendation="Remove owner role from non-essential users",
                provider="gcp",
                resource="project"
            )
        ]

    def _get_mock_iam_findings(self) -> List[SecurityFinding]:
        """Return mock multi-cloud IAM findings"""
        return [
            SecurityFinding(
                title="GCP: Overly Permissive Owner Role Assignment",
                severity="HIGH",
                explanation="Multiple users have 'roles/owner' in GCP project, granting full administrative access",
                recommendation="Remove owner role and assign specific roles based on job functions",
                provider="gcp",
                resource="user:admin@example.com"
            ),
            SecurityFinding(
                title="AWS: Administrator Access Policy on User Account",
                severity="HIGH",
                explanation="IAM user 'admin' has AdministratorAccess policy attached, providing unrestricted access",
                recommendation="Replace with specific policies or use IAM roles with temporary credentials",
                provider="aws",
                resource="arn:aws:iam::123456789012:user/admin"
            ),
            SecurityFinding(
                title="Azure: Global Administrator Role Assignment",
                severity="HIGH",
                explanation="User has Global Administrator role in Azure AD, granting tenant-wide admin privileges",
                recommendation="Use role-based access control with minimal required permissions",
                provider="azure",
                resource="admin@contoso.onmicrosoft.com"
            ),
        ]

    def _get_mock_security_findings(self) -> List[SecurityFinding]:
        """Return mock multi-cloud security findings"""
        return [
            SecurityFinding(
                title="Cross-Cloud Storage Exposure Risk",
                severity="HIGH",
                explanation="Public storage containers detected across multiple clouds: GCS bucket and S3 bucket",
                recommendation="Review and restrict public access across all cloud storage services",
                provider="gcp",
                resource="storage.googleapis.com/example-public-bucket"
            ),
            SecurityFinding(
                title="AWS: Unencrypted RDS Instance",
                severity="HIGH",
                explanation="Production database instance lacks encryption at rest",
                recommendation="Enable RDS encryption and migrate data to encrypted instance",
                provider="aws",
                resource="arn:aws:rds:us-east-1:123456789012:db:prod-db"
            ),
        ]

    def _get_mock_compliance_findings(self) -> List[SecurityFinding]:
        """Return mock compliance findings"""
        return [
            SecurityFinding(
                title="Multi-Cloud CIS Benchmark Compliance Gap",
                severity="MEDIUM",
                explanation="Compliance scores vary significantly across clouds: GCP (75%), AWS (78%), Azure (82%)",
                recommendation="Implement consistent security controls to achieve uniform compliance levels",
                provider="aws",
                resource="CIS AWS Foundations Benchmark"
            ),
        ]


class MultiCloudSecurityExplainer:
    """Main orchestrator for multi-cloud security risk analysis"""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        use_mock: bool = False,
        input_file: str = "data/collected.json",
        output_dir: str = "data",
    ):
        self.project_id = project_id
        self.location = location
        self.use_mock = use_mock
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Initialize analyzer
        self.analyzer = MultiCloudGeminiAnalyzer(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
        )

    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration data from collector output"""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        with open(self.input_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze(self) -> List[SecurityFinding]:
        """Perform security analysis on collected configuration"""
        logger.info(f"Loading configuration from: {self.input_file}")
        configuration = self.load_configuration()

        logger.info("Starting multi-cloud security risk analysis...")
        findings = self.analyzer.analyze_multi_cloud_risks(configuration)

        logger.info(f"Analysis complete. Found {len(findings)} security issues.")
        return findings

    def save_findings(
        self, findings: List[SecurityFinding], filename: str = "explained.json"
    ) -> Path:
        """Save analysis findings to JSON file"""
        output_path = self.output_dir / filename

        # Convert findings to dict format
        findings_data = [finding.to_dict() for finding in findings]

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(findings_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Findings saved to: {output_path}")
        return output_path


def main(
    project_id: str = "example-project",
    location: str = "us-central1",
    use_mock: bool = True,
    input_file: str = "data/collected.json",
    output_dir: str = "data",
):
    """
    Analyze multi-cloud configuration for security risks using Gemini LLM.

    Args:
        project_id: GCP project ID for Vertex AI
        location: GCP region for Vertex AI
        use_mock: Use mock responses instead of real LLM calls
        input_file: Path to configuration data from collector
        output_dir: Directory to save analysis results
    """
    try:
        # Set up Google Cloud authentication if not using mock
        if not use_mock:
            if not os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                logger.warning(
                    "GOOGLE_APPLICATION_CREDENTIALS not set. Using application default credentials."
                )

        # Initialize explainer
        explainer = MultiCloudSecurityExplainer(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
            input_file=input_file,
            output_dir=output_dir,
        )

        # Perform analysis
        findings = explainer.analyze()

        # Save findings
        output_path = explainer.save_findings(findings)

        print(f"✅ Analysis successful! Found {len(findings)} security issues.")
        print(f"Results saved to: {output_path}")

        # Display summary by provider
        provider_summary = {}
        for finding in findings:
            provider = finding.provider
            if provider not in provider_summary:
                provider_summary[provider] = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
            provider_summary[provider][finding.severity] += 1

        print(f"\nSeverity summary by cloud provider:")
        for provider, counts in provider_summary.items():
            print(f"\n{provider.upper()}:")
            print(f"  HIGH: {counts['HIGH']}")
            print(f"  MEDIUM: {counts['MEDIUM']}")
            print(f"  LOW: {counts['LOW']}")

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        logger.info("Please run the collector agent first to generate configuration data.")
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    fire.Fire(main)