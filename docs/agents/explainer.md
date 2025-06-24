# Explainer Agent Documentation

The Explainer Agent analyzes collected GCP configuration data using Google's Gemini LLM to identify security risks and provide recommendations.

## Overview

The Explainer Agent:

- Processes collected GCP configuration data
- Uses Vertex AI's Gemini model for intelligent analysis
- Identifies security risks with severity ratings
- Provides actionable recommendations
- Outputs structured findings in JSON format

## Architecture

```
┌─────────────────┐
│ collected.json  │
└────────┬────────┘
         │
┌────────▼────────┐
│ Explainer Agent │
├─────────────────┤
│ - Risk Analyzer │
│ - Gemini Client │
│ - Mock Provider │
└────────┬────────┘
         │
┌────────▼────────┐
│ explained.json  │
└─────────────────┘
```

## Usage

### Command Line Interface

```bash
# Basic usage
python python_agents/explainer/agent_explainer.py

# Specify input file
python python_agents/explainer/agent_explainer.py --input=./data/collected.json

# Use mock mode (no Vertex AI calls)
python python_agents/explainer/agent_explainer.py --use_mock=True

# Specify output location
python python_agents/explainer/agent_explainer.py --output=./custom/explained.json

# Set minimum severity threshold
python python_agents/explainer/agent_explainer.py --min_severity=MEDIUM
```

### Python API

```python
from explainer.agent_explainer import ExplainerAgent, ExplainerConfig

# Initialize with configuration
config = ExplainerConfig(
    project_id="my-project",
    region="us-central1",
    model="gemini-1.5-flash",
    use_mock=False,
    temperature=0.3
)

agent = ExplainerAgent(config)

# Analyze collected data
findings = agent.analyze(collected_data)

# Process specific resource types
iam_findings = agent.analyze_iam_policies(iam_policies)
scc_findings = agent.analyze_scc_findings(scc_findings)
```

## Configuration

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `project_id` | string | Required | GCP project for Vertex AI |
| `region` | string | "us-central1" | Vertex AI region |
| `model` | string | "gemini-1.5-flash" | Gemini model to use |
| `use_mock` | boolean | False | Use mock analysis |
| `temperature` | float | 0.3 | LLM temperature (0.0-1.0) |
| `max_tokens` | integer | 2048 | Maximum response tokens |
| `input_path` | string | "data/collected.json" | Input file location |
| `output_path` | string | "data/explained.json" | Output file location |
| `min_severity` | string | "LOW" | Minimum severity to report |
| `batch_size` | integer | 10 | Resources per LLM call |

### Environment Variables

```bash
# Vertex AI configuration
export VERTEX_AI_PROJECT=my-project
export VERTEX_AI_REGION=us-central1
export VERTEX_AI_MODEL=gemini-1.5-pro

# Agent configuration
export PADDI_MIN_SEVERITY=MEDIUM
export PADDI_USE_MOCK=false
```

## Output Format

### Finding Structure

```json
{
  "findings": [
    {
      "id": "iam-001",
      "title": "Overly Permissive Owner Role Assignment",
      "severity": "CRITICAL",
      "category": "IAM_MISCONFIGURATION",
      "resource": "projects/my-project",
      "explanation": "The user account 'admin@example.com' has been granted the 'roles/owner' role at the project level. This provides complete control over all resources and should be avoided in production environments.",
      "recommendation": "Follow the principle of least privilege by:\n1. Remove the owner role assignment\n2. Grant specific predefined roles based on actual needs\n3. Use custom roles for fine-grained access control\n4. Implement time-bound access using IAM conditions",
      "references": [
        "https://cloud.google.com/iam/docs/understanding-roles",
        "https://cloud.google.com/iam/docs/using-iam-securely"
      ],
      "compliance_frameworks": ["CIS", "PCI-DSS", "SOC2"],
      "risk_score": 9.5,
      "remediation_effort": "MEDIUM"
    }
  ],
  "summary": {
    "total_findings": 15,
    "by_severity": {
      "CRITICAL": 2,
      "HIGH": 5,
      "MEDIUM": 6,
      "LOW": 2
    },
    "by_category": {
      "IAM_MISCONFIGURATION": 8,
      "PUBLIC_ACCESS": 4,
      "ENCRYPTION": 3
    }
  },
  "metadata": {
    "analysis_timestamp": "2024-01-15T10:45:00Z",
    "model_used": "gemini-1.5-flash",
    "analysis_duration_seconds": 45
  }
}
```

