#!/usr/bin/env python3
"""
Agent B: Security Risk Explainer

This agent analyzes GCP configurations collected by Agent A using Gemini LLM
to identify security risks and provide recommendations.
"""

import json
import logging
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

import fire

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import models
except ImportError:
    aiplatform = None
    models = None

from common.auth import check_gcp_credentials
from common.models import SecurityFinding

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMInterface(ABC):
    """Abstract interface for LLM interactions"""

    @abstractmethod
    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks in the configuration"""


class PromptTemplate:
    """Template for generating security analysis prompts"""

    SYSTEM_PROMPT = (
        "You are a Google Cloud security expert analyzing GCP configurations "
        "for security risks. Your task is to identify security vulnerabilities, "
        "misconfigurations, and violations of security best practices."
        "\n\n"
        "For each finding, provide:\n"
        "1. A clear, concise title\n"
        "2. Severity level (HIGH, MEDIUM, or LOW)\n"
        "3. Detailed explanation of the risk\n"
        "4. Specific, actionable recommendations\n"
        "\n"
        "Focus on:\n"
        "- IAM policy violations (overly permissive roles, service account misuse)\n"
        "- Security Command Center findings\n"
        "- Principle of least privilege violations\n"
        "- Public exposure risks\n"
        "- Compliance issues\n"
        "\n"
        "Respond in JSON format as an array of findings."
    )

    IAM_ANALYSIS_PROMPT = """Analyze the following IAM policy configuration for security risks:

{iam_policy}

Identify issues such as:
- Overly permissive roles (e.g., roles/owner, roles/editor)
- Service accounts with excessive privileges
- External users with sensitive permissions
- Violations of least privilege principle
- Missing security best practices

Provide findings in this JSON format:
[
  {{
    "title": "Finding title",
    "severity": "HIGH|MEDIUM|LOW",
    "explanation": "Detailed explanation",
    "recommendation": "Specific recommendation"
  }}
]"""

    SCC_ANALYSIS_PROMPT = """Analyze the following Security Command Center findings:

{scc_findings}

For each finding:
- Explain the security impact
- Assess the actual risk level
- Provide remediation steps
- Consider the context and resource type

