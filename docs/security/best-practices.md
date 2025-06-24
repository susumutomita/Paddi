# Security Best Practices

This guide outlines security best practices for using Paddi and protecting your Google Cloud Platform infrastructure.

## Paddi Security Configuration

### Authentication and Authorization

#### Service Account Setup

Create a dedicated service account with minimal permissions:

```bash
# Create service account
gcloud iam service-accounts create paddi-auditor \
    --display-name="Paddi Security Auditor" \
    --description="Service account for Paddi security audits"

# Grant minimal required roles
PROJECT_ID="your-project-id"
SA_EMAIL="paddi-auditor@${PROJECT_ID}.iam.gserviceaccount.com"

# Read-only roles for auditing
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.securityReviewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/securitycenter.findings.viewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/aiplatform.user"

# Create and download key
gcloud iam service-accounts keys create paddi-sa-key.json \
    --iam-account=${SA_EMAIL}
```

#### Key Management

```bash
# Encrypt service account key
openssl enc -aes-256-cbc -salt -in paddi-sa-key.json -out paddi-sa-key.json.enc

# Store encrypted key in secure location
# Use environment variable for decryption password
export PADDI_KEY_PASSWORD="your-secure-password"

# Decrypt when needed
openssl enc -d -aes-256-cbc -in paddi-sa-key.json.enc -out paddi-sa-key.json
```

### Secure Configuration

#### Environment Variables

```bash
# Use environment variables for sensitive data
export GOOGLE_APPLICATION_CREDENTIALS="/secure/path/paddi-sa-key.json"
export PADDI_PROJECT_ID="your-project-id"
export VERTEX_AI_API_KEY="your-api-key"  # If using API key

# Never commit .env files
echo ".env" >> .gitignore
```

#### Configuration File Security

```toml
# paddi.toml - Safe to commit
[general]
use_mock = false
log_level = "INFO"

[paths]
# Use environment variables for sensitive paths
credentials_path = "${GOOGLE_APPLICATION_CREDENTIALS}"

[security]
# Security settings
encrypt_reports = true
redact_sensitive_data = true
```

### Network Security

#### API Endpoint Security

```python
# Use private Vertex AI endpoints when available
from google.cloud import aiplatform

aiplatform.init(
    project=project_id,
    location=region,
    encryption_spec_key_name=cmek_key,  # Customer-managed encryption
)
```

#### Firewall Rules

```bash
# Restrict outbound traffic to required endpoints only
ALLOWED_ENDPOINTS=(
    "aiplatform.googleapis.com"
    "iam.googleapis.com"
    "securitycenter.googleapis.com"
)

# Configure firewall rules accordingly
```

## GCP Security Best Practices

### IAM Best Practices

#### Principle of Least Privilege

```python
# Bad - Overly permissive
{
    "bindings": [{
        "role": "roles/owner",
        "members": ["user:developer@example.com"]
    }]
}

# Good - Specific roles
{
    "bindings": [
        {
            "role": "roles/compute.viewer",
            "members": ["user:developer@example.com"]
        },
        {
            "role": "roles/logging.viewer",
            "members": ["user:developer@example.com"]
        }
    ]
}
```

#### Use Groups for Access Management

```python
# Bad - Individual user bindings
{
    "bindings": [{
        "role": "roles/editor",
        "members": [
            "user:alice@example.com",
            "user:bob@example.com",
            "user:charlie@example.com"
        ]
    }]
}

# Good - Group-based access
{
    "bindings": [{
        "role": "roles/editor",
        "members": ["group:dev-team@example.com"]
    }]
}
```

#### Implement IAM Conditions

```python
# Time-based access
{
    "bindings": [{
        "role": "roles/compute.admin",
        "members": ["user:oncall@example.com"],
        "condition": {
            "title": "Business hours only",
            "expression": 'request.time.getHours("America/Los_Angeles") >= 9 && request.time.getHours("America/Los_Angeles") <= 17'
        }
    }]
}

# Resource-based conditions
{
    "bindings": [{
        "role": "roles/storage.objectAdmin",
        "members": ["serviceAccount:app@project.iam.gserviceaccount.com"],
        "condition": {
            "title": "Specific bucket only",
            "expression": 'resource.name.startsWith("projects/_/buckets/app-data")'
        }
    }]
}
```

