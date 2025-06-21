# 🩹 Paddi: AI-Powered Multi-Agent Cloud Audit System

[![CI](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml/badge.svg)](https://github.com/susumutomita/Paddi)
![Last commit](https://img.shields.io/github/last-commit/susumutomita/Paddi)
![Top language](https://img.shields.io/github/languages/top/susumutomita/Paddi)
![Pull requests](https://img.shields.io/github/issues-pr/susumutomita/Paddi)
![Code size](https://img.shields.io/github/languages/code-size/susumutomita/Paddi)
![Repo size](https://img.shields.io/github/repo-size/susumutomita/Paddi)

**Paddi** is a multi-agent system that automates cloud security audits using Google Cloud AI and a unified CLI interface. It orchestrates three specialized agents that work together to collect configurations, analyze security risks with AI, and generate comprehensive audit reports.

Built for the [Google Cloud AI Hackathon: Multi-Agent Edition](https://googlecloudmultiagents.devpost.com/). This project demonstrates how AI agents can transform security workflows by automating manual audit processes while maintaining enterprise-grade quality.

---

## 🚀 Quick Start

Get started with Paddi in less than a minute:

```bash
# Install Paddi (future Homebrew support)
# brew install paddi

# Try Paddi with sample data - zero configuration needed!
paddi init

# Output:
# ✅ Paddi init 完了:
#   • Markdown: output/audit.md
#   • HTML: output/audit.html（ブラウザで開けます）
#   • サイトプレビュー: npx honkit serve docs/
```

That's it! Paddi automatically runs the full audit pipeline with sample GCP data, demonstrating its capabilities without requiring any GCP credentials or setup.

---

## 🏗️ Architecture

Paddi implements a **three-agent pipeline** architecture, where each agent has a single, well-defined responsibility:

```mermaid
graph LR
    A[Collector Agent] -->|collected.json| B[Explainer Agent]
    B -->|explained.json| C[Reporter Agent]
    C --> D[Audit Reports]
    
    style A fill:#4285f4,stroke:#1a73e8,stroke-width:2px,color:#fff
    style B fill:#ea4335,stroke:#d33b27,stroke-width:2px,color:#fff
    style C fill:#34a853,stroke:#1e8e3e,stroke-width:2px,color:#fff
    style D fill:#fbbc04,stroke:#f9ab00,stroke-width:2px,color:#000
```

### Agent Details

#### 1. **Collector Agent** (`python_agents/collector/`)
- **Purpose**: Gather GCP configuration data
- **Input**: GCP project ID or mock data flag
- **Output**: `data/collected.json` containing IAM policies and Security Command Center findings
- **Key Features**:
  - Real GCP API integration via `google-cloud-iam` and `google-cloud-securitycenter`
  - Mock data support for testing and demos
  - Extensible to support multiple cloud providers

#### 2. **Explainer Agent** (`python_agents/explainer/`)
- **Purpose**: Analyze security risks using AI
- **Input**: `data/collected.json` from Collector
- **Output**: `data/explained.json` with AI-generated security insights
- **Key Features**:
  - Powered by Google's Gemini AI (via Vertex AI)
  - Categorizes findings by severity (CRITICAL, HIGH, MEDIUM, LOW)
  - Provides actionable recommendations in natural language
  - Mock mode for offline development

#### 3. **Reporter Agent** (`python_agents/reporter/`)
- **Purpose**: Generate human-readable audit reports
- **Input**: `data/explained.json` from Explainer
- **Output**: Multiple report formats:
  - `output/audit.md` - Markdown for documentation tools
  - `output/audit.html` - Interactive HTML report
  - `docs/` - HonKit site structure for web hosting
- **Key Features**:
  - Jinja2 templating for customizable reports
  - Multiple output formats
  - Severity-based organization
  - Japanese and English support

### Orchestration Layer

The **Rust CLI** (`cli/`) provides a unified interface to orchestrate the Python agents:

```rust
// Simplified orchestration flow
orchestrator.run_collector()?;
orchestrator.run_explainer()?;
orchestrator.run_reporter(formats)?;
```

---

## 📚 CLI Usage Guide

### Installation

```bash
# Clone the repository
git clone https://github.com/susumutomita/Paddi.git
cd Paddi

# Build the Rust CLI
cd cli
cargo build --release

# Add to PATH (or use cargo install)
export PATH=$PATH:$(pwd)/target/release
```

### Core Commands

#### `paddi init` - Zero-Setup Trial
```bash
# Run a complete audit with sample data
paddi init

# Skip the automatic pipeline run
paddi init --skip-run

# Specify output directory
paddi init --output custom-output/
```

#### `paddi audit` - Full Pipeline
```bash
# Run complete audit pipeline
paddi audit

# Use mock data instead of real GCP
paddi audit --use-mock

# Specify GCP project
paddi audit --project-id my-gcp-project

# Verbose output
paddi audit -v
```

#### `paddi collect` - Data Collection Only
```bash
# Collect from real GCP project
paddi collect --project-id my-gcp-project

# Collect mock data for testing
paddi collect --use-mock
```

#### `paddi analyze` - AI Analysis Only
```bash
# Analyze collected data with AI
paddi analyze

# Use mock AI responses
paddi analyze --use-mock
```

#### `paddi report` - Generate Reports
```bash
# Generate default reports (Markdown + HTML)
paddi report

# Generate specific formats
paddi report --format markdown,html,honkit

# Custom input/output directories
paddi report --input-dir data/ --output-dir reports/
```

#### `paddi config` - Configuration Management
```bash
# Show current configuration
paddi config show

# Validate configuration
paddi config validate

# Initialize new configuration
paddi config init
```

### Configuration

Paddi uses TOML configuration files. Create `paddi.toml`:

```toml
[gcp]
project_id = "my-gcp-project"
use_mock = false

[paths]
data_dir = "data"
output_dir = "output"

[python]
command = "python3"
agents_path = "python_agents"

[execution]
timeout_seconds = 300
```

### Environment Variables

- `PADDI_CONFIG` - Path to configuration file
- `GOOGLE_APPLICATION_CREDENTIALS` - GCP service account key
- `RUST_LOG` - Logging level (info, debug, trace)

---

## 🎯 Use Cases

### 1. **Development & Testing**
```bash
# Quick start with sample data
paddi init

# Test individual agents
paddi collect --use-mock
paddi analyze --use-mock
paddi report
```

### 2. **Real GCP Audits**
```bash
# Authenticate with GCP
gcloud auth application-default login

# Run full audit
paddi audit --project-id production-project
```

### 3. **CI/CD Integration**
```yaml
# GitHub Actions example
- name: Run Security Audit
  run: |
    paddi audit --project-id ${{ secrets.GCP_PROJECT }}
    
- name: Upload Reports
  uses: actions/upload-artifact@v3
  with:
    name: audit-reports
    path: output/
```

### 4. **Scheduled Audits**
```bash
# Cron job for weekly audits
0 0 * * 0 paddi audit --project-id prod && \
  gsutil cp output/audit.html gs://audit-reports/$(date +%Y%m%d).html
```

---

## 📊 Sample Output

### Markdown Report (`output/audit.md`)
```markdown
# Security Audit Report - example-project-123

**Audit Date:** 2024-01-21
**Total Findings:** 4

## Executive Summary

This security audit identified 4 findings across your GCP infrastructure.

### Severity Breakdown
- **CRITICAL**: 1 findings
- **HIGH**: 1 findings
- **MEDIUM**: 1 findings
- **LOW**: 1 findings

## Detailed Findings

### 1. Public Bucket Access
**Severity:** CRITICAL
**Explanation:** The bucket 'sensitive-data-bucket' has public access enabled...
**Recommendation:** Remove allUsers and allAuthenticatedUsers from bucket IAM policy
```

### HonKit Documentation (`docs/`)
- Interactive web documentation
- Severity-based navigation
- Japanese localization
- Searchable content
- Export to PDF capability

---

## 🛠️ Development

### Prerequisites
- Python 3.10+
- Rust 1.70+
- Google Cloud SDK (for real GCP audits)

### Setup Development Environment
```bash
# Python agents
cd python_agents
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Rust CLI
cd ../cli
cargo build
cargo test

# Run quality checks
cd ../python_agents
make before-commit
```

### Testing
```bash
# Python tests
pytest --cov=. --cov-report=term-missing

# Rust tests
cargo test

# Integration tests
./scripts/integration_test.sh
```

---

## 🌐 Tech Stack

- **Python 3.10+**: Agent implementation
- **Rust**: CLI and orchestration
- **Google Vertex AI**: Gemini Pro for AI analysis
- **Google Cloud APIs**: IAM, Security Command Center
- **Jinja2**: Report templating
- **HonKit**: Documentation generation
- **Tokio**: Async runtime for Rust

---

## 🚀 Roadmap

- [ ] Homebrew formula for easy installation
- [ ] Support for AWS and Azure
- [ ] Custom rule definitions
- [ ] Slack/Teams notifications
- [ ] Compliance frameworks (SOC2, ISO27001)
- [ ] Web UI dashboard
- [ ] Agent marketplace

---

## 👥 Contributors

- **Strategy & Architecture**: [Susumu Tomita](https://susumutomita.netlify.app/) - Full Stack Developer
- **Implementation**: Claude Code + AI collaboration

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/contributing/development.md) for details.

```bash
# Fork and clone
git clone https://github.com/YOUR-USERNAME/Paddi.git

# Create feature branch
git checkout -b feature/amazing-feature

# Make changes and test
make test

# Submit PR
git push origin feature/amazing-feature
```

---

## 📄 License

Paddi is licensed under the [MIT License](LICENSE).

---

## 🙏 Acknowledgments

- Google Cloud AI Hackathon organizers
- The open-source community
- Early adopters and testers

---

<p align="center">
  Made with ❤️ for the security community
</p>