# Configuration Guide

This guide covers all configuration options available in Paddi.

## Configuration File

Paddi uses TOML format for configuration. The default location is `paddi.toml` in the current directory.

### Basic Configuration

```toml
# paddi.toml

[general]
# Your GCP project ID
project_id = "my-gcp-project"

# Organization ID (optional, for org-level audits)
organization_id = "123456789"

# Use mock data instead of real GCP APIs
use_mock = false

# Default output directory
output_dir = "./output"

# Log level (DEBUG, INFO, WARNING, ERROR)
log_level = "INFO"
```

### Paths Configuration

```toml
[paths]
# Python interpreter to use
python_interpreter = "python3"

# Directory containing Python agents
agents_dir = "./python_agents"

# Data directory for intermediate files
data_dir = "./data"

# Templates directory
templates_dir = "./python_agents/templates"
```

### Execution Configuration

```toml
[execution]
# Timeout for each agent (seconds)
timeout_seconds = 300

# Number of parallel operations
parallelization = 4

# Retry failed operations
retry_count = 3

# Delay between retries (seconds)
retry_delay = 5
```

### Vertex AI Configuration

```toml
[vertex_ai]
# GCP region for Vertex AI
region = "us-central1"

# Model to use
model = "gemini-1.5-flash"

# Temperature for LLM responses (0.0 - 1.0)
temperature = 0.3

# Maximum tokens in response
max_tokens = 2048

# Custom prompt template (optional)
prompt_template = """
Analyze the following GCP configuration for security issues:
{configuration}

Focus on:
1. Overly permissive IAM policies
2. Public exposure risks
3. Compliance violations
"""
```

### Collector Configuration

```toml
[collector]
# Resource types to collect
resource_types = ["iam", "scc_findings", "compute", "storage"]

# IAM policy filters
iam_filters = {
    exclude_service_accounts = false,
    exclude_google_managed = true,
    member_domains = ["example.com"]
}

# Security Command Center settings
scc_settings = {
    organization_id = "123456789",
    filter = "state=\"ACTIVE\"",
    page_size = 100
}

# API rate limiting
rate_limit = {
    requests_per_second = 10,
    burst_size = 20
}
```

### Reporter Configuration

```toml
[reporter]
# Output formats
formats = ["markdown", "html", "json"]

# Template settings
template_settings = {
    include_executive_summary = true,
    include_technical_details = true,
    include_remediation_steps = true,
    group_by_severity = true
}

# HTML report settings
html_settings = {
    theme = "light",
    include_charts = true,
    embed_styles = true
}

# Markdown settings
markdown_settings = {
    flavor = "github",
    include_toc = true,
    obsidian_compatible = true
}
```

### Advanced Configuration

```toml
[filters]
# Severity thresholds
min_severity = "LOW"  # Don't report issues below this
fail_on_severity = "CRITICAL"  # Exit with error if found

# Resource filters
resource_filters = {
    include_projects = ["prod-*", "staging-*"],
    exclude_projects = ["test-*", "dev-*"],
    include_regions = ["us-central1", "europe-west1"],
    exclude_labels = ["environment:development"]
}

# Finding filters
finding_filters = {
    categories = ["PUBLIC_ACCESS", "IAM_MISCONFIG", "DATA_EXPOSURE"],
    exclude_patterns = ["test", "demo", "sample"]
}

[notifications]
# Webhook for results (optional)
webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
webhook_on_severity = ["CRITICAL", "HIGH"]

# Email notifications (requires SMTP setup)
email = {
    enabled = false,
    smtp_host = "smtp.gmail.com",
    smtp_port = 587,
    from_address = "paddi@example.com",
    to_addresses = ["security@example.com"],
    on_severity = ["CRITICAL"]
}
```

## Environment Variables

Configuration can also be set via environment variables:

```bash
# Override configuration file
export PADDI_CONFIG=/path/to/custom.toml

# Override specific settings
export PADDI_PROJECT_ID=my-project
export PADDI_USE_MOCK=true
export PADDI_LOG_LEVEL=DEBUG
export PADDI_OUTPUT_DIR=/tmp/paddi-output

# Vertex AI settings
export VERTEX_AI_REGION=us-central1
export VERTEX_AI_MODEL=gemini-1.5-pro

# Google Cloud settings
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

## CLI Flags

Command-line flags override configuration file settings:

```bash
# Override project ID
paddi audit --project-id=my-other-project

# Use mock data
paddi audit --use-mock

# Custom output directory
paddi audit --output-dir=/tmp/audit-results

# Verbose logging
paddi audit --log-level=DEBUG

# Custom configuration file
paddi audit --config=/path/to/custom.toml
```

## Configuration Precedence

Settings are applied in this order (later overrides earlier):

1. Default values
2. Configuration file (`paddi.toml`)
3. Environment variables
4. Command-line flags

## Per-Agent Configuration

Each agent can have its own configuration section:

```toml
[agents.collector]
# Collector-specific settings
timeout = 120
batch_size = 50

[agents.explainer]
# Explainer-specific settings
timeout = 180
max_retries = 5
cache_results = true

[agents.reporter]
# Reporter-specific settings
timeout = 60
compress_output = true
```

## Configuration Validation

Paddi validates configuration on startup:

```bash
# Validate configuration
paddi config validate

# Show effective configuration
paddi config show

# Show configuration with sources
paddi config show --verbose
```

## Example Configurations

### Minimal Configuration

```toml
[general]
project_id = "my-project"
```

### Production Configuration

```toml
[general]
project_id = "prod-security-audit"
organization_id = "123456789"
use_mock = false
log_level = "INFO"
output_dir = "/var/log/paddi/audits"

[execution]
timeout_seconds = 600
parallelization = 8
retry_count = 3

[vertex_ai]
region = "us-central1"
model = "gemini-1.5-pro"
temperature = 0.2

[collector]
resource_types = ["iam", "scc_findings", "compute", "storage", "network"]
rate_limit = { requests_per_second = 20 }

[reporter]
formats = ["markdown", "html", "json"]
template_settings = { include_executive_summary = true }

[filters]
min_severity = "MEDIUM"
fail_on_severity = "CRITICAL"

[notifications]
webhook_url = "https://hooks.slack.com/services/XXX/YYY/ZZZ"
webhook_on_severity = ["CRITICAL", "HIGH"]
```

### Development Configuration

```toml
[general]
project_id = "dev-project"
use_mock = true
log_level = "DEBUG"
output_dir = "./dev-output"

[execution]
timeout_seconds = 60
parallelization = 1

[vertex_ai]
region = "us-central1"
model = "gemini-1.5-flash"
temperature = 0.5
```

## Best Practices

1. **Use Version Control**: Keep your configuration files in git
2. **Separate Environments**: Use different configs for dev/staging/prod
3. **Secure Credentials**: Never commit credentials to configuration files
4. **Validate Changes**: Always run `paddi config validate` after changes
5. **Document Custom Settings**: Add comments to explain non-obvious configurations

## Troubleshooting

### Configuration Not Found

```bash
# Specify configuration file explicitly
paddi audit --config=/path/to/paddi.toml

# Or set environment variable
export PADDI_CONFIG=/path/to/paddi.toml
```

### Invalid Configuration

```bash
# Validate and show errors
paddi config validate --verbose

# Show effective configuration
paddi config show
```

### Permission Issues

```bash
# Ensure configuration file is readable
chmod 644 paddi.toml

# For system-wide configuration
sudo cp paddi.toml /etc/paddi/paddi.toml
```