### Service Account Security

#### Key Rotation

```bash
#!/bin/bash
# rotate-sa-keys.sh

SA_EMAIL="paddi-auditor@project.iam.gserviceaccount.com"

# List existing keys
OLD_KEYS=$(gcloud iam service-accounts keys list \
    --iam-account=${SA_EMAIL} \
    --format="value(name)" \
    --filter="keyType=USER_MANAGED")

# Create new key
gcloud iam service-accounts keys create new-key.json \
    --iam-account=${SA_EMAIL}

# Update application to use new key
# ... deployment steps ...

# Delete old keys after verification
for KEY in ${OLD_KEYS}; do
    gcloud iam service-accounts keys delete ${KEY} \
        --iam-account=${SA_EMAIL} --quiet
done
```

#### Workload Identity

```yaml
# For GKE workloads - use Workload Identity
apiVersion: v1
kind: ServiceAccount
metadata:
  name: paddi-sa
  annotations:
    iam.gke.io/gcp-service-account: paddi-auditor@project.iam.gserviceaccount.com
```

### Data Protection

#### Encryption at Rest

```python
# Ensure all storage uses encryption
def create_secure_bucket(bucket_name: str, cmek_key: str):
    """Create bucket with customer-managed encryption."""
    storage_client = storage.Client()

    bucket = storage_client.bucket(bucket_name)
    bucket.encryption_key = cmek_key
    bucket.location = "us-central1"
    bucket.storage_class = "STANDARD"

    # Enable uniform bucket-level access
    bucket.iam_configuration.uniform_bucket_level_access_enabled = True

    bucket.create()
```

#### Data Residency

```toml
# Configure data residency in paddi.toml
[security]
allowed_regions = ["us-central1", "us-east1"]
data_residency_check = true
```

### Network Security

#### VPC Service Controls

```python
# Configure VPC Service Controls
def setup_vpc_perimeter():
    """Set up VPC Service Perimeter for Paddi."""
    # Define perimeter
    perimeter = {
        "name": "paddi-security-perimeter",
        "resources": [
            f"projects/{project_id}"
        ],
        "restricted_services": [
            "aiplatform.googleapis.com",
            "storage.googleapis.com"
        ],
        "access_levels": ["paddi_access_level"]
    }
```

#### Private Google Access

```bash
# Enable Private Google Access
gcloud compute networks subnets update ${SUBNET_NAME} \
    --region=${REGION} \
    --enable-private-ip-google-access
```

## Paddi-Specific Security Findings

### Critical Severity Issues

These require immediate attention:

1. **Public Data Exposure**

   ```python
   # Finding: Storage bucket with public access
   {
       "title": "Public Storage Bucket",
       "severity": "CRITICAL",
       "remediation": "Remove allUsers and allAuthenticatedUsers bindings"
   }
   ```

2. **Overly Permissive IAM**

   ```python
   # Finding: User with Owner role
   {
       "title": "Owner Role Assignment",
       "severity": "CRITICAL",
       "remediation": "Replace with specific predefined roles"
   }
   ```

3. **Unencrypted Data**

   ```python
   # Finding: Storage without encryption
   {
       "title": "Unencrypted Storage",
       "severity": "CRITICAL",
       "remediation": "Enable default encryption with CMEK"
   }
   ```

### Remediation Priorities

```python
# Priority matrix for remediation
REMEDIATION_PRIORITY = {
    "CRITICAL": {
        "timeline": "Immediate (within 24 hours)",
        "approval": "Not required",
        "notification": "Security team + Management"
    },
    "HIGH": {
        "timeline": "Within 7 days",
        "approval": "Team lead",
        "notification": "Security team"
    },
    "MEDIUM": {
        "timeline": "Within 30 days",
        "approval": "Not required",
        "notification": "Team"
    },
    "LOW": {
        "timeline": "Next quarter",
        "approval": "Not required",
        "notification": "None"
    }
}
```

## Compliance Frameworks

### CIS Google Cloud Platform Benchmark

Key controls audited by Paddi:

