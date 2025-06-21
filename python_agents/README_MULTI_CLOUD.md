# Multi-Cloud Support for Paddi

This document describes the multi-cloud support added to Paddi, enabling security audits across Google Cloud Platform (GCP), Amazon Web Services (AWS), and Microsoft Azure.

## Overview

The multi-cloud support extends Paddi's capabilities to:
- Collect security configurations from GCP, AWS, and Azure
- Analyze findings using a unified security framework
- Generate comprehensive reports covering all cloud providers
- Maintain backward compatibility with existing GCP-only workflows

## Architecture

### Cloud Provider Abstraction

```
cloud_provider.py
├── CloudProvider (enum: GCP, AWS, AZURE)
├── CloudConfig (configuration dataclass)
├── CloudProviderInterface (abstract base)
├── IAMCollectorInterface (identity management)
├── SecurityCollectorInterface (security findings)
├── LogCollectorInterface (audit logs)
└── CloudCollectorFactory (provider instantiation)
```

### Provider Implementations

- **GCP Provider** (`gcp_provider.py`)
  - IAM policies and bindings
  - Security Command Center findings
  - Cloud Audit Logs
  
- **AWS Provider** (`aws_provider.py`)
  - IAM users, roles, and policies
  - Security Hub findings
  - CloudTrail logs
  
- **Azure Provider** (`azure_provider.py`)
  - Azure AD users and roles
  - Security Center alerts
  - Activity logs

## Usage

### Multi-Cloud Audit

```bash
# Using configuration file
python collector/agent_collector.py \
  --providers='config/multi_cloud_config.json' \
  --use_mock=false

# Using inline JSON
python collector/agent_collector.py \
  --providers='[
    {"provider": "gcp", "project_id": "my-project"},
    {"provider": "aws", "account_id": "123456789012"},
    {"provider": "azure", "subscription_id": "00000000-0000-0000-0000-000000000000"}
  ]'
```

### Single Cloud Audit

```bash
# AWS audit
python collector/agent_collector.py \
  --provider=aws \
  --account_id=123456789012 \
  --region=us-east-1

# Azure audit  
python collector/agent_collector.py \
  --provider=azure \
  --subscription_id=00000000-0000-0000-0000-000000000000

# GCP audit (legacy compatible)
python collector/agent_collector.py \
  --project_id=my-gcp-project
```

### Complete Workflow

```python
# See run_multi_cloud_example.py for a complete example

# 1. Collect configurations
python collector/agent_collector.py --providers='[...]'

# 2. Analyze with Gemini
python explainer/agent_explainer.py

# 3. Generate reports
python reporter/agent_reporter.py
```

## Configuration

### Authentication

Each cloud provider requires appropriate credentials:

**GCP:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
# OR use application default credentials
gcloud auth application-default login
```

**AWS:**
```bash
export AWS_ACCESS_KEY_ID=your-access-key
export AWS_SECRET_ACCESS_KEY=your-secret-key
# OR use AWS profile
export AWS_PROFILE=your-profile
```

**Azure:**
```bash
export AZURE_CLIENT_ID=your-client-id
export AZURE_CLIENT_SECRET=your-client-secret
export AZURE_TENANT_ID=your-tenant-id
# OR use Azure CLI
az login
```

### Configuration File Format

```json
[
  {
    "provider": "gcp",
    "project_id": "my-gcp-project",
    "region": "us-central1",
    "credentials_path": "~/.config/gcloud/application_default_credentials.json"
  },
  {
    "provider": "aws",
    "account_id": "123456789012", 
    "region": "us-east-1",
    "credentials_path": "~/.aws/credentials"
  },
  {
    "provider": "azure",
    "subscription_id": "00000000-0000-0000-0000-000000000000",
    "region": "eastus",
    "credentials_path": "~/.azure/credentials"
  }
]
```

## Output Format

### Collected Data Structure

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "providers": {
    "gcp": {
      "iam": {...},
      "security": {...},
      "logs": {...}
    },
    "aws": {
      "iam": {...},
      "security": {...},
      "logs": {...}
    },
    "azure": {
      "iam": {...},
      "security": {...},
      "logs": {...}
    }
  },
  "summary": {
    "total_users": 25,
    "total_roles": 15,
    "total_findings": 42,
    "high_severity_findings": 12,
    "providers_analyzed": ["gcp", "aws", "azure"]
  }
}
```

### Security Findings Format

```json
[
  {
    "title": "AWS: Administrator Access Policy on User Account",
    "severity": "HIGH",
    "explanation": "IAM user has AdministratorAccess policy attached",
    "recommendation": "Apply least privilege principle",
    "provider": "aws",
    "resource": "arn:aws:iam::123456789012:user/admin"
  }
]
```

## Backward Compatibility

The implementation maintains full backward compatibility:

1. **Legacy GCP Commands**: Original GCP-only commands still work
2. **Data Format**: Legacy format is detected and handled automatically
3. **Report Generation**: Reports adapt to single or multi-cloud data

## Security Considerations

- **Credentials**: Never commit cloud credentials to version control
- **Permissions**: Use least-privilege service accounts/roles
- **Mock Mode**: Use `--use_mock=true` for testing without real credentials
- **Data Sensitivity**: Audit reports may contain sensitive information

## Testing

Run tests with mock data:

```bash
# Run all tests
pytest tests/

# Run specific test suites
pytest tests/test_multi_cloud_collector.py
pytest tests/test_cloud_providers.py
pytest tests/test_multi_cloud_explainer.py
pytest tests/test_multi_cloud_reporter.py
```

## Dependencies

New dependencies for multi-cloud support:

```
# AWS
boto3>=1.26.0
botocore>=1.29.0

# Azure
azure-identity>=1.14.0
azure-mgmt-resource>=23.0.0
azure-mgmt-authorization>=4.0.0
azure-mgmt-security>=5.0.0
azure-mgmt-monitor>=6.0.0
```

Install all dependencies:
```bash
pip install -r requirements.txt
```