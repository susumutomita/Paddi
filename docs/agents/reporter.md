# Reporter Agent Documentation

The Reporter Agent transforms security findings into professional, actionable reports in multiple formats.

## Overview

The Reporter Agent:
- Processes analyzed security findings
- Generates reports in Markdown, HTML, and JSON formats
- Uses customizable Jinja2 templates
- Creates executive summaries and technical details
- Supports multiple output formats and styles

## Architecture

```
┌─────────────────┐
│ explained.json  │
└────────┬────────┘
         │
┌────────▼────────┐
│ Reporter Agent  │
├─────────────────┤
│ - Template Engine│
│ - Format Builder│
│ - Style Manager │
└────────┬────────┘
         │
┌────────▼────────┐
│ Output Reports  │
├─────────────────┤
│ - audit.md      │
│ - audit.html    │
│ - audit.json    │
└─────────────────┘
```

## Usage

### Command Line Interface

```bash
# Basic usage
python python_agents/reporter/agent_reporter.py

# Specify input file
python python_agents/reporter/agent_reporter.py --input=./data/explained.json

# Generate specific formats
python python_agents/reporter/agent_reporter.py --formats=markdown,html

# Use custom template
python python_agents/reporter/agent_reporter.py --template=./templates/custom.j2

# Specify output directory
python python_agents/reporter/agent_reporter.py --output-dir=./reports

# Set report options
python python_agents/reporter/agent_reporter.py --include-summary --group-by-severity
```

### Python API

```python
from reporter.agent_reporter import ReporterAgent, ReporterConfig

# Initialize with configuration
config = ReporterConfig(
    formats=["markdown", "html", "json"],
    template_dir="./templates",
    output_dir="./output",
    include_executive_summary=True,
    group_by_severity=True
)

agent = ReporterAgent(config)

# Generate reports
reports = agent.generate_reports(findings)

# Generate specific format
markdown_report = agent.generate_markdown(findings)
html_report = agent.generate_html(findings)
```

## Configuration

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `formats` | list | ["markdown", "html"] | Output formats to generate |
| `template_dir` | string | "./templates" | Template directory path |
| `output_dir` | string | "./output" | Output directory for reports |
| `input_path` | string | "data/explained.json" | Input findings file |
| `include_summary` | boolean | True | Include executive summary |
| `include_toc` | boolean | True | Include table of contents |
| `group_by_severity` | boolean | True | Group findings by severity |
| `group_by_category` | boolean | False | Group findings by category |
| `include_charts` | boolean | True | Include charts in HTML |
| `theme` | string | "light" | HTML theme (light/dark) |
| `obsidian_compatible` | boolean | True | Make Markdown Obsidian-compatible |

### Template Variables

Templates have access to these variables:

```python
{
    'findings': List[Finding],
    'summary': {
        'total': int,
        'by_severity': dict,
        'by_category': dict,
        'critical_count': int,
        'high_count': int
    },
    'metadata': {
        'generated_at': datetime,
        'project_id': str,
        'report_version': str
    },
    'config': ReporterConfig
}
```

## Output Formats

### Markdown Report

```markdown
# Security Audit Report

Generated: 2024-01-15 10:30:00

## Executive Summary

**Critical Issues Found: 2**
**Total Findings: 15**

### Severity Distribution
- CRITICAL: 2
- HIGH: 5
- MEDIUM: 6
- LOW: 2

## Critical Findings

### 1. Overly Permissive Owner Role Assignment
**Severity:** CRITICAL  
**Category:** IAM_MISCONFIGURATION  
**Resource:** projects/my-project

**Description:**
The user account 'admin@example.com' has been granted the 'roles/owner' role...

**Recommendation:**
1. Remove the owner role assignment
2. Grant specific predefined roles based on actual needs
3. Use custom roles for fine-grained access control

---
```

### HTML Report

