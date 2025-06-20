# Paddi Python Agents

This directory contains the Python implementation of Paddi's multi-agent system for GCP security audits.

## 🔄 Agent Workflow

1. **Agent A**: Collects GCP configurations → `data/collected.json`
2. **Agent B**: Analyzes with Gemini LLM → `data/explained.json`
3. **Agent C**: Generates reports → `output/audit.md` & `output/audit.html`

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run all agents in sequence (with mock data)
python run_example.py

# Or run individually:
python collector/agent_collector.py --use_mock=True
python explainer/agent_explainer.py --use_mock=True
python reporter/agent_reporter.py
```

## 📋 Agent A: GCP Configuration Collector

The collector agent retrieves Google Cloud Platform configurations including IAM policies and Security Command Center findings.

### Installation

```bash
cd python_agents
pip install -r requirements.txt
```

### Usage

#### Using Mock Data (Default)

```bash
python collector/agent_collector.py
```

#### With Custom Parameters

```bash
python collector/agent_collector.py \
  --project_id="my-gcp-project" \
  --organization_id="123456789" \
  --use_mock=True \
  --output_dir="data"
```

#### Using Real GCP APIs

To use real GCP APIs, you need to:

1. Set up Google Cloud authentication:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

2. Run with `--use_mock=False`:
   ```bash
   python collector/agent_collector.py \
     --project_id="my-real-project" \
     --organization_id="my-org-id" \
     --use_mock=False
   ```

### Output

The collector generates a JSON file at `data/collected.json` with the following structure:

```json
{
  "project_id": "example-project",
  "organization_id": "123456",
  "timestamp": "2024-01-01T00:00:00Z",
  "iam_policies": {
    "bindings": [...],
    "etag": "...",
    "version": 1
  },
  "scc_findings": [
    {
      "name": "...",
      "category": "OVERPRIVILEGED_SERVICE_ACCOUNT",
      "severity": "HIGH",
      ...
    }
  ]
}
```

### Development

#### Running Tests

```bash
make test
```

#### Running Tests with Coverage

```bash
make coverage
```

#### Code Quality Checks

Before committing, run:

```bash
make before-commit
```

This will:
1. Format code with Black
2. Run Flake8 linter
3. Execute all tests
4. Check coverage is above 80%

### Architecture

The collector follows SOLID principles:

- **Single Responsibility**: Each collector class has one responsibility
- **Open/Closed**: Easy to extend with new collectors
- **Interface Segregation**: Clean collector interface
- **Dependency Inversion**: Collectors depend on abstractions

### Error Handling

- Gracefully falls back to mock data if APIs are unavailable
- Logs all errors with appropriate severity
- Continues collection even if individual components fail

### Future Enhancements

- [ ] Add support for more GCP resources (Compute, Storage, etc.)
- [ ] Implement parallel collection for better performance
- [ ] Add configuration file support
- [ ] Support for multiple projects in one run

## 🧠 Agent B: Security Risk Explainer

The explainer agent analyzes collected GCP configurations using Google's Gemini LLM to identify security risks and provide recommendations.

### Usage

#### Using Mock Data (Default)

```bash
python explainer/agent_explainer.py --use_mock=True
```

#### With Custom Parameters

```bash
python explainer/agent_explainer.py \
  --project_id="my-gcp-project" \
  --location="us-central1" \
  --use_mock=True \
  --input_file="data/collected.json" \
  --output_dir="data"
```

#### Using Real Vertex AI/Gemini

To use real Gemini API:

1. Set up Google Cloud authentication:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
   ```

2. Ensure your project has Vertex AI API enabled:
   ```bash
   gcloud services enable aiplatform.googleapis.com
   ```

3. Run with `--use_mock=False`:
   ```bash
   python explainer/agent_explainer.py \
     --project_id="my-real-project" \
     --location="us-central1" \
     --use_mock=False
   ```

### Output

The explainer generates a JSON file at `data/explained.json` with security findings:

```json
[
  {
    "title": "Overly Permissive Owner Role Assignment",
    "severity": "HIGH",
    "explanation": "Multiple users have been granted the 'roles/owner' role...",
    "recommendation": "Remove the owner role from non-essential users..."
  },
  {
    "title": "Service Account with Editor Role",
    "severity": "MEDIUM",
    "explanation": "The service account has been granted 'roles/editor'...",
    "recommendation": "Replace the editor role with more specific roles..."
  }
]
```

### Features

- **Prompt Engineering**: Structured prompts for consistent security analysis
- **Rate Limiting**: Built-in delays and retry logic for API calls
- **Error Handling**: Graceful fallback to mock data on API failures
- **Severity Classification**: Automatic risk level assessment (HIGH/MEDIUM/LOW)
- **Contextual Analysis**: Considers both IAM policies and SCC findings

### Architecture

The explainer follows clean architecture principles:

- **LLMInterface**: Abstract interface for LLM interactions
- **PromptTemplate**: Centralized prompt management
- **SecurityFinding**: Type-safe data model for findings
- **GeminiSecurityAnalyzer**: Concrete implementation with Vertex AI
- **SecurityRiskExplainer**: Main orchestrator with file I/O

## 📊 Agent C: Security Audit Report Generator

The reporter agent converts security findings from Agent B into readable audit reports in Markdown and HTML formats.

### Usage

#### Default Usage

```bash
python reporter/agent_reporter.py
```

#### With Custom Parameters

```bash
python reporter/agent_reporter.py \
  --input_dir="data" \
  --output_dir="output" \
  --template_dir="templates"
```

### Output

The reporter generates two report formats:

1. **Markdown Report** (`output/audit.md`):
   - Obsidian-compatible format
   - Includes YAML frontmatter with metadata
   - Mermaid diagrams for severity visualization
   - Structured sections with clear remediation priorities
   - Emoji indicators for severity levels

2. **HTML Report** (`output/audit.html`):
   - Standalone HTML file with embedded CSS
   - Professional Google-style design
   - Color-coded severity badges
   - Responsive grid layout for severity summary
   - Interactive and printable format

### Features

- **Multiple Output Formats**: Markdown for documentation tools, HTML for web viewing
- **Jinja2 Template Support**: Full customization capability for both formats
- **Executive Summary**: High-level overview with severity breakdown
- **Visual Analytics**: Mermaid pie charts in Markdown, styled cards in HTML
- **Smart Metadata**: Automatically extracts project info from collector's output
- **Professional Styling**: Clean, audit-ready reports suitable for stakeholders
- **SOLID Architecture**: Clean separation of concerns with abstract generators

### Templates

Custom templates can be placed in the `templates/` directory:

- `report.md.j2`: Jinja2 template for Markdown output (sample included)
- `report.html.j2`: Jinja2 template for HTML output

Template variables available:
```python
report = {
    'project_name': str,      # Project ID from collector
    'audit_date': str,        # Current date (YYYY-MM-DD)
    'total_findings': int,    # Count of all findings
    'severity_counts': dict,  # {'HIGH': 2, 'MEDIUM': 1, ...}
    'findings': [             # List of SecurityFinding objects
        {
            'title': str,
            'severity': str,
            'explanation': str,
            'recommendation': str
        }
    ]
}
```

### Architecture

The reporter follows SOLID principles:

- **ReportGenerator** (ABC): Abstract base class defining the interface
- **MarkdownGenerator**: Generates Obsidian-compatible Markdown reports
- **HTMLGenerator**: Generates styled HTML reports with embedded CSS
- **ReportService**: Main service orchestrating report generation
- **SecurityFinding**: Data class for type-safe finding representation
- **AuditReport**: Data class containing all report data

### Example Output

The generated Markdown includes:
- YAML frontmatter for Obsidian
- Mermaid pie chart for severity distribution
- Tabular summary of findings
- Detailed findings with recommendations
- Remediation priority guidelines

The HTML report features:
- Modern, responsive design
- Color-coded severity indicators
- Summary cards with finding counts
- Professional layout suitable for sharing