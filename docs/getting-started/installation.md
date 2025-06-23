# Installation Guide

This guide will help you install and set up Paddi on your system.

## Prerequisites

Before installing Paddi, ensure you have the following:

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Rust**: 1.70 or higher (for CLI installation)
- **Git**: For cloning the repository

### Google Cloud Requirements

- Google Cloud Project with billing enabled
- Appropriate IAM permissions:
  - `roles/iam.securityReviewer` (for reading IAM policies)
  - `roles/securitycenter.findings.viewer` (for Security Command Center)
  - `roles/aiplatform.user` (for Vertex AI/Gemini)

## Installation Methods

### Method 1: Using the Rust CLI (Recommended)

1. **Clone the repository:**

   ```bash
   git clone https://github.com/susumutomita/Paddi.git
   cd Paddi
   ```

2. **Install the Rust CLI:**

   ```bash
   cd cli
   make install
   ```

   This will:
   - Build the Rust binary
   - Install it to `~/.local/bin/paddi`
   - Set up shell completions

3. **Verify installation:**

   ```bash
   paddi --version
   ```

### Method 2: Python-only Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/susumutomita/Paddi.git
   cd Paddi/python_agents
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
   python run_example.py --use_mock=True
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

Create a configuration file:

```bash
cp cli/paddi.example.toml paddi.toml
```

Edit `paddi.toml` with your settings:

```toml
[general]
project_id = "your-project-id"
organization_id = "your-org-id"  # Optional

[paths]
python_interpreter = "python3"
agents_dir = "./python_agents"

[execution]
timeout_seconds = 300
use_mock = false  # Set to true for testing without GCP access
```

## Verify Installation

### Test with Mock Data

```bash
# Using CLI
paddi audit --use-mock

# Using Python directly
cd python_agents
python run_example.py --use_mock=True
```

### Test with Real GCP Data

```bash
# Ensure you're authenticated first
paddi audit --project-id=YOUR_PROJECT_ID
```

## Troubleshooting

### Common Issues

1. **Permission Denied (Rust CLI)**

   ```bash
   chmod +x ~/.local/bin/paddi
   export PATH="$HOME/.local/bin:$PATH"
   ```

2. **Python Import Errors**
   - Ensure you're in the virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Google Cloud Authentication Errors**
   - Re-authenticate: `gcloud auth application-default login`
   - Check project permissions

4. **Vertex AI Region Issues**
   - Set the region in configuration or environment:

   ```bash
   export VERTEX_AI_REGION=us-central1
   ```

## Next Steps

- Read the [Quick Start Guide](quick-start.md) to run your first audit
- Check the [Configuration Guide](configuration.md) for advanced settings
- See [Examples](../examples/basic-audit.md) for common use cases
