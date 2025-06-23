# Collector Agent Documentation

The Collector Agent is responsible for gathering Google Cloud Platform (GCP) configuration data for security analysis.

## Overview

The Collector Agent:

- Fetches IAM policies and Security Command Center findings
- Supports both mock data (for testing) and real GCP API calls
- Outputs structured JSON for downstream processing
- Implements retry logic and rate limiting

## Architecture

```
┌─────────────────┐
│   CLI/Main      │
└────────┬────────┘
         │
┌────────▼────────┐
│ Collector Agent │
├─────────────────┤
│ - IAM Collector │
│ - SCC Collector │
│ - Mock Provider │
└────────┬────────┘
         │
┌────────▼────────┐
│ collected.json  │
└─────────────────┘
```

## Usage

### Command Line Interface

```bash
# Basic usage
python python_agents/collector/agent_collector.py

# With specific project
python python_agents/collector/agent_collector.py --project_id=my-project

# Using mock data
python python_agents/collector/agent_collector.py --use_mock=True

# Specify output location
python python_agents/collector/agent_collector.py --output=./custom/collected.json

# Collect specific resource types
python python_agents/collector/agent_collector.py --resource_types=iam,scc
```

### Python API

```python
from collector.agent_collector import CollectorAgent, CollectorConfig

# Initialize with configuration
config = CollectorConfig(
    project_id="my-project",
    organization_id="123456789",
    use_mock=False,
    resource_types=["iam", "scc_findings"]
)

agent = CollectorAgent(config)

# Run collection
result = agent.collect()

# Access collected data
iam_policies = result.iam_policies
scc_findings = result.scc_findings
```

## Configuration

### Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `project_id` | string | Required | GCP project ID to audit |
| `organization_id` | string | Optional | Organization ID for org-level resources |
| `use_mock` | boolean | False | Use mock data instead of real APIs |
| `resource_types` | list | ["iam", "scc"] | Resource types to collect |
| `output_path` | string | "data/collected.json" | Output file location |
| `page_size` | integer | 100 | Results per API page |
| `max_retries` | integer | 3 | Maximum retry attempts |
| `timeout` | integer | 300 | Timeout in seconds |

### Environment Variables

```bash
# Google Cloud authentication
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# Override defaults
export PADDI_PROJECT_ID=my-project
export PADDI_USE_MOCK=true
```

## Collected Data Structure

### Output Format

```json
{
  "metadata": {
    "timestamp": "2024-01-15T10:30:00Z",
    "project_id": "my-project",
    "organization_id": "123456789",
    "collector_version": "1.0.0"
  },
  "iam_policies": [
    {
      "resource": "projects/my-project",
      "policy": {
        "bindings": [
          {
            "role": "roles/owner",
            "members": ["user:admin@example.com"]
          }
        ],
        "etag": "BwXg7...",
        "version": 1
      }
    }
  ],
  "scc_findings": [
    {
      "name": "organizations/123/findings/finding-id",
      "category": "PUBLIC_RESOURCE",
      "severity": "HIGH",
      "state": "ACTIVE",
      "resource_name": "//storage.googleapis.com/my-bucket",
      "finding_class": "VULNERABILITY"
    }
  ]
}
```

## Collectors

### IAM Collector

Collects IAM policies from:

- Project level
- Organization level (if configured)
- Resource level (future enhancement)

Features:

- Filters out Google-managed service accounts (configurable)
- Captures policy bindings, conditions, and audit configs
- Handles large policies with pagination

### Security Command Center Collector

Collects findings from Security Command Center:

- Active security findings
- Filtered by severity and state
- Includes vulnerability and misconfiguration findings

Features:

- Customizable finding filters
- Batch processing for large result sets
- Automatic retry on API errors

### Mock Data Provider

Provides realistic test data:

- Sample IAM policies with common misconfigurations
- Example SCC findings across severity levels
- Consistent data structure for testing

## Error Handling

### Retry Logic

```python
# Automatic retry with exponential backoff
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(min=1, max=10),
    retry=retry_if_exception_type(GoogleAPIError)
)
def collect_iam_policies(self):
    # Collection logic
```

### Error Types

| Error | Cause | Resolution |
|-------|-------|------------|
| `AuthenticationError` | Missing/invalid credentials | Set up authentication |
| `PermissionError` | Insufficient permissions | Grant required roles |
| `QuotaExceededError` | API quota exceeded | Implement rate limiting |
| `TimeoutError` | Operation timeout | Increase timeout setting |

