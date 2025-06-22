#!/bin/bash

# Paddi Dashboard Cloud Run Deployment Script

set -e

# Configuration
PROJECT_ID="${PROJECT_ID:-your-gcp-project-id}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="paddi-dashboard"
IMAGE_NAME="gcr.io/${PROJECT_ID}/${SERVICE_NAME}"

echo "🚀 Deploying Paddi Dashboard to Cloud Run"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI is not installed. Please install it first."
    exit 1
fi

# Authenticate and set project
echo "📋 Setting up GCP project..."
gcloud config set project ${PROJECT_ID}

# Enable required APIs
echo "🔧 Enabling required APIs..."
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable aiplatform.googleapis.com

# Create service account if it doesn't exist
echo "👤 Setting up service account..."
SERVICE_ACCOUNT="paddi-dashboard-sa"
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" &> /dev/null; then
    gcloud iam service-accounts create ${SERVICE_ACCOUNT} \
        --display-name="Paddi Dashboard Service Account"
fi

# Grant necessary permissions
echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
    --member="serviceAccount:${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Create secrets if they don't exist
echo "🔑 Setting up secrets..."
if ! gcloud secrets describe gemini-api-key &> /dev/null; then
    echo "Please enter your Gemini API key:"
    read -s GEMINI_API_KEY
    echo ${GEMINI_API_KEY} | gcloud secrets create gemini-api-key --data-file=-
fi

if ! gcloud secrets describe flask-secret-key &> /dev/null; then
    # Generate a random secret key
    FLASK_SECRET=$(openssl rand -hex 32)
    echo ${FLASK_SECRET} | gcloud secrets create flask-secret-key --data-file=-
fi

# Build the container
echo "🏗️ Building container image..."
gcloud builds submit --tag ${IMAGE_NAME}:latest .

# Deploy to Cloud Run
echo "☁️ Deploying to Cloud Run..."
gcloud run deploy ${SERVICE_NAME} \
    --image ${IMAGE_NAME}:latest \
    --platform managed \
    --region ${REGION} \
    --service-account "${SERVICE_ACCOUNT}@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 1 \
    --max-instances 10 \
    --set-env-vars "GOOGLE_CLOUD_PROJECT=${PROJECT_ID}" \
    --set-secrets "GEMINI_API_KEY=gemini-api-key:latest,SECRET_KEY=flask-secret-key:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe ${SERVICE_NAME} --region ${REGION} --format 'value(status.url)')

echo "✅ Deployment complete!"
echo "🌐 Dashboard URL: ${SERVICE_URL}"
echo ""
echo "Next steps:"
echo "1. Visit ${SERVICE_URL} to access the dashboard"
echo "2. Configure authentication (OAuth) for production use"
echo "3. Set up monitoring and alerting"
echo "4. Configure custom domain if needed"