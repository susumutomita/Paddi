# Code Style Guide

This guide defines the coding standards and conventions for the Paddi project. Following these guidelines ensures code consistency and maintainability across the codebase.

## General Principles

1. **Readability**: Code is read more often than it's written
2. **Simplicity**: Prefer simple, clear solutions over clever ones
3. **Consistency**: Follow existing patterns in the codebase
4. **Documentation**: Document why, not what
5. **Testing**: Write tests for all new functionality

## Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some project-specific conventions.

### Code Formatting

We use **Black** for automatic code formatting:

```bash
# Format all Python files
black python_agents/

# Check formatting without changing files
black --check python_agents/
```

Configuration in `pyproject.toml`:

```toml
[tool.black]
line-length = 88
target-version = ['py38']
include = '\.pyi?$'
```

### Imports

Order imports according to PEP 8:

```python
# Standard library imports
import json
import os
from datetime import datetime
from pathlib import Path

# Related third party imports
import requests
from google.cloud import storage
from jinja2 import Template

# Local application imports
from paddi.config import Config
from paddi.utils import get_logger
```

Use `isort` to automatically sort imports:

```bash
isort python_agents/
```

### Naming Conventions

```python
# Classes use PascalCase
class SecurityAnalyzer:
    pass

# Functions and variables use snake_case
def analyze_iam_policy(policy_data):
    finding_count = 0
    return finding_count

# Constants use UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_TIMEOUT = 300

# Private functions/methods prefix with underscore
def _internal_helper():
    pass

# Module-level private variables
_logger = get_logger(__name__)
```

### Type Hints

Always use type hints for function signatures:

```python
from typing import List, Dict, Optional, Union, Tuple

def analyze_findings(
    findings: List[Dict[str, Any]],
    severity_filter: Optional[str] = None
) -> Tuple[List[Finding], AnalysisSummary]:
    """
    Analyze security findings.

    Args:
        findings: List of finding dictionaries
        severity_filter: Optional severity level filter

    Returns:
        Tuple of processed findings and analysis summary
    """
    processed: List[Finding] = []
    # Implementation
    return processed, summary
```

### Docstrings

Use Google-style docstrings:

```python
class CollectorAgent:
    """Agent for collecting GCP configuration data.

    This agent connects to various GCP APIs to collect configuration
    data for security analysis.

    Attributes:
        project_id: GCP project ID to audit
        credentials: Service account credentials
        use_mock: Whether to use mock data
    """

    def collect_iam_policies(self) -> List[IAMPolicy]:
        """Collect IAM policies from the project.

        Fetches all IAM policies including project-level and
        resource-level policies.

        Returns:
            List of IAMPolicy objects

        Raises:
            CollectionError: If API calls fail
            AuthenticationError: If credentials are invalid

        Example:
            >>> agent = CollectorAgent(project_id="my-project")
            >>> policies = agent.collect_iam_policies()
            >>> print(f"Found {len(policies)} policies")
        """
        pass
```

### Error Handling

Be explicit about error handling:

```python
# Good
try:
    response = api_client.get_iam_policy(resource)
except PermissionError as e:
    logger.warning(f"Insufficient permissions for {resource}: {e}")
    return None
except APIError as e:
    logger.error(f"API call failed: {e}")
    raise CollectionError(f"Failed to collect IAM policy: {e}") from e

# Bad - too broad exception handling
try:
    response = api_client.get_iam_policy(resource)
except Exception:
    return None
```

### Logging

Use structured logging:

```python
import logging

logger = logging.getLogger(__name__)

# Good - structured logging with context
logger.info(
    "Collected IAM policies",
    extra={
        "project_id": self.project_id,
        "policy_count": len(policies),
        "duration_seconds": duration
    }
)

# Bad - unstructured string formatting
logger.info(f"Collected {len(policies)} policies in {duration}s")
```

### Testing

Write comprehensive tests:

