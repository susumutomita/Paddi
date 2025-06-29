# Development Guide

Welcome to the Paddi development guide! This document will help you set up
your development environment and contribute to the project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git
- Google Cloud SDK (for testing with real GCP resources)
- Docker (optional, for containerized development)

### Clone the Repository

```bash
git clone https://github.com/susumutomita/Paddi.git
cd Paddi
```

### Python Development Setup

#### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

#### 3. Install in Development Mode

```bash
pip install -e .
```

#### 4. Set Up Pre-commit Hooks

```bash
pre-commit install
```

## Project Structure

```text
Paddi/
├── app/                    # Python application code
│   ├── collector/         # Data collection agent
│   ├── explainer/         # Analysis agent (LLM integration)
│   └── reporter/          # Report generation agent
├── tests/                 # Test suite
├── templates/             # Report templates
├── data/                  # Intermediate data storage
├── output/                # Generated reports
├── docs/                  # Documentation
├── examples/              # Example configurations
└── main.py                # CLI entry point
```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Your Changes

Follow the coding standards for the language you're working with:

#### Python Code Style

```python
# Good example
from typing import List, Dict, Optional
from dataclasses import dataclass

@dataclass
class SecurityFinding:
    """Represents a security finding.

    Attributes:
        title: Brief description of the finding
        severity: Severity level (CRITICAL, HIGH, MEDIUM, LOW)
        explanation: Detailed explanation of the security issue
    """
    title: str
    severity: str
    explanation: str
    recommendation: Optional[str] = None

    def is_critical(self) -> bool:
        """Check if finding is critical severity."""
        return self.severity == "CRITICAL"
```

### 3. Write Tests

#### Python Tests

```python
# tests/test_collector.py
import pytest
from collector.agent_collector import CollectorAgent

@pytest.fixture
def mock_collector():
    """Create collector with mock data."""
    return CollectorAgent({"use_mock": True})

def test_collect_iam_policies(mock_collector):
    """Test IAM policy collection."""
    result = mock_collector.collect()

    assert len(result.iam_policies) > 0
    assert all(p.resource.startswith("projects/") for p in result.iam_policies)

def test_collect_with_filters(mock_collector):
    """Test collection with resource filters."""
    mock_collector.config.resource_types = ["iam"]
    result = mock_collector.collect()

    assert len(result.iam_policies) > 0
    assert len(result.scc_findings) == 0
```

### 4. Run Quality Checks

#### Python

```bash
# Run tests with coverage
make test

# Run linting
make lint

# Format code
make format

# Run all checks (required before commit)
make before-commit
```

### 5. Update Documentation

Update relevant documentation for your changes:

- API documentation for new functions/classes
- README updates for new features
- Example updates if behavior changes
- Migration guide for breaking changes

### 6. Submit Pull Request

```bash
git add .
git commit -m "feat: add support for Cloud Storage auditing"
git push origin feature/your-feature-name
```

Create a pull request on GitHub with:

- Clear description of changes
- Link to related issue
- Test results
- Documentation updates

## Testing

### Unit Tests

Test individual components in isolation:

```python
# Example: Testing a specific analyzer
def test_iam_analyzer():
    analyzer = IAMAnalyzer()

    policy = {
        "bindings": [{
            "role": "roles/owner",
            "members": ["user:test@example.com"]
        }]
    }

    findings = analyzer.analyze(policy)
    assert len(findings) == 1
    assert findings[0].severity == "CRITICAL"
```

### Integration Tests

Test component interactions:

```python
# Example: Testing full pipeline
def test_full_audit_pipeline():
    # Collect
    collector = CollectorAgent({"use_mock": True})
    collected = collector.collect()

    # Analyze
    explainer = ExplainerAgent({"use_mock": True})
    findings = explainer.analyze(collected.to_dict())

    # Report
    reporter = ReporterAgent({})
    reports = reporter.generate_reports(findings)

    assert "audit.md" in reports
    assert "audit.html" in reports
```

### End-to-End Tests

Test complete workflows:

```bash
# Test CLI with mock data
./test_e2e.sh --use-mock

# Test with real GCP (requires authentication)
./test_e2e.sh --project-id=test-project
```

## Adding New Features

### Adding a New Collector

1. Create collector class:

```python
# collector/storage_collector.py
from .base import BaseCollector

class StorageCollector(BaseCollector):
    """Collect Cloud Storage bucket configurations."""

    def collect(self) -> List[Dict]:
        """Collect storage bucket data."""
        # Implementation
        pass
```

1. Register in the agent:

```python
# collector/agent_collector.py
COLLECTORS = {
    'iam': IAMCollector,
    'scc': SCCCollector,
    'storage': StorageCollector,  # New collector
}
```

1. Add tests:

```python
# tests/test_storage_collector.py
def test_storage_collector():
    collector = StorageCollector(mock_client)
    buckets = collector.collect()
    assert len(buckets) > 0
```

### Adding a New Report Format

1. Create format handler:

```python
# reporter/formats/pdf_format.py
from .base import BaseFormat

class PDFFormat(BaseFormat):
    """Generate PDF reports."""

    def generate(self, findings: List[Finding]) -> bytes:
        """Generate PDF report."""
        # Implementation
        pass
```

1. Register format:

```python
# reporter/agent_reporter.py
FORMATS = {
    'markdown': MarkdownFormat,
    'html': HTMLFormat,
    'pdf': PDFFormat,  # New format
}
```

## Debugging

### Python Debugging

```python
# Use debugger
import pdb; pdb.set_trace()

# Or with ipdb for better experience
import ipdb; ipdb.set_trace()

# Use logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug information")
```

### Common Issues

1. **Import Errors**

   ```bash
   # Ensure you're in virtual environment
   which python  # Should show venv path

   # Reinstall in development mode
   pip install -e .
   ```

2. **Test Failures**

   ```bash
   # Run specific test with output
   pytest -xvs tests/test_specific.py::test_function

   ```

## Performance Profiling

### Python Profiling

```python
# Using cProfile
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Code to profile
result = expensive_operation()

profiler.disable()
stats = pstats.Stats(profiler).sort_stats('cumulative')
stats.print_stats()
```

## Release Process

### Version Bumping

```bash
# Python version (setup.py or pyproject.toml)
[tool.poetry]
version = "1.2.0"
```

### Changelog

Update `CHANGELOG.md`:

```markdown
## [1.2.0] - 2024-01-15

### Added
- Cloud Storage bucket auditing
- Custom policy support

### Changed
- Improved performance of IAM analysis

### Fixed
- Memory leak in report generation
```

### Release Checklist

- [ ] All tests passing
- [ ] Documentation updated
- [ ] Changelog updated
- [ ] Version bumped
- [ ] Tagged release
- [ ] Published to package registries

## Getting Help

- **Discord**: Join our [Discord server](https://discord.gg/paddi)
- **Issues**: Check [existing issues](https://github.com/susumutomita/Paddi/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/susumutomita/Paddi/discussions)

## Code of Conduct

Please read and follow our [Code of Conduct](../CODE_OF_CONDUCT.md) to ensure
a welcoming environment for all contributors.

## License

By contributing to Paddi, you agree that your contributions will be licensed
under the project's MIT License.
