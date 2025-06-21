# API Reference

This document provides a comprehensive API reference for all Paddi agents and core components.

## Core Components

### Configuration

#### `Config` Class

Base configuration class for all agents.

```python
from paddi.config import Config

class Config:
    """Base configuration class."""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Path to TOML configuration file
        """
    
    def load(self) -> Dict[str, Any]:
        """Load configuration from file and environment."""
    
    def validate(self) -> bool:
        """Validate configuration values."""
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
```

### Data Models

#### `Finding` Class

Represents a security finding.

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class Severity(Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"

@dataclass
class Finding:
    """Security finding data model."""
    
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
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary."""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Finding':
        """Create finding from dictionary."""
```

## Collector Agent API

### `CollectorAgent` Class

Main class for collecting GCP resources.

```python
from collector.agent_collector import CollectorAgent, CollectorConfig

class CollectorAgent:
    """Agent for collecting GCP configuration data."""
    
    def __init__(self, config: CollectorConfig):
        """
        Initialize collector agent.
        
        Args:
            config: Collector configuration
        """
    
    def collect(self) -> CollectionResult:
        """
        Run collection process.
        
        Returns:
            CollectionResult with collected data
            
        Raises:
            CollectionError: If collection fails
            AuthenticationError: If GCP auth fails
        """
    
    def collect_iam_policies(self) -> List[IAMPolicy]:
        """
        Collect IAM policies.
        
        Returns:
            List of IAM policies
        """
    
    def collect_scc_findings(self) -> List[SCCFinding]:
        """
        Collect Security Command Center findings.
        
        Returns:
            List of SCC findings
        """
    
    def save_results(self, results: CollectionResult, output_path: str):
        """
        Save collection results to file.
        
        Args:
            results: Collection results
            output_path: Output file path
        """
```

### `CollectorConfig` Class

Configuration for the collector agent.

```python
@dataclass
class CollectorConfig:
    """Collector agent configuration."""
    
    project_id: str
    organization_id: Optional[str] = None
    use_mock: bool = False
    resource_types: List[str] = field(default_factory=lambda: ["iam", "scc"])
    output_path: str = "data/collected.json"
    page_size: int = 100
    max_retries: int = 3
    timeout: int = 300
    
    def validate(self) -> bool:
        """Validate configuration."""
```

### `CollectionResult` Class

Results from collection process.

```python
@dataclass
class CollectionResult:
    """Collection process results."""
    
    metadata: Dict[str, Any]
    iam_policies: List[IAMPolicy]
    scc_findings: List[SCCFinding]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
    
    def save(self, path: str):
        """Save results to JSON file."""
    
    @classmethod
    def load(cls, path: str) -> 'CollectionResult':
        """Load results from JSON file."""
```

### Collector Interfaces

```python
from abc import ABC, abstractmethod

class CollectorInterface(ABC):
    """Base interface for resource collectors."""
    
    @abstractmethod
    def collect(self) -> List[Dict[str, Any]]:
        """Collect resources."""
        pass

class IAMCollector(CollectorInterface):
    """IAM policy collector."""
    
    def __init__(self, project_id: str, credentials: Any):
        """Initialize IAM collector."""
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect IAM policies."""
    
    def get_project_policy(self) -> Dict[str, Any]:
        """Get project-level IAM policy."""

class SCCCollector(CollectorInterface):
    """Security Command Center findings collector."""
    
    def __init__(self, organization_id: str, credentials: Any):
        """Initialize SCC collector."""
    
    def collect(self, filters: Optional[str] = None) -> List[Dict[str, Any]]:
        """Collect SCC findings with optional filters."""
```

## Explainer Agent API

### `ExplainerAgent` Class

Main class for analyzing security risks.

```python
from explainer.agent_explainer import ExplainerAgent, ExplainerConfig

class ExplainerAgent:
    """Agent for analyzing security risks using LLM."""
    
    def __init__(self, config: ExplainerConfig):
        """
        Initialize explainer agent.
        
        Args:
            config: Explainer configuration
        """
    
    def analyze(self, collected_data: Dict[str, Any]) -> List[Finding]:
        """
        Analyze collected data for security issues.
        
        Args:
            collected_data: Data from collector agent
            
        Returns:
            List of security findings
            
        Raises:
            AnalysisError: If analysis fails
            VertexAIError: If LLM call fails
        """
    
    def analyze_iam_policies(self, policies: List[Dict]) -> List[Finding]:
        """
        Analyze IAM policies for security issues.
        
        Args:
            policies: List of IAM policies
            
        Returns:
            List of findings
        """
    
    def analyze_scc_findings(self, findings: List[Dict]) -> List[Finding]:
        """
        Enhance SCC findings with additional context.
        
        Args:
            findings: List of SCC findings
            
        Returns:
            Enhanced findings
        """
    
    def save_findings(self, findings: List[Finding], output_path: str):
        """
        Save findings to file.
        
        Args:
            findings: List of findings
            output_path: Output file path
        """
```

### `ExplainerConfig` Class

Configuration for the explainer agent.

```python
@dataclass
class ExplainerConfig:
    """Explainer agent configuration."""
    
    project_id: str
    region: str = "us-central1"
    model: str = "gemini-1.5-flash"
    use_mock: bool = False
    temperature: float = 0.3
    max_tokens: int = 2048
    input_path: str = "data/collected.json"
    output_path: str = "data/explained.json"
    min_severity: str = "LOW"
    batch_size: int = 10
    
    def validate(self) -> bool:
        """Validate configuration."""
```

### LLM Integration

```python
class GeminiClient:
    """Client for Vertex AI Gemini model."""
    
    def __init__(self, project_id: str, region: str, model: str):
        """
        Initialize Gemini client.
        
        Args:
            project_id: GCP project ID
            region: Vertex AI region
            model: Model name
        """
    
    def generate(self, prompt: str, **kwargs) -> str:
        """
        Generate response from prompt.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
    
    async def stream_generate(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """
        Stream generated response.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional parameters
            
        Yields:
            Generated text chunks
        """
```

## Reporter Agent API

### `ReporterAgent` Class

Main class for generating reports.

```python
from reporter.agent_reporter import ReporterAgent, ReporterConfig

class ReporterAgent:
    """Agent for generating security reports."""
    
    def __init__(self, config: ReporterConfig):
        """
        Initialize reporter agent.
        
        Args:
            config: Reporter configuration
        """
    
    def generate_reports(self, findings: List[Finding]) -> Dict[str, str]:
        """
        Generate reports in configured formats.
        
        Args:
            findings: List of security findings
            
        Returns:
            Dictionary of format -> report content
        """
    
    def generate_markdown(self, findings: List[Finding]) -> str:
        """
        Generate Markdown report.
        
        Args:
            findings: List of findings
            
        Returns:
            Markdown report content
        """
    
    def generate_html(self, findings: List[Finding]) -> str:
        """
        Generate HTML report.
        
        Args:
            findings: List of findings
            
        Returns:
            HTML report content
        """
    
    def generate_json(self, findings: List[Finding]) -> str:
        """
        Generate JSON report.
        
        Args:
            findings: List of findings
            
        Returns:
            JSON report content
        """
    
    def save_reports(self, reports: Dict[str, str], output_dir: str):
        """
        Save generated reports to disk.
        
        Args:
            reports: Dictionary of reports
            output_dir: Output directory
        """
```

### `ReporterConfig` Class

Configuration for the reporter agent.

```python
@dataclass
class ReporterConfig:
    """Reporter agent configuration."""
    
    formats: List[str] = field(default_factory=lambda: ["markdown", "html"])
    template_dir: str = "./templates"
    output_dir: str = "./output"
    input_path: str = "data/explained.json"
    include_summary: bool = True
    include_toc: bool = True
    group_by_severity: bool = True
    group_by_category: bool = False
    include_charts: bool = True
    theme: str = "light"
    obsidian_compatible: bool = True
    
    def validate(self) -> bool:
        """Validate configuration."""
```

### Template Engine

```python
class TemplateEngine:
    """Jinja2-based template engine."""
    
    def __init__(self, template_dir: str):
        """
        Initialize template engine.
        
        Args:
            template_dir: Template directory path
        """
    
    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Render template with context.
        
        Args:
            template_name: Template file name
            context: Template context data
            
        Returns:
            Rendered content
        """
    
    def add_filter(self, name: str, func: Callable):
        """
        Add custom Jinja2 filter.
        
        Args:
            name: Filter name
            func: Filter function
        """
```

## Utilities

### Logging

```python
from paddi.utils.logger import get_logger

# Get logger for module
logger = get_logger(__name__)

# Log with different levels
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# Configure logging
from paddi.utils.logger import configure_logging

configure_logging(
    level="DEBUG",
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    output_file="paddi.log"
)
```

### Error Handling

```python
from paddi.utils.errors import (
    PaddiError,
    ConfigurationError,
    CollectionError,
    AnalysisError,
    ReportError
)

# Base error class
class PaddiError(Exception):
    """Base exception for Paddi."""
    pass

# Specific errors
class ConfigurationError(PaddiError):
    """Configuration-related errors."""
    pass

class CollectionError(PaddiError):
    """Data collection errors."""
    pass

class AnalysisError(PaddiError):
    """Analysis errors."""
    pass

class ReportError(PaddiError):
    """Report generation errors."""
    pass
```

### Retry Logic

```python
from paddi.utils.retry import retry_with_backoff

@retry_with_backoff(
    max_attempts=3,
    initial_delay=1,
    max_delay=10,
    exceptions=(APIError, TimeoutError)
)
def api_call():
    """Make API call with automatic retry."""
    pass
```

### Rate Limiting

```python
from paddi.utils.rate_limit import RateLimiter

# Create rate limiter
limiter = RateLimiter(
    requests_per_second=10,
    burst_size=20
)

# Use rate limiter
with limiter:
    make_api_call()

# Or as decorator
@limiter.limit
def make_api_call():
    pass
```

## Integration Examples

### Custom Collector

```python
from collector.agent_collector import CollectorInterface

class CustomCollector(CollectorInterface):
    """Custom resource collector."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def collect(self) -> List[Dict[str, Any]]:
        """Collect custom resources."""
        resources = []
        
        # Custom collection logic
        # ...
        
        return resources

# Register collector
from collector.registry import register_collector

register_collector("custom", CustomCollector)
```

### Custom Analyzer

```python
from explainer.analyzers import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    """Custom security analyzer."""
    
    def analyze(self, resource: Dict[str, Any]) -> List[Finding]:
        """Analyze resource for security issues."""
        findings = []
        
        # Custom analysis logic
        if self.is_risky(resource):
            findings.append(Finding(
                id=f"custom-{resource['id']}",
                title="Custom Security Issue",
                severity=Severity.HIGH,
                explanation="...",
                recommendation="..."
            ))
        
        return findings

# Register analyzer
from explainer.registry import register_analyzer

register_analyzer("custom", CustomAnalyzer)
```

### Custom Reporter Format

```python
from reporter.formats import BaseFormat

class XMLFormat(BaseFormat):
    """XML report format."""
    
    def generate(self, findings: List[Finding]) -> str:
        """Generate XML report."""
        import xml.etree.ElementTree as ET
        
        root = ET.Element("security-report")
        
        for finding in findings:
            finding_elem = ET.SubElement(root, "finding")
            ET.SubElement(finding_elem, "title").text = finding.title
            ET.SubElement(finding_elem, "severity").text = finding.severity.value
            # ... more fields
        
        return ET.tostring(root, encoding="unicode")

# Register format
from reporter.registry import register_format

register_format("xml", XMLFormat)
```

## Testing Utilities

### Mock Providers

```python
from paddi.testing import MockCollector, MockExplainer

# Use mock collector
collector = MockCollector()
data = collector.collect()  # Returns sample data

# Use mock explainer
explainer = MockExplainer()
findings = explainer.analyze(data)  # Returns sample findings
```

### Test Fixtures

```python
from paddi.testing.fixtures import (
    sample_iam_policy,
    sample_scc_finding,
    sample_finding,
    sample_collected_data
)

# Use in tests
def test_analyzer():
    data = sample_collected_data()
    agent = ExplainerAgent(use_mock=True)
    findings = agent.analyze(data)
    assert len(findings) > 0
```

## Type Definitions

```python
from typing import TypedDict, Literal, Union

class IAMBinding(TypedDict):
    role: str
    members: List[str]
    condition: Optional[Dict[str, Any]]

class IAMPolicy(TypedDict):
    version: int
    bindings: List[IAMBinding]
    etag: str

SeverityLevel = Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"]

ResourceType = Union[
    Literal["iam"],
    Literal["scc_findings"],
    Literal["compute"],
    Literal["storage"]
]
```