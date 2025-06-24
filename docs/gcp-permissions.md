# Required GCP Permissions

To use Paddi with real Google Cloud API integration, you need to ensure the service account or user running Paddi has the following permissions:

## Required Roles

The simplest approach is to grant these predefined roles:

1. **Security Reviewer** (`roles/iam.securityReviewer`)
   - Allows viewing IAM policies and security configurations
   - Required for IAM policy collection

2. **Security Center Findings Viewer** (`roles/securitycenter.findingsViewer`)
   - Allows viewing Security Command Center findings
   - Required for security findings collection

3. **Logs Viewer** (`roles/logging.viewer`)
   - Allows viewing Cloud Audit Logs
   - Required for audit log collection

## Specific Permissions

If you prefer to create a custom role with minimal permissions, include these:

### IAM Permissions
- `resourcemanager.projects.getIamPolicy`
- `iam.serviceAccounts.list`
- `iam.serviceAccounts.getIamPolicy`

### Security Command Center Permissions
- `securitycenter.findings.list`
- `securitycenter.findings.get`
- `securitycenter.sources.list`

### Logging Permissions
- `logging.logEntries.list`
- `logging.logs.list`

## Authentication Setup

Paddi uses Application Default Credentials (ADC). Set up authentication using one of these methods:

1. **Local Development**: Run `gcloud auth application-default login`
2. **Service Account**: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account key file
3. **GCE/GKE/Cloud Run**: Uses the default service account automatically

## Example: Creating a Service Account

```bash
# Create service account
gcloud iam service-accounts create paddi-auditor \
    --description="Service account for Paddi security audits" \
    --display-name="Paddi Auditor"

# Grant required roles
PROJECT_ID=$(gcloud config get-value project)
SA_EMAIL="paddi-auditor@${PROJECT_ID}.iam.gserviceaccount.com"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/iam.securityReviewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/securitycenter.findingsViewer"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SA_EMAIL}" \
    --role="roles/logging.viewer"

# Create and download key
gcloud iam service-accounts keys create paddi-key.json \
    --iam-account=${SA_EMAIL}

# Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="paddi-key.json"
```

## Security Command Center Setup

Note: Security Command Center requires organization-level setup. If you're testing with a personal project, the findings API might return empty results. In this case, Paddi will gracefully fall back to mock data.

For production use:
1. Enable Security Command Center API in your organization
2. Ensure the service account has organization-level permissions for SCC
3. Configure the organization ID in Paddi if needed