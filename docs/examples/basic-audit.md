# Basic Audit Examples

This guide provides practical examples of running basic security audits with Paddi.

## Quick Start Example

### Running Your First Audit

```bash
# Using mock data (no GCP credentials required)
paddi audit --use-mock

# Output:
# ✓ Collecting GCP resources... Done
# ✓ Analyzing security risks... Done
# ✓ Generating reports... Done
#
# Audit complete! Reports saved to ./output/
# - audit.md (Markdown report)
# - audit.html (HTML report)
#
# Summary: 15 findings (2 CRITICAL, 5 HIGH, 6 MEDIUM, 2 LOW)
```

## Real GCP Project Audit

### Prerequisites

```bash
# Authenticate with Google Cloud
gcloud auth application-default login

# Set your project
gcloud config set project my-project-id

# Enable required APIs
gcloud services enable iam.googleapis.com
gcloud services enable securitycenter.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### Basic Audit Command

```bash
# Run full audit on your project
paddi audit --project-id=my-project-id

# Or if project is set in config
paddi audit
```

## Common Scenarios

### 1. Daily Security Check

Create a simple script for daily audits:

```bash
#!/bin/bash
# daily-audit.sh

DATE=$(date +%Y%m%d)
OUTPUT_DIR="./audits/$DATE"

echo "Running daily security audit..."
paddi audit --output-dir="$OUTPUT_DIR" --fail-on-critical

if [ $? -eq 4 ]; then
    echo "CRITICAL findings detected! Check $OUTPUT_DIR/audit.html"
    # Send notification
    mail -s "Critical Security Findings" team@example.com < "$OUTPUT_DIR/audit.md"
else
    echo "Audit complete. No critical findings."
fi
```

### 2. IAM Policy Review

Focus on IAM policies only:

```bash
# Collect only IAM data
paddi collect --resource-types=iam

# Analyze with focus on permissions
paddi analyze --categories=IAM_MISCONFIGURATION

# Generate report
paddi report
```

Example output in `audit.md`:

```markdown
# Security Audit Report

## Critical Findings

### 1. Overly Permissive Owner Role
**Severity:** CRITICAL
**Resource:** projects/my-project

The following accounts have owner-level access:
- user:developer@example.com
- serviceAccount:test-sa@my-project.iam.gserviceaccount.com

**Recommendation:**
- Remove owner role from developer@example.com
- Grant specific roles like roles/editor instead
- For service accounts, use custom roles with minimal permissions
```

### 3. Security Command Center Integration

Analyze existing SCC findings:

```bash
# Collect SCC findings
paddi collect --resource-types=scc_findings

# Enhance with AI analysis
paddi analyze

# Generate detailed report
paddi report --include-technical-details
```

### 4. Compliance-Focused Audit

Run audit with compliance framework focus:

```python
# custom_audit.py
from python_agents.explainer.agent_explainer import ExplainerAgent

# Configure for compliance
config = {
    "prompt_template": """
    Analyze the following GCP configuration for compliance with:
    - CIS Google Cloud Platform Benchmark
    - PCI-DSS requirements
    - HIPAA security rules

    Focus on:
    1. Access controls
    2. Encryption requirements
    3. Audit logging
    4. Network security

    Configuration:
    {configuration}
    """
}

agent = ExplainerAgent(config)
findings = agent.analyze(collected_data)
```

## Working with Output

### Understanding the Reports

After running an audit, you'll find these files:

```
output/
├── audit.md          # Markdown report (Obsidian-compatible)
├── audit.html        # HTML report with charts
└── audit.json        # Structured data for automation
```

### Markdown Report Structure

```markdown
# Security Audit Report

Generated: 2024-01-15 10:30:00

## Executive Summary

**Critical Issues:** 2
**Total Findings:** 15

### Top Risks
1. Public storage bucket exposing sensitive data
2. Service account with excessive permissions
3. Missing encryption on database instances

## Findings by Severity

### CRITICAL (2)

#### 1. Public Storage Bucket
- **Resource:** gs://my-data-bucket
- **Risk:** Bucket is publicly accessible
- **Impact:** Sensitive data exposure
- **Fix:** Remove allUsers and allAuthenticatedUsers bindings

### HIGH (5)
...
```

### HTML Report Features

The HTML report includes:

- Interactive charts showing severity distribution
- Filtering by severity and category
- Expandable finding details
- Print-friendly formatting
- Dark/light theme toggle

### JSON Output for Automation

```json
{
  "metadata": {
    "generated_at": "2024-01-15T10:30:00Z",
    "project_id": "my-project",
    "total_findings": 15
  },
  "findings": [
    {
      "id": "iam-001",
      "severity": "CRITICAL",
      "title": "Overly Permissive Owner Role",
      "category": "IAM_MISCONFIGURATION",
      "resource": "projects/my-project",
      "risk_score": 9.5
    }
  ]
}
```

## Automation Examples

### 1. Slack Notification

```python
#!/usr/bin/env python3
# notify_critical.py

