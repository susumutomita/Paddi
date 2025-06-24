# Quick Start Guide

Get started with Paddi in minutes! This guide will walk you through running your first security audit.

## Prerequisites

Make sure you have completed the [installation](installation.md) process.

## Your First Audit (Mock Data)

The quickest way to see Paddi in action is using mock data:

```bash
# Using the CLI
paddi audit --use-mock

# Or using Python directly
cd python_agents
python run_example.py --use_mock=True
```

This will:

1. Collect sample GCP configuration data
2. Analyze it for security issues using Gemini
3. Generate reports in `output/` directory

## Your First Real Audit

### Step 1: Configure Your Project

Create or edit `paddi.toml`:

```toml
[general]
project_id = "my-gcp-project"
use_mock = false

[vertex_ai]
region = "us-central1"
model = "gemini-1.5-flash"
```

### Step 2: Run the Audit

```bash
paddi audit
```

### Step 3: Review Results

Check the generated reports:

- `output/audit.md` - Markdown report (Obsidian-compatible)
- `output/audit.html` - HTML report for web viewing

## Understanding the Output

### Report Structure

The audit report includes:

1. **Executive Summary**
   - Total findings by severity
   - Critical issues requiring immediate attention

2. **Detailed Findings**
   - Issue title and severity
   - Technical explanation
   - Specific recommendations
   - Affected resources

3. **Remediation Priority**
   - Ordered list of fixes by severity
   - Estimated effort for each fix

### Severity Levels

- **CRITICAL**: Immediate security risk (e.g., public data exposure)
- **HIGH**: Significant risk (e.g., overly permissive IAM)
- **MEDIUM**: Moderate risk (e.g., missing best practices)
- **LOW**: Minor issues (e.g., naming conventions)

## Common Use Cases

### 1. Audit Specific Resources

```bash
# Audit only IAM policies
paddi collect --resource-type=iam
paddi analyze
paddi report

# Audit only Security Command Center findings
paddi collect --resource-type=scc-findings
paddi analyze
paddi report
```

### 2. Scheduled Audits

Create a cron job for regular audits:

```bash
# Add to crontab
0 0 * * * /usr/local/bin/paddi audit --output-dir=/var/log/paddi/$(date +\%Y\%m\%d)
```

### 3. CI/CD Integration

Add to your CI pipeline:

```yaml
# GitHub Actions example
- name: Run Security Audit
  run: |
    paddi audit --fail-on-critical
```

### 4. Custom Analysis

Run individual agents with custom parameters:

```bash
# Collect with specific filters
python python_agents/collector/agent_collector.py \
  --project_id=my-project \
  --resource_types=iam,scc

# Analyze with custom prompts
python python_agents/explainer/agent_explainer.py \
  --severity_threshold=MEDIUM

# Generate report with custom template
python python_agents/reporter/agent_reporter.py \
  --template=custom-template.j2
```

## Quick Commands Reference

| Command | Description |
|---------|-------------|
| `paddi audit` | Run full audit pipeline |
| `paddi collect` | Collect GCP configurations only |
| `paddi analyze` | Analyze collected data only |
| `paddi report` | Generate reports only |
| `paddi config show` | Display current configuration |
| `paddi --help` | Show all available commands |

## Tips for Effective Audits

1. **Start with Mock Data**: Test your setup before running on production
2. **Use Filters**: Focus on specific resources to reduce noise
3. **Review Regularly**: Schedule weekly or monthly audits
4. **Track Progress**: Compare reports over time to measure improvement
5. **Customize Templates**: Adapt report format to your organization's needs

## Next Steps

- Learn about [Configuration Options](configuration.md)
- Explore [Advanced Scenarios](../examples/advanced-scenarios.md)
- Read about [Security Best Practices](../security/best-practices.md)
- Contribute to the project - see [Development Guide](../contributing/development.md)
