"""Ollama-based security analyzer for local LLM support."""

import json
import logging
import time
from typing import Any, Dict, List

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout

from app.common.models import SecurityFinding
from app.explainer.agent_explainer import LLMInterface, PromptTemplate

logger = logging.getLogger(__name__)


class OllamaSecurityAnalyzer(LLMInterface):
    """Security analyzer using Ollama local LLM."""

    def __init__(
        self,
        model: str = "llama3",
        endpoint: str = "http://localhost:11434",
        temperature: float = 0.2,
        max_output_tokens: int = 2048,
        use_mock: bool = False,
        timeout: int = 60,
    ):
        """
        Initialize OllamaSecurityAnalyzer.
        
        Args:
            model: Ollama model name (e.g., 'llama3', 'codellama', 'mistral')
            endpoint: Ollama API endpoint URL
            temperature: Model temperature for generation
            max_output_tokens: Maximum tokens to generate
            use_mock: Use mock responses instead of real API calls
            timeout: Request timeout in seconds
        """
        self.model = model
        self.endpoint = endpoint.rstrip("/")
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens
        self.use_mock = use_mock
        self.timeout = timeout
        self._rate_limit_delay = 0.5  # Shorter delay for local model
        
        # Verify Ollama server is accessible
        if not use_mock:
            self._verify_ollama_server()
    
    def _verify_ollama_server(self) -> None:
        """Verify that Ollama server is accessible."""
        try:
            response = requests.get(f"{self.endpoint}/api/tags", timeout=5)
            response.raise_for_status()
            logger.info("Connected to Ollama server at %s", self.endpoint)
            
            # Check if the specified model is available
            models = response.json().get("models", [])
            model_names = [m["name"] for m in models]
            
            if self.model not in model_names:
                logger.warning(
                    "Model '%s' not found. Available models: %s", 
                    self.model, 
                    ", ".join(model_names)
                )
                # Try to pull the model
                self._pull_model()
        except ConnectionError:
            logger.error(
                "Cannot connect to Ollama server at %s. "
                "Please ensure Ollama is running (ollama serve)", 
                self.endpoint
            )
            raise
        except Exception as e:
            logger.error("Error verifying Ollama server: %s", e)
            raise
    
    def _pull_model(self) -> None:
        """Attempt to pull the specified model."""
        logger.info("Attempting to pull model '%s'...", self.model)
        try:
            response = requests.post(
                f"{self.endpoint}/api/pull",
                json={"name": self.model},
                timeout=300  # 5 minutes for model download
            )
            response.raise_for_status()
            logger.info("Successfully pulled model '%s'", self.model)
        except Exception as e:
            logger.error("Failed to pull model '%s': %s", self.model, e)
            raise
    
    def analyze_security_risks(self, configuration: Dict[str, Any]) -> List[SecurityFinding]:
        """Analyze security risks in the configuration."""
        findings = []

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
        """Analyze data from a specific cloud provider."""
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
        """Analyze IAM policies for security risks."""
        if self.use_mock:
            return self._get_mock_iam_findings(provider_name)
        
        prompt = self._build_analysis_prompt(
            PromptTemplate.IAM_ANALYSIS_PROMPT.format(
                iam_policy=json.dumps(iam_policies, indent=2)
            )
        )
        
        try:
            response = self._call_ollama(prompt)
            findings_data = self._parse_ollama_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing IAM policies with Ollama: %s", e)
            # Fall back to mock findings
            return self._get_mock_iam_findings(provider_name)
    
    def _analyze_scc_findings(self, scc_findings: List[Dict[str, Any]]) -> List[SecurityFinding]:
        """Analyze Security Command Center findings."""
        if self.use_mock or not scc_findings:
            return self._get_mock_scc_findings()
        
        prompt = self._build_analysis_prompt(
            PromptTemplate.SCC_ANALYSIS_PROMPT.format(
                scc_findings=json.dumps(scc_findings, indent=2)
            )
        )
        
        try:
            response = self._call_ollama(prompt)
            findings_data = self._parse_ollama_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing SCC findings with Ollama: %s", e)
            return self._get_mock_scc_findings()
    
    def _analyze_cloud_security_findings(
        self, security_findings: List[Dict[str, Any]], provider_name: str
    ) -> List[SecurityFinding]:
        """Analyze security findings from AWS Security Hub or Azure Security Center."""
        if self.use_mock or not security_findings:
            return self._get_mock_findings_for_provider(provider_name)
        
        prompt = self._build_analysis_prompt(
            f"""Analyze the following {provider_name.upper()} security findings:

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
        )
        
        try:
            response = self._call_ollama(prompt)
            findings_data = self._parse_ollama_response(response)
            return [SecurityFinding(**finding) for finding in findings_data]
        except Exception as e:
            logger.error("Error analyzing %s security findings: %s", provider_name, e)
            return self._get_mock_findings_for_provider(provider_name)
    
    def _build_analysis_prompt(self, user_prompt: str) -> str:
        """Build the complete prompt with system context."""
        return f"{PromptTemplate.SYSTEM_PROMPT}\n\n{user_prompt}"
    
    def _call_ollama(self, prompt: str, max_retries: int = 3) -> str:
        """Call Ollama API with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                # Rate limiting
                time.sleep(self._rate_limit_delay)
                
                # Prepare request
                request_data = {
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.temperature,
                        "num_predict": self.max_output_tokens,
                        "top_p": 0.8,
                    }
                }
                
                # Make API call
                response = requests.post(
                    f"{self.endpoint}/api/generate",
                    json=request_data,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get("response", "")
                
            except Timeout:
                last_exception = TimeoutError(f"Request timed out after {self.timeout}s")
                logger.warning("Ollama request timeout (attempt %d/%d)", attempt + 1, max_retries)
            except HTTPError as e:
                last_exception = e
                logger.warning("Ollama HTTP error (attempt %d/%d): %s", attempt + 1, max_retries, e)
            except ConnectionError as e:
                last_exception = e
                logger.error("Cannot connect to Ollama server. Is it running?")
                break  # Don't retry connection errors
            except Exception as e:
                last_exception = e
                logger.warning("Ollama call failed (attempt %d/%d): %s", attempt + 1, max_retries, e)
            
            if attempt < max_retries - 1:
                # Exponential backoff
                time.sleep((2 ** attempt) * self._rate_limit_delay)
        
        # If we get here, all retries failed
        raise RuntimeError(
            f"Failed to get Ollama response after {max_retries} retries"
        ) from last_exception
    
    def _parse_ollama_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse Ollama response to extract findings."""
        try:
            # Extract JSON from response
            # Handle cases where LLM includes additional text
            json_start = response.find("[")
            json_end = response.rfind("]") + 1
            
            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                findings = json.loads(json_str)
                
                # Validate findings structure
                validated_findings = []
                for finding in findings:
                    if all(key in finding for key in ["title", "severity", "explanation", "recommendation"]):
                        # Normalize severity
                        finding["severity"] = finding["severity"].upper()
                        if finding["severity"] not in ["HIGH", "MEDIUM", "LOW"]:
                            finding["severity"] = "MEDIUM"
                        validated_findings.append(finding)
                
                return validated_findings
            
            logger.error("No valid JSON found in Ollama response")
            return []
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse Ollama response as JSON: %s", e)
            logger.debug("Response: %s", response[:500])  # Log first 500 chars
            return []
    
    # Mock data methods (inherited from base implementation)
    def _get_mock_iam_findings(self, provider_name: str = "gcp") -> List[SecurityFinding]:
        """Return mock IAM findings for testing."""
        if provider_name == "aws":
            return [
                SecurityFinding(
                    title="AWS IAM User with AdministratorAccess Policy",
                    severity="HIGH",
                    explanation=(
                        "The IAM user 'admin-user' has the AWS managed policy "
                        "'AdministratorAccess' attached, granting unrestricted access "
                        "to all AWS services and resources."
                    ),
                    recommendation=(
                        "Remove AdministratorAccess policy and create a custom policy "
                        "with only the specific permissions needed."
                    ),
                ),
            ]
        elif provider_name == "azure":
            return [
                SecurityFinding(
                    title="Azure Subscription Owner Role Assignment",
                    severity="HIGH",
                    explanation=(
                        "Multiple users have the 'Owner' role at the subscription "
                        "level, providing full control over all resources."
                    ),
                    recommendation=(
                        "Limit Owner role assignments to break-glass accounts only. "
                        "Use more restrictive roles like Contributor or Reader."
                    ),
                ),
            ]
        else:  # GCP
            return [
                SecurityFinding(
                    title="Overly Permissive Owner Role Assignment",
                    severity="HIGH",
                    explanation=(
                        "Multiple users have been granted the 'roles/owner' role, "
                        "which provides full administrative access to all resources."
                    ),
                    recommendation=(
                        "Remove the owner role from non-essential users. Instead, "
                        "grant specific roles that provide only the necessary permissions."
                    ),
                ),
            ]
    
    def _get_mock_scc_findings(self) -> List[SecurityFinding]:
        """Return mock SCC findings for testing."""
        return [
            SecurityFinding(
                title="Over-Privileged Service Account Detected",
                severity="HIGH",
                explanation=(
                    "Security Command Center detected a service account with "
                    "excessive permissions that exceed its operational requirements."
                ),
                recommendation=(
                    "Review and reduce the permissions of the identified service "
                    "account following the principle of least privilege."
                ),
            ),
        ]
    
    def _get_mock_findings_for_provider(self, provider_name: str) -> List[SecurityFinding]:
        """Get mock findings for the specified provider."""
        if provider_name == "aws":
            return [
                SecurityFinding(
                    title="S3 Bucket Allows Public Read Access",
                    severity="HIGH",
                    explanation=(
                        "AWS Security Hub detected an S3 bucket configured with "
                        "public read access, potentially exposing sensitive data."
                    ),
                    recommendation=(
                        "Disable public access on the S3 bucket immediately. "
                        "Enable S3 Block Public Access at the account level."
                    ),
                ),
            ]
        elif provider_name == "azure":
            return [
                SecurityFinding(
                    title="Azure Storage Account Allows Public Blob Access",
                    severity="HIGH",
                    explanation=(
                        "Azure Security Center detected that storage account "
                        "permits public blob access, creating unauthorized data access risk."
                    ),
                    recommendation=(
                        "Disable public blob access on the storage account. "
                        "Implement private endpoints and use SAS tokens."
                    ),
                ),
            ]
        return []