## Analysis Features

### Severity Classification

| Severity | Risk Level | Examples |
|----------|------------|----------|
| CRITICAL | Immediate risk | Public data exposure, owner roles, no authentication |
| HIGH | Significant risk | Overly permissive IAM, weak encryption, exposed services |
| MEDIUM | Moderate risk | Missing best practices, outdated configurations |
| LOW | Minor issues | Naming conventions, redundant permissions |

### Risk Categories

1. **IAM_MISCONFIGURATION**
   - Overly permissive roles
   - Service account key risks
   - Missing IAM conditions
   - Cross-project access issues

2. **PUBLIC_ACCESS**
   - Public storage buckets
   - Exposed compute instances
   - Open firewall rules
   - Public datasets

3. **ENCRYPTION**
   - Missing encryption at rest
   - Weak encryption algorithms
   - Unencrypted data transfer
   - Key management issues

4. **COMPLIANCE**
   - Regulatory violations
   - Policy non-compliance
   - Audit logging gaps
   - Data residency issues

5. **VULNERABILITY**
   - Known CVEs
   - Outdated software
   - Missing patches
   - Configuration weaknesses

## Prompt Engineering

### Default Analysis Prompt

```python
DEFAULT_PROMPT = """
You are a cloud security expert analyzing GCP configurations.

Analyze the following configuration data and identify security risks:
{configuration}

For each finding, provide:
1. A clear, concise title
2. Severity level (CRITICAL/HIGH/MEDIUM/LOW)
3. Detailed explanation of the risk
4. Specific, actionable recommendations
5. Relevant compliance frameworks affected

Focus on:
- IAM misconfigurations and overly permissive access
- Public exposure of resources
- Missing encryption or security controls
- Compliance violations (CIS, PCI-DSS, HIPAA, etc.)
- Best practice violations

Output format: JSON array of findings
"""
```

### Custom Prompts

```python
# Industry-specific prompt
HEALTHCARE_PROMPT = """
Analyze for HIPAA compliance focusing on:
- PHI data protection
- Access controls and audit logs
- Encryption requirements
- Business associate agreements
"""

# Severity-focused prompt
HIGH_SEVERITY_PROMPT = """
Focus only on CRITICAL and HIGH severity issues that could lead to:
- Data breaches
- Service disruptions
- Compliance violations with financial impact
"""
```

## Advanced Features

### Batch Processing

```python
# Process multiple resources in batches
def batch_analyze(resources, batch_size=10):
    findings = []
    for batch in chunks(resources, batch_size):
        batch_findings = analyze_batch(batch)
        findings.extend(batch_findings)
    return findings
```

### Caching

```python
# Cache analysis results to avoid duplicate API calls
@lru_cache(maxsize=1000)
def analyze_resource(resource_hash):
    return gemini_client.analyze(resource)
```

### Custom Analyzers

```python
# Add custom analysis logic
class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, resource):
        findings = []

        # Custom logic
        if self.is_public_bucket(resource):
            findings.append(self.create_finding(
                title="Public Storage Bucket",
                severity="CRITICAL",
                explanation="...",
                recommendation="..."
            ))

        return findings

# Register analyzer
explainer.register_analyzer('storage', CustomAnalyzer())
```

## Error Handling

### Retry Logic

```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type(VertexAIError)
)
def call_gemini(self, prompt):
    return self.gemini_client.generate(prompt)
```

