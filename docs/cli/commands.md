# CLI Commands Reference

This document provides a comprehensive reference for all Paddi CLI commands.

## Overview

The Paddi CLI provides a unified interface for running security audits on Google Cloud Platform resources.

```bash
paddi [OPTIONS] COMMAND [ARGS]
```

## Global Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--config` | `-c` | Path to configuration file | `./paddi.toml` |
| `--project-id` | `-p` | GCP project ID | From config |
| `--log-level` | `-l` | Logging level (DEBUG/INFO/WARNING/ERROR) | INFO |
| `--output-dir` | `-o` | Output directory for results | `./output` |
| `--no-color` | | Disable colored output | False |
| `--version` | `-v` | Show version information | |
| `--help` | `-h` | Show help message | |

## Commands

### `paddi audit`

Run a complete security audit pipeline.

```bash
paddi audit [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--use-mock` | Use mock data instead of real GCP APIs | False |
| `--skip-collect` | Skip collection phase (use existing data) | False |
| `--skip-analyze` | Skip analysis phase | False |
| `--skip-report` | Skip report generation | False |
| `--fail-on-critical` | Exit with error if critical findings | False |
| `--fail-on-severity` | Exit with error on specified severity | None |
| `--parallel` | Run agents in parallel | False |
| `--timeout` | Overall timeout in seconds | 600 |

**Examples:**

```bash
# Run full audit on current project
paddi audit

# Run audit with mock data
paddi audit --use-mock

# Run audit and fail on critical findings
paddi audit --fail-on-critical

# Run audit with custom timeout
paddi audit --timeout=300

# Skip collection and use existing data
paddi audit --skip-collect
```

### `paddi collect`

Run only the collection phase.

```bash
paddi collect [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--resource-types` | Comma-separated resource types to collect | iam,scc |
| `--use-mock` | Use mock data | False |
| `--output` | Output file path | data/collected.json |
| `--filters` | JSON string of collection filters | {} |
| `--page-size` | API pagination size | 100 |

**Examples:**

```bash
# Collect all resources
paddi collect

# Collect only IAM policies
paddi collect --resource-types=iam

# Collect with custom filters
paddi collect --filters='{"exclude_service_accounts": true}'

# Use mock data
paddi collect --use-mock
```

### `paddi analyze`

Run only the analysis phase on collected data.

```bash
paddi analyze [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Input file with collected data | data/collected.json |
| `--output` | Output file for findings | data/explained.json |
| `--use-mock` | Use mock LLM responses | False |
| `--model` | Gemini model to use | gemini-1.5-flash |
| `--min-severity` | Minimum severity to report | LOW |
| `--categories` | Comma-separated categories to analyze | All |

**Examples:**

```bash
# Analyze collected data
paddi analyze

# Use specific model
paddi analyze --model=gemini-1.5-pro

# Filter by severity
paddi analyze --min-severity=MEDIUM

# Analyze specific categories
paddi analyze --categories=IAM_MISCONFIGURATION,PUBLIC_ACCESS
```

### `paddi report`

Generate reports from analyzed findings.

```bash
paddi report [OPTIONS]
```

**Options:**

| Option | Description | Default |
|--------|-------------|---------|
| `--input` | Input file with findings | data/explained.json |
| `--formats` | Comma-separated output formats | markdown,html |
| `--template` | Custom template file | Default templates |
| `--no-summary` | Exclude executive summary | False |
| `--group-by` | Grouping strategy (severity/category) | severity |

**Examples:**

```bash
# Generate default reports
paddi report

# Generate only Markdown
paddi report --formats=markdown

# Use custom template
paddi report --template=./custom-template.j2