```html
<!DOCTYPE html>
<html>
<head>
    <title>Security Audit Report</title>
    <style>
        /* Professional styling */
        .critical { color: #d32f2f; }
        .high { color: #f57c00; }
        .medium { color: #fbc02d; }
        .low { color: #388e3c; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Security Audit Report</h1>
        <div class="summary-card">
            <h2>Executive Summary</h2>
            <div class="metrics">
                <div class="metric critical">
                    <span class="count">2</span>
                    <span class="label">Critical</span>
                </div>
                <!-- More metrics -->
            </div>
        </div>
        <!-- Detailed findings -->
    </div>
</body>
</html>
```

### JSON Report

```json
{
  "report": {
    "generated_at": "2024-01-15T10:30:00Z",
    "project_id": "my-project",
    "summary": {
      "total_findings": 15,
      "critical": 2,
      "high": 5,
      "medium": 6,
      "low": 2
    },
    "findings": [
      {
        "id": "iam-001",
        "severity": "CRITICAL",
        "title": "Overly Permissive Owner Role Assignment",
        "details": "..."
      }
    ]
  }
}
```

## Templates

### Default Templates

1. **report.md.j2** - Markdown template
2. **report.html.j2** - HTML template
3. **summary.md.j2** - Executive summary template
4. **email.html.j2** - Email notification template

### Custom Templates

Create custom templates using Jinja2:

```jinja2
{# custom-report.md.j2 #}
# {{ metadata.project_id }} Security Report

Generated: {{ metadata.generated_at }}

## Priority Actions Required

{% for finding in findings %}
{% if finding.severity in ['CRITICAL', 'HIGH'] %}
### {{ loop.index }}. {{ finding.title }}
- **Risk:** {{ finding.explanation }}
- **Action:** {{ finding.recommendation }}
{% endif %}
{% endfor %}

## Full Report

{% for finding in findings|sort(attribute='severity') %}
...
{% endfor %}
```

### Template Filters

Custom Jinja2 filters available:

```python
# Severity icon filter
{{ finding.severity|severity_icon }}  # Returns 🔴, 🟠, 🟡, 🟢

# Markdown sanitize
{{ finding.explanation|markdown_safe }}

# Date formatting
{{ metadata.generated_at|format_date }}

# Resource shortening
{{ finding.resource|short_resource }}  # projects/my-project → my-project
```

## Styling and Themes

### HTML Themes

```python
# Light theme (default)
config = ReporterConfig(theme="light")

# Dark theme
config = ReporterConfig(theme="dark")

# Custom theme
config = ReporterConfig(
    theme="custom",
    custom_css="./styles/corporate.css"
)
```

### Markdown Flavors

```python
# GitHub Flavored Markdown
config = ReporterConfig(markdown_flavor="github")

# Obsidian-compatible
config = ReporterConfig(
    markdown_flavor="obsidian",
    obsidian_tags=True,
    obsidian_links=True
)

# Standard Markdown
config = ReporterConfig(markdown_flavor="standard")
```

## Advanced Features

### Report Sections

```python
# Customize report sections
config = ReporterConfig(
    sections=[
        "executive_summary",
        "critical_findings",
        "recommendations",
        "technical_details",
        "appendix"
    ],
    section_options={
        "executive_summary": {
            "include_charts": True,
            "max_findings": 5
        }
    }
)
```

### Finding Grouping

```python
# Group by multiple criteria
config = ReporterConfig(
    grouping=[
        {
            "by": "severity",
            "order": ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        },
        {
            "by": "category",
            "order": ["IAM_MISCONFIGURATION", "PUBLIC_ACCESS"]
        }
    ]
)
```

### Charts and Visualizations

```python
# Enable charts in HTML reports
config = ReporterConfig(
    include_charts=True,
    chart_types=["severity_pie", "category_bar", "trend_line"],
    chart_library="chartjs"  # or "d3"
)
```

## Customization

### Adding New Formats