## Performance Optimization

### Rate Limiting

```python
# Built-in rate limiting
rate_limiter = RateLimiter(
    requests_per_second=10,
    burst_size=20
)
```

### Batch Processing

```python
# Process in batches to reduce API calls
BATCH_SIZE = 50
for batch in chunks(resources, BATCH_SIZE):
    process_batch(batch)
```

### Caching

```python
# Cache frequently accessed data
@lru_cache(maxsize=128)
def get_project_iam_policy(project_id):
    # Fetch policy
```

## Extending the Collector

### Adding New Resource Types

1. Create a new collector class:

```python
class ComputeCollector(BaseCollector):
    def collect(self):
        # Implementation
        return compute_instances
```

2. Register in the main collector:

```python
COLLECTORS = {
    'iam': IAMCollector,
    'scc': SCCCollector,
    'compute': ComputeCollector,  # New collector
}
```

3. Update configuration schema:

```python
RESOURCE_TYPES = ['iam', 'scc', 'compute']
```

### Custom Filters

```python
# Add custom filtering logic
def custom_iam_filter(policy):
    # Filter out test accounts
    return not any('test' in member for binding in policy.bindings
                   for member in binding.members)

collector.add_filter('iam', custom_iam_filter)
```

## Testing

### Unit Tests

```bash
# Run collector tests
pytest python_agents/tests/test_collector.py

# With coverage
pytest --cov=collector python_agents/tests/test_collector.py
```

### Integration Tests

```python
# Test with mock data
def test_collector_mock():
    agent = CollectorAgent(use_mock=True)
    result = agent.collect()
    assert len(result.iam_policies) > 0
    assert len(result.scc_findings) > 0

# Test with real APIs (requires auth)
@pytest.mark.integration
def test_collector_real():
    agent = CollectorAgent(project_id="test-project")
    result = agent.collect()
    assert result.metadata.project_id == "test-project"
```

## Troubleshooting

### Common Issues

1. **Authentication Errors**

   ```bash
   # Verify authentication
   gcloud auth application-default print-access-token

   # Re-authenticate
   gcloud auth application-default login
   ```

2. **Permission Errors**

   ```bash
   # Check current permissions
   gcloud projects get-iam-policy PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:user:YOUR_EMAIL"

   # Grant required role
   gcloud projects add-iam-policy-binding PROJECT_ID \
     --member="user:YOUR_EMAIL" \
     --role="roles/iam.securityReviewer"
   ```

3. **API Not Enabled**

   ```bash
   # Enable required APIs
   gcloud services enable iam.googleapis.com
   gcloud services enable securitycenter.googleapis.com
   ```

### Debug Mode

```bash
# Enable debug logging
export PADDI_LOG_LEVEL=DEBUG
python python_agents/collector/agent_collector.py

# Or via command line
python python_agents/collector/agent_collector.py --log-level=DEBUG
```

## Best Practices

1. **Use Service Accounts**: For production, use dedicated service accounts with minimal permissions
2. **Implement Filtering**: Filter out noise early to reduce processing overhead
3. **Handle Pagination**: Always handle paginated responses properly
4. **Monitor Quotas**: Track API usage to avoid quota exhaustion
5. **Validate Output**: Verify collected data structure before passing to next agent

## API Reference

### CollectorAgent Class

```python
class CollectorAgent:
    def __init__(self, config: CollectorConfig):
        """Initialize collector with configuration."""

    def collect(self) -> CollectionResult:
        """Run collection and return results."""

    def collect_iam_policies(self) -> List[IAMPolicy]:
        """Collect IAM policies from configured resources."""

    def collect_scc_findings(self) -> List[SCCFinding]:
        """Collect Security Command Center findings."""

    def save_results(self, results: CollectionResult, output_path: str):
        """Save collection results to JSON file."""
```

### Data Models

```python
@dataclass
class IAMPolicy:
    resource: str
    policy: dict
    metadata: dict

@dataclass
class SCCFinding:
    name: str
    category: str
    severity: str
    state: str
    resource_name: str
    finding_class: str

@dataclass
class CollectionResult:
    metadata: dict
    iam_policies: List[IAMPolicy]
    scc_findings: List[SCCFinding]
```