```python
import pytest
from unittest.mock import Mock, patch

class TestSecurityAnalyzer:
    """Test cases for SecurityAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        """Create analyzer instance for tests."""
        return SecurityAnalyzer(config={"min_severity": "MEDIUM"})

    def test_analyze_critical_finding(self, analyzer):
        """Test that critical findings are properly identified."""
        # Arrange
        finding = {
            "severity": "CRITICAL",
            "title": "Public bucket",
            "resource": "gs://my-bucket"
        }

        # Act
        result = analyzer.analyze(finding)

        # Assert
        assert result.severity == "CRITICAL"
        assert result.requires_immediate_action is True

    @patch('analyzer.gemini_client')
    def test_analyze_with_llm(self, mock_gemini, analyzer):
        """Test LLM integration."""
        # Arrange
        mock_gemini.generate.return_value = "Risk analysis text"

        # Act
        result = analyzer.analyze_with_llm(finding_data)

        # Assert
        mock_gemini.generate.assert_called_once()
        assert "Risk analysis" in result
```

## Rust Style Guide

We follow the official [Rust Style Guide](https://doc.rust-lang.org/1.0.0/style/) and use `rustfmt` for formatting.

### Code Formatting

```bash
# Format all Rust code
cargo fmt

# Check formatting
cargo fmt -- --check
```

Configuration in `rustfmt.toml`:

```toml
edition = "2021"
max_width = 100
use_small_heuristics = "Default"
```

### Naming Conventions

```rust
// Modules use snake_case
mod security_analyzer;

// Types use PascalCase
struct SecurityFinding {
    title: String,
    severity: Severity,
}

// Functions use snake_case
fn analyze_iam_policy(policy: &Policy) -> Result<Vec<Finding>> {
    // Implementation
}

// Constants use UPPER_SNAKE_CASE
const MAX_RETRY_ATTEMPTS: u32 = 3;

// Enums use PascalCase, variants use PascalCase
enum Severity {
    Critical,
    High,
    Medium,
    Low,
}
```

### Error Handling

Use `Result` and `?` operator:

```rust
use anyhow::{Context, Result};

fn collect_resources(project_id: &str) -> Result<Vec<Resource>> {
    let client = create_client()
        .context("Failed to create GCP client")?;

    let resources = client
        .list_resources(project_id)
        .context("Failed to list resources")?;

    Ok(resources)
}

// For library code, use specific error types
#[derive(Debug, thiserror::Error)]
enum CollectionError {
    #[error("Authentication failed: {0}")]
    AuthError(String),

    #[error("API call failed: {0}")]
    ApiError(#[from] ApiError),
}
```

### Documentation

Use doc comments:

```rust
/// Configuration for the Paddi CLI application.
///
/// This struct holds all configuration values needed to run
/// security audits on GCP projects.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    /// GCP project ID to audit
    pub project_id: String,

    /// Whether to use mock data instead of real API calls
    pub use_mock: bool,

    /// Output directory for generated reports
    pub output_dir: PathBuf,
}

impl Config {
    /// Load configuration from a TOML file.
    ///
    /// # Arguments
    ///
    /// * `path` - Path to the configuration file
    ///
    /// # Returns
    ///
    /// Returns the loaded configuration or an error if loading fails.
    ///
    /// # Example
    ///
    /// ```
    /// use paddi::config::Config;
    ///
    /// let config = Config::load("paddi.toml")?;
    /// println!("Project: {}", config.project_id);
    /// ```
    pub fn load<P: AsRef<Path>>(path: P) -> Result<Self> {
        let content = fs::read_to_string(path)?;
        let config: Config = toml::from_str(&content)?;
        Ok(config)
    }
}
```

### Testing

```rust
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_config_loading() {
        // Arrange
        let config_path = "tests/fixtures/test_config.toml";

        // Act
        let config = Config::load(config_path).unwrap();

        // Assert
        assert_eq!(config.project_id, "test-project");
        assert!(config.use_mock);
    }

    #[tokio::test]
    async fn test_async_collection() {
        // Arrange
        let collector = Collector::new_mock();

        // Act
        let resources = collector.collect_all().await.unwrap();

        // Assert
        assert!(!resources.is_empty());
    }
}
```

### Async Code

Use `tokio` for async runtime:

```rust
use tokio::time::{sleep, Duration};