# Group by category
paddi report --group-by=category
```

### `paddi config`

Manage Paddi configuration.

```bash
paddi config SUBCOMMAND [OPTIONS]
```

**Subcommands:**

#### `paddi config show`

Display current configuration.

```bash
paddi config show [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--verbose` | Show configuration sources |
| `--format` | Output format (toml/json/yaml) |

**Examples:**

```bash
# Show current configuration
paddi config show

# Show with sources
paddi config show --verbose

# Output as JSON
paddi config show --format=json
```

#### `paddi config validate`

Validate configuration file.

```bash
paddi config validate [OPTIONS]
```

**Examples:**

```bash
# Validate current config
paddi config validate

# Validate specific file
paddi config validate --config=./custom.toml
```

#### `paddi config init`

Initialize a new configuration file.

```bash
paddi config init [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--force` | Overwrite existing configuration |
| `--minimal` | Create minimal configuration |

**Examples:**

```bash
# Create default configuration
paddi config init

# Create minimal config
paddi config init --minimal

# Overwrite existing
paddi config init --force
```

### `paddi list`

List available resources and options.

```bash
paddi list RESOURCE [OPTIONS]
```

**Resources:**

- `models` - List available Gemini models
- `regions` - List available Vertex AI regions
- `resource-types` - List collectible resource types
- `templates` - List available report templates

**Examples:**

```bash
# List available models
paddi list models

# List regions
paddi list regions

# List resource types
paddi list resource-types
```

### `paddi validate`

Validate collected or analyzed data.

```bash
paddi validate FILE [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--schema` | Schema to validate against |
| `--strict` | Enable strict validation |

**Examples:**

```bash
# Validate collected data
paddi validate data/collected.json

# Validate findings
paddi validate data/explained.json --strict
```

## Environment Variables

CLI options can be set via environment variables:

```bash
# Set project ID
export PADDI_PROJECT_ID=my-project

# Set log level
export PADDI_LOG_LEVEL=DEBUG

# Set configuration file
export PADDI_CONFIG=/path/to/config.toml

# Use mock mode
export PADDI_USE_MOCK=true

# Set output directory
export PADDI_OUTPUT_DIR=/tmp/paddi-output
```

## Configuration File Usage

The CLI respects settings in the configuration file:

```toml
# paddi.toml
[general]
project_id = "my-project"
use_mock = false

[cli]
default_command = "audit"
confirm_critical_actions = true
progress_bar = true
```

## Output Formats

### JSON Output

Get JSON output for scripting:

```bash
# Output audit results as JSON
paddi audit --output-format=json

# Parse with jq
paddi audit --output-format=json | jq '.findings[] | select(.severity == "CRITICAL")'
```

### Quiet Mode

Suppress progress output:

```bash
# Run quietly (only show errors)
paddi audit --quiet

# Run with minimal output
paddi audit --log-level=ERROR
```

## Exit Codes

| Code | Description |
|------|-------------|
| 0 | Success |
| 1 | General error |
| 2 | Configuration error |
| 3 | Authentication error |
| 4 | Critical findings found (with --fail-on-critical) |
| 5 | Timeout exceeded |
| 6 | Invalid input data |

## Shell Completion

Enable shell completion for better CLI experience:

### Bash

```bash
# Add to ~/.bashrc
eval "$(paddi completion bash)"
```

### Zsh

```bash
# Add to ~/.zshrc
eval "$(paddi completion zsh)"
```

### Fish

```bash
# Add to ~/.config/fish/config.fish
paddi completion fish | source
```

## Advanced Usage

### Chaining Commands

```bash
# Run individual phases with custom options
paddi collect --resource-types=iam && \
paddi analyze --model=gemini-1.5-pro && \
paddi report --formats=html
```

### Scripting

```bash
#!/bin/bash
# audit.sh - Run audit and notify on critical findings

OUTPUT=$(paddi audit --output-format=json)
CRITICAL_COUNT=$(echo "$OUTPUT" | jq '.summary.critical')

if [ "$CRITICAL_COUNT" -gt 0 ]; then
    # Send notification
    curl -X POST https://hooks.slack.com/services/XXX \
        -d "{\"text\": \"Critical security findings: $CRITICAL_COUNT\"}"
fi
```

### CI/CD Integration

```yaml
# .github/workflows/security-audit.yml
name: Security Audit
on:
  schedule:
    - cron: '0 0 * * *'
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Install Paddi
        run: |
          cd cli && make install
      - name: Run Audit
        run: |
          paddi audit --fail-on-critical
      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: security-reports
          path: ./output/
```

## Debugging

### Verbose Output

```bash
# Enable debug logging
paddi audit --log-level=DEBUG

# Trace API calls
PADDI_TRACE_API=true paddi collect

# Debug configuration loading
PADDI_DEBUG_CONFIG=true paddi audit
```

### Dry Run

```bash
# Show what would be done without executing
paddi audit --dry-run

# Validate configuration without running
paddi config validate
```

## Common Patterns

### Daily Audits

```bash
# Cron job for daily audits
0 2 * * * /usr/local/bin/paddi audit --output-dir=/var/log/paddi/$(date +\%Y\%m\%d)
```

### Project Iteration

```bash
# Audit multiple projects
for project in prod-web prod-api prod-data; do
    paddi audit --project-id=$project --output-dir=./audits/$project
done
```

### Severity Filtering

```bash
# Only show high severity issues
paddi analyze --min-severity=HIGH && paddi report
```

## Tips and Tricks

1. **Use aliases for common commands:**

   ```bash
   alias audit-mock='paddi audit --use-mock'
   alias audit-prod='paddi audit --fail-on-critical'
   ```

2. **Combine with other tools:**

   ```bash
   # Send report via email
   paddi report --formats=html && \
   mail -s "Security Audit" security@example.com < output/audit.html
   ```

3. **Custom output processing:**

   ```bash
   # Extract critical findings
   paddi audit --output-format=json | \
   jq -r '.findings[] | select(.severity == "CRITICAL") | .title'
   ```
