#!/bin/bash
# Deploy to Cloud Run

# Set variables
# Use project ID from environment or default to hackathon project
PROJECT_ID=${GOOGLE_CLOUD_PROJECT:-"paddi-hackathon-2025"}
SERVICE_NAME="paddi"
REGION="asia-northeast1"  # Tokyo region

echo "🚀 Deploying Paddi to Cloud Run..."
echo "Project ID: ${PROJECT_ID}"
echo "Service Name: ${SERVICE_NAME}"
echo "Region: ${REGION}"

# Confirm with user
read -p "Continue with deployment? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 1
fi

IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Check if authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Not authenticated with gcloud. Please run 'gcloud auth login'"
    exit 1
fi

# Set project
echo "Setting project to ${PROJECT_ID}..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "Enabling required APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable aiplatform.googleapis.com
gcloud services enable iam.googleapis.com
gcloud services enable securitycenter.googleapis.com

# Build container
echo "Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}

# Deploy to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
  --image ${IMAGE_NAME} \
  --platform managed \
  --region ${REGION} \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 100 \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
  --set-env-vars="USE_MOCK_DATA=true" \
  --set-env-vars="DEMO_MODE=true" \
  --set-env-vars="LOG_LEVEL=INFO" \
  --set-env-vars="PORT=8080"

# Get service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "Service URL: ${SERVICE_URL}"
echo ""
echo "You can now access:"
echo "- Web Dashboard: ${SERVICE_URL}"
echo "- Health Check: ${SERVICE_URL}/api/health"
echo "- API Endpoint: ${SERVICE_URL}/api/audit"
echo ""
echo "📝 Next steps:"
echo "1. Update README.md with the actual demo URL:"
echo "   Replace: https://paddi-[YOUR-PROJECT-ID]-an.a.run.app"
echo "   With:    ${SERVICE_URL}"
echo ""
echo "2. Test the deployment:"
echo "   curl ${SERVICE_URL}/api/health"
echo ""
echo "3. The service will remain deployed from June 30 - July 16, 2025 for the hackathon."
echo ""
echo "To update the deployment, run this script again."