```python
CIS_CONTROLS = {
    "1.1": "Ensure that corporate login credentials are used",
    "1.2": "Ensure that multi-factor authentication is enabled",
    "1.3": "Ensure that Security Key Enforcement is enabled",
    "1.4": "Ensure that there are only GCP-managed service account keys",
    "1.5": "Ensure that Service Account has no Admin privileges",
    "1.6": "Ensure that IAM users are not assigned Service Account User role",
    "1.7": "Ensure user-managed/external keys for service accounts are rotated",
    "1.8": "Ensure that Separation of duties is enforced while assigning service account roles",
    "1.9": "Ensure that Cloud KMS cryptokeys are not anonymously or publicly accessible"
}
```

### PCI-DSS Compliance

Security controls for payment card data:

```python
PCI_DSS_CHECKS = {
    "access_control": [
        "Implement strong access control measures",
        "Restrict access to cardholder data by business need-to-know",
        "Assign a unique ID to each person with computer access"
    ],
    "encryption": [
        "Encrypt transmission of cardholder data",
        "Use strong cryptography and security protocols"
    ],
    "monitoring": [
        "Track and monitor all access to network resources",
        "Regularly test security systems and processes"
    ]
}
```

### HIPAA Compliance

For healthcare data protection:

```python
HIPAA_REQUIREMENTS = {
    "access_controls": {
        "unique_user_identification": True,
        "automatic_logoff": True,
        "encryption_decryption": True
    },
    "audit_controls": {
        "logging_enabled": True,
        "log_retention_days": 365,
        "log_analysis": True
    },
    "integrity_controls": {
        "data_backup": True,
        "data_validation": True
    }
}
```

## Security Monitoring

### Continuous Auditing

```bash
# Schedule regular audits
# /etc/cron.d/paddi-audit
0 */4 * * * paddi-user /usr/local/bin/paddi audit --fail-on-critical >> /var/log/paddi/audit.log 2>&1
```

### Alert Configuration

```python
# alert_config.py
ALERT_RULES = [
    {
        "name": "Critical Finding Alert",
        "condition": "severity == 'CRITICAL'",
        "actions": ["email", "slack", "pagerduty"],
        "cooldown_minutes": 60
    },
    {
        "name": "Multiple High Findings",
        "condition": "count(severity='HIGH') >= 5",
        "actions": ["email", "slack"],
        "cooldown_minutes": 240
    }
]
```

### Integration with SIEM

```python
# Send findings to SIEM
def send_to_siem(finding):
    siem_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "source": "paddi",
        "severity": finding["severity"],
        "category": "security.audit",
        "message": finding["title"],
        "details": {
            "resource": finding["resource"],
            "explanation": finding["explanation"],
            "recommendation": finding["recommendation"]
        }
    }

    # Send to Splunk/ELK/etc
    siem_client.send_event(siem_event)
```

## Incident Response

### Response Playbook

```python
# incident_response.py
RESPONSE_PLAYBOOK = {
    "CRITICAL": {
        "steps": [
            "Isolate affected resource",
            "Revoke compromised credentials",
            "Enable additional logging",
            "Notify security team",
            "Begin forensic analysis"
        ],
        "contacts": ["security@example.com", "on-call@example.com"],
        "escalation_time": "15 minutes"
    }
}
```

### Automated Remediation

```python
# auto_remediate.py
def auto_remediate(finding):
    """Automatically remediate certain findings."""
    if finding["auto_remediation_allowed"]:
        if finding["type"] == "public_bucket":
            remove_public_access(finding["resource"])
        elif finding["type"] == "old_sa_key":
            rotate_service_account_key(finding["resource"])

        log_remediation(finding)
```

## Security Checklist

Before running Paddi in production:

- [ ] Service account created with minimal permissions
- [ ] Credentials encrypted and stored securely
- [ ] Network restrictions configured
- [ ] Audit logging enabled
- [ ] Alert rules configured
- [ ] Incident response plan documented
- [ ] Regular audit schedule established
- [ ] Report encryption enabled
- [ ] Access controls reviewed
- [ ] Compliance requirements mapped

## Additional Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [CIS Google Cloud Platform Benchmark](https://www.cisecurity.org/benchmark/google_cloud_computing_platform)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [OWASP Cloud Security](https://owasp.org/www-project-cloud-security/)

## Questions?

For security-related questions:

- Review the [Security FAQ](https://github.com/susumutomita/Paddi/wiki/Security-FAQ)
- Contact the security team
- Report security issues privately via [security@paddi.dev](mailto:security@paddi.dev)
