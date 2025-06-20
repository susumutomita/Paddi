# Python Agents for Paddi

This directory contains the Python implementation of the multi-agent system for cloud security audits.

## 🏗️ Architecture

The system follows SOLID principles and consists of three main agents:

1. **Agent A (Collector)**: Collects GCP configuration data
2. **Agent B (Explainer)**: Uses Vertex AI to explain security risks (to be implemented)
3. **Agent C (Reporter)**: Generates Markdown/HTML reports (to be implemented)

## 🚀 Quick Start

### Installation

```bash
cd python_agents
pip install -r requirements.txt
```

### Running the Collector

With mock data (default):
```bash
python collector/agent_collector.py
```

With real GCP data (requires authentication):
```bash
python collector/agent_collector.py --use_mock=False
```

Custom output path:
```bash
python collector/agent_collector.py --output_path=custom/path.json
```

## 🧪 Development

### Running Tests

```bash
make test              # Run unit tests
make test-coverage     # Run tests with coverage report
```

### Code Quality

```bash
make lint              # Run linting
make format            # Format code with black and isort
make before-commit     # Run all quality checks
```

## 📁 Directory Structure

```
python_agents/
├── collector/         # Agent A: GCP Configuration Collector
├── explainer/         # Agent B: Gemini-based Explainer (TBD)
├── reporter/          # Agent C: Report Generator (TBD)
├── tests/             # Unit tests
├── data/              # Intermediate data storage
└── output/            # Generated reports
```

## 🔧 Configuration

The collector supports both mock data and real GCP API calls. When using real GCP APIs, ensure you have:

1. Set up Application Default Credentials
2. Proper IAM permissions for:
   - Cloud Resource Manager API
   - Security Command Center API
   - IAM API

## 📊 Output Format

The collector outputs data in JSON format with the following structure:

```json
{
  "IAMCollector": {
    "policies": [...],
    "custom_roles": [...]
  },
  "SCCFindingsCollector": {
    "findings": [...]
  }
}
```

## 🤝 Contributing

1. Follow SOLID principles
2. Maintain test coverage above 80%
3. Run `make before-commit` before pushing changes
4. Update documentation as needed