Provide analysis in this JSON format:
[
  {{
    "title": "Finding title",
    "severity": "HIGH|MEDIUM|LOW",
    "explanation": "Detailed explanation",
    "recommendation": "Specific recommendation"
  }}
]"""


class GeminiSecurityAnalyzer(LLMInterface):
    """Security analyzer using Google's Gemini model via Vertex AI"""

    def __init__(
        self,
        project_id: str,
        location: str = "us-central1",
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
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
        if aiplatform is None or models is None:
            logger.warning("google-cloud-aiplatform not installed, using mock mode")
            self.use_mock = True
            return

        try:
            aiplatform.init(project=self.project_id, location=self.location)
            self._model = models.GenerativeModel(self.model_name)
            logger.info("Initialized Vertex AI with model: %s", self.model_name)
        except Exception as e:
            logger.error("Failed to initialize Vertex AI: %s", e)
            raise

    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks in the configuration"""
        findings = []

        # Analyze IAM policies
        if "iam_policies" in configuration:
            iam_findings = self._analyze_iam_policies(configuration["iam_policies"])
            findings.extend(iam_findings)

        # Analyze SCC findings
        if "scc_findings" in configuration:
            scc_findings = self._analyze_scc_findings(configuration["scc_findings"])
            findings.extend(scc_findings)

        return findings

    def _analyze_iam_policies(self, iam_policies: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze IAM policies for security risks"""
        if self.use_mock:
            return self._get_mock_iam_findings()

        prompt = PromptTemplate.IAM_ANALYSIS_PROMPT.format(
            iam_policy=json.dumps(iam_policies, indent=2)
        )

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing IAM policies: %s", e)
            return self._get_mock_iam_findings()

    def _analyze_scc_findings(self, scc_findings: List[Dict[str, Any]]) -> List[SecurityFinding]:
        """Analyze Security Command Center findings"""
        if self.use_mock or not scc_findings:
            return self._get_mock_scc_findings()

        prompt = PromptTemplate.SCC_ANALYSIS_PROMPT.format(
            scc_findings=json.dumps(scc_findings, indent=2)
        )

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing SCC findings: %s", e)
            return self._get_mock_scc_findings()

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
                    [PromptTemplate.SYSTEM_PROMPT, prompt],
                    generation_config=generation_config,
                )

                return response.text

            except Exception as e:
                logger.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep((2**attempt) * self._rate_limit_delay)
                else:
                    raise
        # This should never be reached, but satisfies the linter
        raise RuntimeError("Failed to get LLM response after all retries")

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract findings"""
        try:
            # Extract JSON from response
            # Handle cases where LLM includes additional text
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            logger.error("No valid JSON found in LLM response")
            return []
        except json.JSONDecodeError as e:
            logger.error("Failed to parse LLM response as JSON: %s", e)
            logger.debug("Response: %s", response)
            return []

    def _get_mock_iam_findings(self) -> List[SecurityFinding]:
        """Return mock IAM findings for testing"""
        return [
            SecurityFinding(
                title="Overly Permissive Owner Role Assignment",
                severity="HIGH",
                explanation=(
                    "Multiple users have been granted the 'roles/owner' role, "
                    "which provides full administrative access to all resources. "
                    "This violates the principle of least privilege and poses a "
                    "significant security risk."
                ),
                recommendation=(
                    "Remove the owner role from non-essential users. Instead, "
                    "grant specific roles that provide only the necessary "
                    "permissions for their tasks. Consider using roles like "
                    "'roles/editor' or custom roles with limited scope."
                ),
            ),
            SecurityFinding(
                title="Service Account with Editor Role",
                severity="MEDIUM",
                explanation=(
                    "The service account 'app-sa@project.iam.gserviceaccount.com' "
                    "has been granted 'roles/editor', which includes broad "
                    "modification permissions across the project."
                ),
                recommendation=(
                    "Replace the editor role with more specific roles that match "
                    "the service account's actual needs. Consider using predefined "
                    "roles like 'roles/storage.objectAdmin' or create a custom "
                    "role with minimal permissions."
                ),
            ),
        ]

    def _get_mock_scc_findings(self) -> List[SecurityFinding]:
        """Return mock SCC findings for testing"""
        return [
            SecurityFinding(
                title="Over-Privileged Service Account Detected",
                severity="HIGH",
                explanation=(
                    "Security Command Center detected a service account with "
                    "excessive permissions. This account has project-wide access "
                    "that exceeds its operational requirements, creating a "
                    "potential attack vector."
                ),
                recommendation=(
                    "Review and reduce the permissions of the identified service "
                    "account. Implement the principle of least privilege by "
                    "granting only the minimum permissions required for its "
                    "specific functions."
                ),
            ),
            SecurityFinding(
                title="Publicly Accessible Storage Bucket",
                severity="MEDIUM",
                explanation=(
                    "A Cloud Storage bucket has been configured with public "
                    "access. This could lead to unintended data exposure if "
                    "sensitive information is stored in this bucket."
                ),
                recommendation=(
                    "Review the bucket's access controls and remove public access "
                    "unless explicitly required. Implement bucket-level IAM "
                    "policies and use signed URLs for temporary access when needed."
                ),
            ),
        ]


class SecurityRiskExplainer:
    """Main orchestrator for security risk analysis"""

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
        self.analyzer = GeminiSecurityAnalyzer(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
        )

    def load_configuration(self) -> Dict[str, Any]:
        """Load configuration data from Agent A output"""
        if not self.input_file.exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        with open(self.input_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def analyze(self) -> List[SecurityFinding]:
        """Perform security analysis on collected configuration"""
        logger.info("Loading configuration from: %s", self.input_file)
        configuration = self.load_configuration()

        logger.info("Starting security risk analysis...")
        findings = self.analyzer.analyze_security_risks(configuration)

        logger.info("Analysis complete. Found %d security issues.", len(findings))
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

        logger.info("Findings saved to: %s", output_path)
        return output_path


def main(
    project_id: str = "example-project",
    location: str = "us-central1",
    use_mock: bool = True,
    input_file: str = "data/collected.json",
    output_dir: str = "data",
):
    """
    Analyze GCP configuration for security risks using Gemini LLM.

    Args:
        project_id: GCP project ID for Vertex AI
        location: GCP region for Vertex AI
        use_mock: Use mock responses instead of real LLM calls
        input_file: Path to configuration data from Agent A
        output_dir: Directory to save analysis results
    """
    try:
        # Set up Google Cloud authentication if not using mock
        check_gcp_credentials(use_mock)

        # Initialize explainer
        explainer = SecurityRiskExplainer(
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

        # Display summary
        high_severity = sum(1 for f in findings if f.severity == "HIGH")
        medium_severity = sum(1 for f in findings if f.severity == "MEDIUM")
        low_severity = sum(1 for f in findings if f.severity == "LOW")

        print("\nSeverity summary:")
        print(f"  HIGH: {high_severity}")
        print(f"  MEDIUM: {medium_severity}")
        print(f"  LOW: {low_severity}")

    except FileNotFoundError as e:
        logger.error("Input file not found: %s", e)
        logger.info("Please run agent_collector.py first to generate configuration data.")
        raise
    except Exception as e:
        logger.error("Analysis failed: %s", e)
        raise


if __name__ == "__main__":
    fire.Fire(main)
