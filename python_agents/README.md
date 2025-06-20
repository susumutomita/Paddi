# Paddi Python Agents

This directory contains the Python implementation of Paddi's multi-agent system for GCP security audits.

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