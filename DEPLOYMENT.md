# Cloud Run Deployment Guide

This guide provides detailed instructions for deploying Paddi to Google Cloud Run.

## Prerequisites

1. **Google Cloud Account**: Create an account at https://cloud.google.com
2. **gcloud CLI**: Install from https://cloud.google.com/sdk/docs/install
3. **Billing Account**: Enable billing for your GCP project
4. **Docker**: Required for local testing (optional)

## Deployment Options

### Option 1: Using deploy.sh (Recommended)

The simplest way to deploy is using the provided deployment script:

```bash
# Set your project ID (optional, defaults to paddi-hackathon-2025)
export GOOGLE_CLOUD_PROJECT=your-project-id

# Run the deployment script
./deploy.sh
```

The script will:
- Check prerequisites
- Enable required APIs
- Build the container image
- Deploy to Cloud Run
- Display the service URL

### Option 2: Using Cloud Build

For CI/CD integration, use Cloud Build:

```bash
# Submit build directly
gcloud builds submit --config cloudbuild.yaml
```

### Option 3: Manual Deployment

```bash
# 1. Build and push the image
gcloud builds submit --tag gcr.io/${PROJECT_ID}/paddi

# 2. Deploy to Cloud Run
gcloud run deploy paddi \
  --image gcr.io/${PROJECT_ID}/paddi \
  --platform managed \
  --region asia-northeast1 \
  --allow-unauthenticated \
  --min-instances 0 \
  --memory 1Gi
```

## Configuration

### Environment Variables

The following environment variables are set during deployment:

- `GOOGLE_CLOUD_PROJECT`: GCP project ID
- `USE_MOCK_DATA`: Set to `true` for demo mode
- `DEMO_MODE`: Enables demo features
- `LOG_LEVEL`: Logging level (INFO by default)
- `PORT`: Server port (8080)

### Resource Limits

- **Memory**: 1 GiB
- **CPU**: 1 vCPU
- **Timeout**: 300 seconds
- **Min Instances**: 0 (to save costs)
- **Max Instances**: 100

## Verification

After deployment, verify the service is running:

```bash
# Get the service URL
SERVICE_URL=$(gcloud run services describe paddi --region asia-northeast1 --format 'value(status.url)')

# Test health endpoint
curl ${SERVICE_URL}/api/health

# Expected response:
# {"status": "healthy", "timestamp": "2024-01-01T00:00:00"}
```

## Cost Optimization

To minimize costs during the hackathon:

1. **Min Instances = 0**: Service scales to zero when not in use
2. **Region**: Using asia-northeast1 (Tokyo) for lower latency in Japan
3. **Resource Limits**: Conservative memory/CPU allocation

## Troubleshooting

### Common Issues

1. **API not enabled**
   ```bash
   gcloud services enable run.googleapis.com containerregistry.googleapis.com
   ```

2. **Authentication errors**
   ```bash
   gcloud auth login
   gcloud config set project ${PROJECT_ID}
   ```

3. **Build failures**
   - Check Docker file syntax
   - Ensure all dependencies are in requirements.txt
   - Review Cloud Build logs

### Viewing Logs

```bash
# View Cloud Run logs
gcloud run services logs read paddi --region asia-northeast1

# Stream logs in real-time
gcloud run services logs tail paddi --region asia-northeast1
```

## Updating the Service

To update the deployed service:

1. Make your code changes
2. Run `./deploy.sh` again
3. The script will rebuild and redeploy automatically

## Hackathon Requirements

For the AI Agent Hackathon with Google Cloud:

- ✅ Using Cloud Run (Compute product requirement)
- ✅ Service must be accessible June 30 - July 16, 2025
- ✅ Demo URL must be provided in README
- ✅ Using Vertex AI for AI capabilities

## Security Notes

- The demo deployment uses mock data only
- No real GCP credentials are exposed
- Service is publicly accessible (required for demo)
- All sensitive operations are disabled in demo mode