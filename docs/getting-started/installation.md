# Installation Guide

This guide will help you install and set up Paddi on your system.

## Prerequisites

Before installing Paddi, ensure you have the following:

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.10 or higher
- **Git**: For cloning the repository

### Google Cloud Requirements

- Google Cloud Project with billing enabled
- Appropriate IAM permissions:
  - `roles/iam.securityReviewer` (for reading IAM policies)
  - `roles/securitycenter.findings.viewer` (for Security Command Center)
  - `roles/aiplatform.user` (for Vertex AI/Gemini)

## Installation Methods

### Method 1: Standard Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/susumutomita/Paddi.git
   cd Paddi
   ```

2. **Create a virtual environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

4. **Verify installation:**

   ```bash
   python main.py init
   ```

## Google Cloud Setup

### 1. Authentication

Set up Google Cloud authentication:

```bash
# Install gcloud CLI if not already installed
# See: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login
```

### 2. Enable Required APIs

Enable the necessary Google Cloud APIs:

```bash
gcloud services enable iam.googleapis.com
gcloud services enable securitycenter.googleapis.com
gcloud services enable aiplatform.googleapis.com
```

### 3. Set Default Project

```bash
gcloud config set project YOUR_PROJECT_ID
```

## Configuration

Paddi can be configured through command-line arguments or environment variables:

```bash
# Set default project
export GCP_PROJECT_ID="your-project-id"

# Or pass as argument
python main.py audit --project-id="your-project-id"
```

## Verify Installation

### Test with Mock Data

```bash
# Run with mock data (no GCP access required)
python main.py audit --use-mock
```

### Test with Real GCP Data

```bash
# Ensure you're authenticated first
python main.py audit --project-id=YOUR_PROJECT_ID
```

## Troubleshooting

### Common Issues

1. **Python Import Errors**
   - Ensure you're in the virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

2. **Google Cloud Authentication Errors**
   - Re-authenticate: `gcloud auth application-default login`
   - Check project permissions

3. **Vertex AI Region Issues**
   - Set the region in configuration or environment:

   ```bash
   export VERTEX_AI_REGION=us-central1
   ```

## Next Steps

- Read the [Quick Start Guide](quick-start.md) to run your first audit
- Check the [Configuration Guide](configuration.md) for advanced settings
- See [Examples](../examples/basic-audit.md) for common use cases