### Fallback Strategies

```python
def analyze_with_fallback(self, data):
    try:
        # Try primary model
        return self.analyze_with_model(data, "gemini-1.5-pro")
    except QuotaExceededError:
        # Fall back to lighter model
        return self.analyze_with_model(data, "gemini-1.5-flash")
    except VertexAIError:
        # Use rule-based analysis as last resort
        return self.rule_based_analysis(data)
```

## Performance Optimization

### Response Streaming

```python
# Stream responses for large analyses
async def stream_analysis(self, resources):
    async for finding in self.gemini_client.stream_generate(prompt):
        yield parse_finding(finding)
```

### Parallel Processing

```python
# Analyze multiple resources in parallel
async def parallel_analyze(self, resources):
    tasks = [self.analyze_resource(r) for r in resources]
    results = await asyncio.gather(*tasks)
    return flatten(results)
```

## Testing

### Unit Tests

```bash
# Run explainer tests
pytest python_agents/tests/test_explainer.py

# Test specific functionality
pytest python_agents/tests/test_explainer.py::test_severity_classification
```

### Mock Testing

```python
def test_mock_analysis():
    agent = ExplainerAgent(use_mock=True)
    findings = agent.analyze(sample_data)

    assert len(findings) > 0
    assert all(f.severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']
               for f in findings)
    assert all(f.explanation and f.recommendation for f in findings)
```

## Troubleshooting

### Common Issues

1. **Vertex AI Authentication**

   ```bash
   # Verify authentication
   gcloud auth application-default print-access-token

   # Enable Vertex AI API
   gcloud services enable aiplatform.googleapis.com
   ```

2. **Model Availability**

   ```bash
   # List available models
   gcloud ai models list --region=us-central1

   # Check model permissions
   gcloud ai models describe gemini-1.5-flash \
     --region=us-central1
   ```

3. **Quota Limits**

   ```python
   # Implement rate limiting
   rate_limiter = RateLimiter(
       requests_per_minute=60,
       tokens_per_minute=100000
   )
   ```

### Debug Mode

```bash
# Enable detailed logging
export PADDI_LOG_LEVEL=DEBUG
python python_agents/explainer/agent_explainer.py

# Log LLM interactions
export PADDI_LOG_LLM_CALLS=true
```

## Best Practices

1. **Prompt Optimization**
   - Keep prompts focused and specific
   - Include examples for consistent output
   - Test prompts with various input types

2. **Cost Management**
   - Use appropriate model sizes
   - Implement caching for repeated analyses
   - Batch similar resources together

3. **Quality Assurance**
   - Validate LLM outputs against schemas
   - Implement confidence scoring
   - Cross-reference with rule-based checks

4. **Security**
   - Never send sensitive data to LLM
   - Implement data sanitization
   - Use private Vertex AI endpoints

## API Reference

### ExplainerAgent Class

```python
class ExplainerAgent:
    def __init__(self, config: ExplainerConfig):
        """Initialize explainer with configuration."""

    def analyze(self, collected_data: dict) -> List[Finding]:
        """Analyze collected data and return findings."""

    def analyze_iam_policies(self, policies: List[dict]) -> List[Finding]:
        """Analyze IAM policies for security issues."""

    def analyze_scc_findings(self, findings: List[dict]) -> List[Finding]:
        """Enhance SCC findings with additional context."""

    def save_findings(self, findings: List[Finding], output_path: str):
        """Save analysis results to JSON file."""
```

### Data Models

```python
@dataclass
class Finding:
    id: str
    title: str
    severity: Severity
    category: str
    resource: str
    explanation: str
    recommendation: str
    references: List[str] = field(default_factory=list)
    compliance_frameworks: List[str] = field(default_factory=list)
    risk_score: float = 0.0
    remediation_effort: str = "MEDIUM"

@dataclass
class AnalysisSummary:
    total_findings: int
    by_severity: Dict[str, int]
    by_category: Dict[str, int]

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
```