```python
class PDFReporter(BaseReporter):
    def generate(self, findings, output_path):
        # PDF generation logic
        pdf = PDFDocument()
        pdf.add_page()
        # ... add content
        pdf.save(output_path)

# Register format
reporter.register_format('pdf', PDFReporter())
```

### Custom Processors

```python
# Add custom finding processor
def add_jira_links(finding):
    # Add JIRA ticket links to findings
    finding.jira_ticket = f"SEC-{finding.id}"
    return finding

reporter.add_processor(add_jira_links)
```

## Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Generate Security Report
  run: |
    python reporter/agent_reporter.py \
      --formats=markdown,html \
      --output-dir=./artifacts

- name: Upload Reports
  uses: actions/upload-artifact@v2
  with:
    name: security-reports
    path: ./artifacts/
```

### Email Integration

```python
# Send report via email
from reporter.email_sender import EmailSender

sender = EmailSender(
    smtp_host="smtp.gmail.com",
    smtp_port=587,
    username="alerts@example.com"
)

# Send report
sender.send_report(
    to=["security-team@example.com"],
    subject="Security Audit Report - Critical Findings",
    report_path="./output/audit.html"
)
```

## Testing

### Unit Tests

```bash
# Run reporter tests
pytest python_agents/tests/test_reporter.py

# Test specific functionality
pytest python_agents/tests/test_reporter.py::test_markdown_generation
```

### Template Testing

```python
def test_custom_template():
    agent = ReporterAgent()
    
    # Test with sample findings
    findings = [
        Finding(
            severity="CRITICAL",
            title="Test Finding",
            explanation="Test explanation"
        )
    ]
    
    report = agent.generate_with_template(
        findings,
        template="custom.j2"
    )
    
    assert "Test Finding" in report
    assert "CRITICAL" in report
```

## Performance

### Large Report Handling

```python
# Stream large reports
def stream_report(findings, chunk_size=100):
    for chunk in chunks(findings, chunk_size):
        yield generate_chunk(chunk)

# Parallel generation
async def generate_formats_parallel(findings):
    tasks = [
        generate_markdown_async(findings),
        generate_html_async(findings),
        generate_json_async(findings)
    ]
    return await asyncio.gather(*tasks)
```

## Best Practices

1. **Template Management**
   - Version control templates
   - Test templates with various data sizes
   - Keep templates modular and reusable

2. **Output Organization**
   - Use timestamp in filenames
   - Archive old reports
   - Implement report retention policies

3. **Performance**
   - Cache compiled templates
   - Optimize for large finding sets
   - Use streaming for large reports

4. **Accessibility**
   - Include alt text for charts
   - Use semantic HTML
   - Ensure color contrast compliance

## API Reference

### ReporterAgent Class

```python
class ReporterAgent:
    def __init__(self, config: ReporterConfig):
        """Initialize reporter with configuration."""
        
    def generate_reports(self, findings: List[Finding]) -> Dict[str, str]:
        """Generate reports in all configured formats."""
        
    def generate_markdown(self, findings: List[Finding]) -> str:
        """Generate Markdown report."""
        
    def generate_html(self, findings: List[Finding]) -> str:
        """Generate HTML report."""
        
    def generate_json(self, findings: List[Finding]) -> str:
        """Generate JSON report."""
        
    def save_reports(self, reports: Dict[str, str], output_dir: str):
        """Save generated reports to disk."""
```

### Data Models

```python
@dataclass
class ReporterConfig:
    formats: List[str] = field(default_factory=lambda: ["markdown", "html"])
    template_dir: str = "./templates"
    output_dir: str = "./output"
    include_summary: bool = True
    group_by_severity: bool = True
    theme: str = "light"
    
@dataclass
class ReportMetadata:
    generated_at: datetime
    project_id: str
    organization_id: Optional[str]
    report_version: str
    total_findings: int
    
@dataclass
class ReportSection:
    title: str
    content: str
    order: int
    visible: bool = True
```