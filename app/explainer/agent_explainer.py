#!/usr/bin/env python3
"""
Agent B: Security Risk Explainer

This agent analyzes GCP configurations collected by Agent A using Gemini LLM
to identify security risks and provide recommendations.
"""

import json
import logging
import os
import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

import fire

try:
    from google.cloud import aiplatform
    from google.cloud.aiplatform import models
except ImportError:
    aiplatform = None
    models = None

from app.common.auth import check_gcp_credentials
from app.common.models import SecurityFinding
from app.explainer.mock_data_factory import MockDataFactory
from app.explainer.prompt_templates import SYSTEM_PROMPT_ENHANCED, build_analysis_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class LLMInterface(ABC):
    """Abstract interface for LLM interactions."""

    @abstractmethod
    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks in the configuration."""


class PromptTemplate:
    """Template for generating security analysis prompts."""

    SYSTEM_PROMPT = (
        "You are a multi-cloud security expert analyzing cloud configurations "
        "for security risks across AWS, Azure, and Google Cloud Platform. "
        "Your task is to identify security vulnerabilities, "
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
        "- Security findings from cloud-native security services\n"
        "- Principle of least privilege violations\n"
        "- Public exposure risks\n"
        "- Compliance issues\n"
        "- Cross-cloud security best practices\n"
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
    """Security analyzer using Google's Gemini model via Vertex AI."""

    def __init__(
        self,
        project_id: str,
        location: str = "asia-northeast1",
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.1,
        max_output_tokens: int = 2048,
        use_mock: bool = False,
        project_context: Optional[Dict[str, Any]] = None,
    ):
        """Initialize GeminiSecurityAnalyzer with configuration."""
        self.project_id = project_id
        self.location = location
        self.model_name = model_name
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.use_mock = use_mock
        self.project_context = project_context or {}
        self._model = None
        self._rate_limit_delay = 1.0  # Delay between API calls in seconds
        self._mock_factory = MockDataFactory()

        if not use_mock:
            self._initialize_vertex_ai()

    def _initialize_vertex_ai(self):
        """Initialize Vertex AI with project settings."""
        if aiplatform is None or models is None:
            logger.warning("google-cloud-aiplatform not installed, using mock mode")
            self.use_mock = True
            return

        try:
            aiplatform.init(project=self.project_id, location=self.location)
            self._model = models.GenerativeModel(self.model_name)  # pylint: disable=no-member
            logger.info("Initialized Vertex AI with model: %s", self.model_name)
        except Exception as e:
            logger.error("Failed to initialize Vertex AI: %s", e)
            raise

    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks in the configuration"""
        findings = []

        # If project context is provided, use enhanced analysis
        if self.project_context:
            # Collect infrastructure findings
            infra_findings = []
            app_findings = []

            if "providers" in configuration:
                for provider_data in configuration["providers"]:
                    provider_name = provider_data.get("provider", "unknown")
                    provider_findings = self._analyze_provider_data(provider_data, provider_name)
                    infra_findings.extend([f.__dict__ for f in provider_findings])
            else:
                # Single provider (backward compatibility)
                if "iam_policies" in configuration:
                    iam_findings = self._analyze_iam_policies(configuration["iam_policies"])
                    infra_findings.extend([f.__dict__ for f in iam_findings])
                if "scc_findings" in configuration:
                    scc_findings = self._analyze_scc_findings(configuration["scc_findings"])
                    infra_findings.extend([f.__dict__ for f in scc_findings])

            # Perform enhanced analysis with context
            return self._analyze_with_context(infra_findings, app_findings)

        # Standard analysis without context
        # Handle multi-cloud data structure
        if "providers" in configuration:
            # Multi-cloud analysis
            for provider_data in configuration["providers"]:
                provider_name = provider_data.get("provider", "unknown")
                provider_findings = self._analyze_provider_data(provider_data, provider_name)
                findings.extend(provider_findings)
        else:
            # Single provider (backward compatibility)
            # Analyze IAM policies
            if "iam_policies" in configuration:
                iam_findings = self._analyze_iam_policies(configuration["iam_policies"])
                findings.extend(iam_findings)

            # Analyze SCC findings
            if "scc_findings" in configuration:
                scc_findings = self._analyze_scc_findings(configuration["scc_findings"])
                findings.extend(scc_findings)

        return findings

    def _analyze_provider_data(
        self, provider_data: Dict[str, Any], provider_name: str
    ) -> List[SecurityFinding]:
        """Analyze data from a specific cloud provider"""
        findings = []

        # Handle error cases
        if "error" in provider_data:
            logger.warning(
                "Skipping %s due to collection error: %s", provider_name, provider_data["error"]
            )
            return findings

        # Analyze IAM/identity data
        if "iam_policies" in provider_data:
            iam_findings = self._analyze_iam_policies(provider_data["iam_policies"], provider_name)
            findings.extend(iam_findings)

        # Analyze security findings
        if "security_findings" in provider_data:
            if provider_name == "gcp":
                security_findings = self._analyze_scc_findings(provider_data["security_findings"])
            else:
                security_findings = self._analyze_cloud_security_findings(
                    provider_data["security_findings"], provider_name
                )
            findings.extend(security_findings)

        return findings

    def _analyze_iam_policies(
        self, iam_policies: Dict[str, Any], provider_name: str = "gcp"
    ) -> List[SecurityFinding]:
        """Analyze IAM policies for security risks"""
        if self.use_mock:
            if provider_name == "aws":
                return self._get_mock_aws_iam_findings()
            if provider_name == "azure":
                return self._get_mock_azure_iam_findings()
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
        last_exception = None

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
                system_prompt = (
                    SYSTEM_PROMPT_ENHANCED
                    if self.project_context
                    else self._get_basic_system_prompt()
                )
                response = self._model.generate_content(
                    [system_prompt, prompt],
                    generation_config=generation_config,
                )

                return response.text

            except Exception as e:
                last_exception = e
                logger.warning("LLM call failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
                if attempt < max_retries - 1:
                    # Exponential backoff
                    time.sleep((2**attempt) * self._rate_limit_delay)

        # If we get here, all retries failed
        raise RuntimeError(
            f"Failed to get LLM response after {max_retries} retries"
        ) from last_exception

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
        return self._mock_factory.create_iam_findings()

    def _analyze_with_context(
        self, infra_findings: List[Dict], app_findings: List[Dict]
    ) -> List[SecurityFinding]:
        """Perform enhanced analysis with project context"""
        if self.use_mock:
            return self._get_enhanced_mock_findings()

        prompt = build_analysis_prompt(infra_findings, app_findings, self.project_context)

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_enhanced_response(response)

            # Convert enhanced format to SecurityFinding objects
            findings = []
            for finding in findings_data:
                # Extract basic fields
                basic_finding = SecurityFinding(
                    title=finding.get("title", "Unknown Finding"),
                    severity=finding.get("severity", "MEDIUM"),
                    explanation=finding.get("explanation", ""),
                    recommendation=finding.get("recommendation", {}).get("summary", ""),
                )

                # Store additional fields in metadata if needed
                # This maintains backward compatibility
                findings.append(basic_finding)

            return findings
        except Exception as e:
            logger.error("Error in enhanced analysis: %s", e)
            return self._get_enhanced_mock_findings()

    def _parse_enhanced_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse enhanced LLM response with extended fields"""
        try:
            # Extract JSON from response
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            if json_start == -1:
                # Try finding single object
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                if json_start != -1 and json_end > json_start:
                    json_str = response[json_start:json_end]
                    return [json.loads(json_str)]
            else:
                if json_end > json_start:
                    json_str = response[json_start:json_end]
                    return json.loads(json_str)

            logger.error("No valid JSON found in enhanced LLM response")
            return []
        except json.JSONDecodeError as e:
            logger.error("Failed to parse enhanced LLM response as JSON: %s", e)
            logger.debug("Response: %s", response)
            return []

    def _get_enhanced_mock_findings(self) -> List[SecurityFinding]:
        """Return enhanced mock findings with full metadata"""
        return self._mock_factory.create_enhanced_findings()

    def _get_basic_system_prompt(self) -> str:
        """Get basic system prompt for backward compatibility"""
        return (
            "You are a multi-cloud security expert analyzing cloud configurations "
            "for security risks across AWS, Azure, and Google Cloud Platform. "
            "Your task is to identify security vulnerabilities, "
            "misconfigurations, and violations of security best practices."
            "\n\n"
            "For each finding, provide:\n"
            "1. A clear, concise title\n"
            "2. Severity level (HIGH, MEDIUM, or LOW)\n"
            "3. Detailed explanation of the risk\n"
            "4. Specific, actionable recommendations\n"
            "\n"
            "Respond in JSON format as an array of findings."
        )

    def _analyze_cloud_security_findings(
        self, security_findings: List[Dict[str, Any]], provider_name: str
    ) -> List[SecurityFinding]:
        """Analyze security findings from AWS Security Hub or Azure Security Center"""
        if self.use_mock or not security_findings:
            return self._get_mock_findings_for_provider(provider_name)

        # For real analysis, format findings for LLM
        prompt = f"""Analyze the following {provider_name.upper()} security findings:

{json.dumps(security_findings, indent=2)}

For each finding:
- Explain the security impact
- Assess the actual risk level
- Provide remediation steps specific to {provider_name.upper()}
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

        try:
            response = self._call_llm_with_retry(prompt)
            findings_data = self._parse_llm_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing %s security findings: %s", provider_name, e)
            return self._get_mock_findings_for_provider(provider_name)

    def _get_mock_findings_for_provider(self, provider_name: str) -> List[SecurityFinding]:
        """Get mock findings for the specified provider"""
        if provider_name == "aws":
            return self._get_mock_aws_security_findings()
        if provider_name == "azure":
            return self._get_mock_azure_security_findings()
        return []

    def _get_mock_aws_iam_findings(self) -> List[SecurityFinding]:
        """Return mock AWS IAM findings"""
        return self._mock_factory.create_provider_iam_findings("aws")

    def _get_mock_azure_iam_findings(self) -> List[SecurityFinding]:
        """Return mock Azure IAM findings"""
        return self._mock_factory.create_provider_iam_findings("azure")

    def _get_mock_aws_security_findings(self) -> List[SecurityFinding]:
        """Return mock AWS Security Hub findings"""
        return self._mock_factory.create_provider_security_findings("aws")

    def _get_mock_azure_security_findings(self) -> List[SecurityFinding]:
        """Return mock Azure Security Center findings"""
        return self._mock_factory.create_provider_security_findings("azure")

    def _get_mock_scc_findings(self) -> List[SecurityFinding]:
        """Return mock SCC findings for testing"""
        return self._mock_factory.create_scc_findings()


def get_analyzer(config: Dict[str, Any]) -> LLMInterface:
    """設定に基づいてAIアナライザーを取得"""
    provider = config.get("ai_provider", "gemini")

    if provider == "ollama":
        from .ollama_explainer import OllamaSecurityAnalyzer

        return OllamaSecurityAnalyzer(
            model=config.get("ollama_model", "gemma3:latest"),
            endpoint=config.get("ollama_endpoint", "http://localhost:11434"),
        )
    # Gemini
    return GeminiSecurityAnalyzer(
        project_id=config["project_id"],
        location=config.get("location", "asia-northeast1"),
        use_mock=config.get("use_mock", False),
        project_context=config.get("project_context"),
    )


class SecurityRiskExplainer:
    """Main orchestrator for security risk analysis"""

    def __init__(
        self,
        project_id: str = None,
        location: str = "asia-northeast1",
        use_mock: bool = False,
        input_file: str = "data/collected.json",
        output_dir: str = "data",
        ai_provider: str = None,
        ollama_model: str = None,
        ollama_endpoint: str = None,
        project_path: Optional[str] = None,
    ):
        """Initialize SecurityRiskExplainer with configuration."""
        self.input_file = Path(input_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.project_id = project_id
        self.location = location
        self.use_mock = use_mock
        self.project_context = {}

        # Collect project context if path provided
        if project_path:
            # Import at function level to avoid circular imports
            # but this makes mocking harder in tests
            from app.explainer.context_collector import ContextCollector

            collector = ContextCollector(project_path)
            self.project_context = collector.collect_project_context()

        # Build config for analyzer factory
        config = {
            "ai_provider": ai_provider or os.getenv("AI_PROVIDER", "gemini"),
            "use_mock": use_mock,
        }

        if config["ai_provider"] == "ollama":
            config["ollama_model"] = ollama_model or os.getenv("OLLAMA_MODEL", "gemma3:latest")
            config["ollama_endpoint"] = ollama_endpoint or os.getenv(
                "OLLAMA_ENDPOINT", "http://localhost:11434"
            )
        else:
            # Gemini requires project_id
            if not project_id:
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
            if not project_id and not use_mock:
                raise ValueError(
                    "project_id is required for Gemini "
                    "(set via parameter or GOOGLE_CLOUD_PROJECT/PROJECT_ID env var)"
                )
            config["project_id"] = project_id
            # Check for location in environment variable
            if not location or location == "asia-northeast1":
                location = os.getenv("VERTEX_AI_LOCATION", "asia-northeast1")
            config["location"] = location

        # Add project context to config
        if self.project_context:
            config["project_context"] = self.project_context

        # Initialize analyzer using factory
        self.analyzer = get_analyzer(config)

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
    project_id: str = None,
    location: str = "asia-northeast1",
    use_mock: bool = True,
    input_file: str = "data/collected.json",
    output_dir: str = "data",
    ai_provider: str = None,
    ollama_model: str = None,
    ollama_endpoint: str = None,
):
    """
    Analyze cloud configuration for security risks using AI.

    Args:
        project_id: GCP project ID for Vertex AI (required for Gemini)
        location: GCP region for Vertex AI
        use_mock: Use mock responses instead of real LLM calls
        input_file: Path to configuration data from Agent A
        output_dir: Directory to save analysis results
        ai_provider: AI provider to use ('gemini' or 'ollama')
        ollama_model: Ollama model name (default: llama3)
        ollama_endpoint: Ollama API endpoint (default: http://localhost:11434)
    """
    try:
        # Determine AI provider
        provider = ai_provider or os.getenv("AI_PROVIDER", "gemini")

        # Set up Google Cloud authentication if using Gemini and not mock
        if provider == "gemini" and not use_mock:
            check_gcp_credentials(use_mock)

        # Initialize explainer
        explainer = SecurityRiskExplainer(
            project_id=project_id,
            location=location,
            use_mock=use_mock,
            input_file=input_file,
            output_dir=output_dir,
            ai_provider=ai_provider,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
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