import json
import requests
import subprocess

# Run audit
result = subprocess.run(
    ["paddi", "audit", "--output-format=json"],
    capture_output=True,
    text=True
)

# Parse results
data = json.loads(result.stdout)
critical_count = sum(1 for f in data["findings"] if f["severity"] == "CRITICAL")

if critical_count > 0:
    # Send Slack notification
    webhook_url = "https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

    message = {
        "text": f"🚨 Security Audit Alert",
        "attachments": [{
            "color": "danger",
            "title": f"{critical_count} Critical Findings",
            "text": "Review the full report at: <link>",
            "fields": [
                {
                    "title": finding["title"],
                    "value": finding["resource"],
                    "short": True
                }
                for finding in data["findings"]
                if finding["severity"] == "CRITICAL"
            ]
        }]
    }

    requests.post(webhook_url, json=message)
```

### 2. GitHub Action

```yaml
# .github/workflows/security-audit.yml
name: Weekly Security Audit

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Cloud SDK
      uses: google-github-actions/setup-gcloud@v1
      with:
        service_account_key: ${{ secrets.GCP_SA_KEY }}
        project_id: ${{ secrets.GCP_PROJECT_ID }}

    - name: Install Paddi
      run: |
        cd cli
        make install

    - name: Run Security Audit
      run: |
        paddi audit --fail-on-critical

    - name: Upload Reports
      uses: actions/upload-artifact@v3
      with:
        name: security-reports
        path: output/

    - name: Create Issue for Critical Findings
      if: failure()
      uses: actions/github-script@v6
      with:
        script: |
          github.rest.issues.create({
            owner: context.repo.owner,
            repo: context.repo.repo,
            title: '🚨 Critical Security Findings',
            body: 'The security audit found critical issues. Check the [workflow run](${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}) for details.',
            labels: ['security', 'critical']
          })
```

### 3. CSV Export

```python
#!/usr/bin/env python3
# export_to_csv.py

import json
import csv
from pathlib import Path

# Read JSON report
with open("output/audit.json") as f:
    data = json.load(f)

# Export to CSV
with open("output/findings.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=[
        "id", "title", "severity", "category",
        "resource", "risk_score", "recommendation"
    ])

    writer.writeheader()
    for finding in data["findings"]:
        writer.writerow({
            "id": finding["id"],
            "title": finding["title"],
            "severity": finding["severity"],
            "category": finding["category"],
            "resource": finding["resource"],
            "risk_score": finding.get("risk_score", 0),
            "recommendation": finding["recommendation"]
        })

print("Exported findings to output/findings.csv")
```

## Filtering and Customization

### Filter by Severity

```bash
# Only analyze high-risk issues
paddi analyze --min-severity=HIGH

# Only report critical findings
paddi report --min-severity=CRITICAL
```

### Custom Categories

```bash
# Focus on specific security categories
paddi analyze --categories=IAM_MISCONFIGURATION,PUBLIC_ACCESS

# Exclude certain categories
paddi analyze --exclude-categories=NAMING_CONVENTION
```

### Resource Filtering

```toml
# paddi.toml
[collector]
resource_filters = {
    include_projects = ["prod-*"],
    exclude_projects = ["test-*", "dev-*"],
    include_regions = ["us-central1", "europe-west1"]
}
```

## Performance Tips

### 1. Use Caching

```bash
# Skip collection if data exists
if [ -f "data/collected.json" ]; then
    paddi audit --skip-collect
else
    paddi audit
fi
```

### 2. Parallel Execution

```bash
# Run agents in parallel
paddi audit --parallel
```

### 3. Batch Processing

```bash
# Process multiple projects efficiently
for project in $(gcloud projects list --format="value(projectId)"); do
    echo "Auditing $project..."
    paddi audit --project-id=$project --output-dir="./audits/$project" &
done
wait
```

## Troubleshooting Common Issues

### Authentication Errors

```bash
# Error: Could not authenticate to Google Cloud
# Solution:
gcloud auth application-default login
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
```

### API Quota Exceeded

```bash
# Error: Quota exceeded for api.aiplatform.googleapis.com
# Solution: Use rate limiting
paddi audit --rate-limit=5  # 5 requests per second
```

### No Findings Reported

```bash
# Check if mock mode is accidentally enabled
paddi config show | grep use_mock

# Run with debug logging
paddi audit --log-level=DEBUG
```

## Next Steps

- Review [Advanced Scenarios](advanced-scenarios.md) for complex use cases
- Read [Security Best Practices](../security/best-practices.md)
- Explore [CLI Commands](../cli/commands.md) for more options
- Check [Contributing Guide](../contributing/development.md) to extend Paddi