async fn collect_with_retry(client: &Client) -> Result<Vec<Resource>> {
    let mut attempts = 0;

    loop {
        match client.list_resources().await {
            Ok(resources) => return Ok(resources),
            Err(e) if attempts < MAX_RETRY_ATTEMPTS => {
                attempts += 1;
                let delay = Duration::from_secs(2u64.pow(attempts));
                sleep(delay).await;
            }
            Err(e) => return Err(e.into()),
        }
    }
}
```

## Commit Message Convention

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Test additions or modifications
- `chore`: Maintenance tasks
- `perf`: Performance improvements

### Examples

```bash
# Feature
feat(collector): add Cloud Storage bucket collection

# Bug fix
fix(explainer): handle empty IAM policy bindings

# Documentation
docs(api): update collector API reference

# With breaking change
feat(cli)!: change configuration file format

BREAKING CHANGE: Configuration now uses TOML instead of JSON
```

## Code Review Checklist

Before submitting a PR, ensure:

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] New code has tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention
- [ ] No commented-out code
- [ ] No debug print statements
- [ ] Error handling is appropriate
- [ ] Security considerations addressed

## Linting

### Python Linting

```bash
# Run flake8
flake8 python_agents/

# Run pylint
pylint python_agents/

# Run mypy for type checking
mypy python_agents/
```

Configuration in `setup.cfg`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, E266, E501, W503
exclude = .git,__pycache__,venv

[mypy]
python_version = 3.8
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

### Rust Linting

```bash
# Run clippy
cargo clippy -- -D warnings

# Run with all features
cargo clippy --all-features -- -D warnings
```

## IDE Configuration

### VS Code

`.vscode/settings.json`:

```json
{
    "python.linting.enabled": true,
    "python.linting.flake8Enabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "[python]": {
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    },
    "[rust]": {
        "editor.formatOnSave": true
    }
}
```

### PyCharm

1. Set Python interpreter to virtual environment
2. Enable Black formatter
3. Configure import sorting with isort
4. Enable type checking with mypy

## Security Considerations

### Never Commit

- API keys or credentials
- Personal information
- Internal URLs or endpoints
- Sensitive configuration

### Always Consider

- Input validation
- SQL injection prevention
- Path traversal protection
- Rate limiting
- Authentication checks

Example of secure coding:

```python
# Good - validate input
def get_resource(resource_id: str) -> Resource:
    # Validate resource ID format
    if not re.match(r'^[a-zA-Z0-9-]+$', resource_id):
        raise ValueError("Invalid resource ID format")

    # Prevent path traversal
    safe_path = Path(resource_id).name
    return load_resource(safe_path)

# Bad - no validation
def get_resource(resource_id: str) -> Resource:
    return load_resource(resource_id)
```

## Performance Guidelines

### Python

```python
# Use generators for large datasets
def process_findings(findings: List[Finding]) -> Iterator[ProcessedFinding]:
    for finding in findings:
        # Process one at a time instead of loading all into memory
        yield process_single_finding(finding)

# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=128)
def get_project_metadata(project_id: str) -> ProjectMetadata:
    # Expensive API call cached
    return fetch_metadata(project_id)
```

### Rust

```rust
// Use references instead of cloning
fn process_findings(findings: &[Finding]) -> Vec<ProcessedFinding> {
    findings
        .iter()
        .map(|f| process_single_finding(f))
        .collect()
}

// Pre-allocate collections when size is known
let mut results = Vec::with_capacity(findings.len());
for finding in findings {
    results.push(process(finding)?);
}
```

## Questions?

If you have questions about code style:

1. Check existing code for examples
2. Ask in pull request reviews
3. Discuss in [GitHub Discussions](https://github.com/susumutomita/Paddi/discussions)
