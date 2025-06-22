use anyhow::{Context, Result};
use clap::Args;
use std::fs;
use std::path::Path;
use tracing::{info, warn};

use crate::config::Config;
use crate::orchestrator::AgentOrchestrator;

#[derive(Args)]
pub struct InitArgs {
    #[arg(
        short,
        long,
        help = "Output directory for generated files",
        default_value = "output"
    )]
    output: String,

    #[arg(long, help = "Skip running the full pipeline after initialization")]
    skip_run: bool,
}

pub async fn run(args: InitArgs, mut config: Config) -> Result<()> {
    info!("🚀 Initializing Paddi with sample data...");

    // Create necessary directories
    create_directories(&args.output)?;

    // Copy sample data to the data directory
    setup_sample_data()?;

    // Update config to use the sample data
    config.gcp.use_mock = true;

    if !args.skip_run {
        info!("🔄 Running full audit pipeline with sample data...");

        // Create orchestrator and run the full pipeline
        let orchestrator = AgentOrchestrator::new(config);

        // Run collector
        info!("📊 Collecting sample GCP configuration data...");
        orchestrator
            .run_collector(Some(true), None)
            .await
            .context("Failed to run collector")?;

        // Run explainer
        info!("🧠 Analyzing security risks with AI...");
        orchestrator
            .run_explainer(Some(true), None)
            .await
            .context("Failed to run explainer")?;

        // Run reporter with both markdown and html formats
        info!("📝 Generating audit reports...");
        let formats = vec![
            "markdown".to_string(),
            "html".to_string(),
            "honkit".to_string(),
        ];
        orchestrator
            .run_reporter(None, None, Some(formats))
            .await
            .context("Failed to run reporter")?;

        // Print success message with file locations
        println!("\n✅ Paddi init 完了:");
        println!("  • Markdown: {}/audit.md", args.output);
        println!("  • HTML: {}/audit.html（ブラウザで開けます）", args.output);

        // Check if honkit is available and provide guidance
        if which::which("honkit").is_ok() || which::which("npx").is_ok() {
            println!("  • サイトプレビュー: npx honkit serve docs/");
        } else {
            println!("  • サイトプレビュー: npm install -g honkit && honkit serve docs/");
        }
    } else {
        info!("✅ Initialization complete. Sample data is ready in data/collected.json");
        info!("Run 'paddi audit' to execute the full pipeline.");
    }

    Ok(())
}

fn create_directories(output_dir: &str) -> Result<()> {
    let dirs = vec!["data", output_dir, "docs"];

    for dir in dirs {
        fs::create_dir_all(dir).with_context(|| format!("Failed to create directory: {}", dir))?;
        info!("📁 Created directory: {}", dir);
    }

    Ok(())
}

fn setup_sample_data() -> Result<()> {
    let sample_file = "examples/gcp_sample.json";
    let target_file = "data/collected.json";

    // Check if sample file exists
    if !Path::new(sample_file).exists() {
        // If not, create it with embedded sample data
        create_sample_file(sample_file)?;
    }

    // Copy sample data to data directory
    fs::copy(sample_file, target_file)
        .with_context(|| format!("Failed to copy {} to {}", sample_file, target_file))?;

    info!("📋 Sample GCP configuration data copied to {}", target_file);

    Ok(())
}

fn create_sample_file(path: &str) -> Result<()> {
    // Create examples directory if it doesn't exist
    if let Some(parent) = Path::new(path).parent() {
        fs::create_dir_all(parent)?;
    }

    // Embedded sample data
    let sample_data = r#"{
  "iam_policies": [
    {
      "resource": "projects/example-project-123",
      "bindings": [
        {
          "role": "roles/owner",
          "members": [
            "user:admin@example.com",
            "serviceAccount:test-sa@example-project-123.iam.gserviceaccount.com"
          ]
        },
        {
          "role": "roles/editor",
          "members": [
            "user:developer@example.com",
            "group:dev-team@example.com"
          ]
        },
        {
          "role": "roles/viewer",
          "members": [
            "allUsers"
          ]
        },
        {
          "role": "roles/storage.admin",
          "members": [
            "user:storage-admin@example.com",
            "serviceAccount:storage-sa@example-project-123.iam.gserviceaccount.com"
          ]
        }
      ]
    },
    {
      "resource": "buckets/sensitive-data-bucket",
      "bindings": [
        {
          "role": "roles/storage.objectViewer",
          "members": [
            "allAuthenticatedUsers"
          ]
        }
      ]
    }
  ],
  "scc_findings": [
    {
      "name": "organizations/123456789/sources/1234567890/findings/finding-1",
      "category": "PUBLIC_BUCKET_ACL",
      "resourceName": "//storage.googleapis.com/sensitive-data-bucket",
      "state": "ACTIVE",
      "severity": "CRITICAL",
      "finding": {
        "description": "Bucket has public access enabled",
        "recommendation": "Remove allUsers and allAuthenticatedUsers from bucket IAM policy"
      }
    },
    {
      "name": "organizations/123456789/sources/1234567890/findings/finding-2",
      "category": "OVER_PRIVILEGED_SERVICE_ACCOUNT",
      "resourceName": "//iam.googleapis.com/projects/example-project-123/serviceAccounts/test-sa@example-project-123.iam.gserviceaccount.com",
      "state": "ACTIVE",
      "severity": "HIGH",
      "finding": {
        "description": "Service account has owner role",
        "recommendation": "Follow least privilege principle and grant only necessary permissions"
      }
    },
    {
      "name": "organizations/123456789/sources/1234567890/findings/finding-3",
      "category": "WEAK_SSL_POLICY",
      "resourceName": "//compute.googleapis.com/projects/example-project-123/global/sslPolicies/weak-ssl-policy",
      "state": "ACTIVE",
      "severity": "MEDIUM",
      "finding": {
        "description": "SSL policy allows TLS 1.0 and TLS 1.1",
        "recommendation": "Update SSL policy to use minimum TLS 1.2"
      }
    },
    {
      "name": "organizations/123456789/sources/1234567890/findings/finding-4",
      "category": "UNUSED_IAM_ROLE",
      "resourceName": "//iam.googleapis.com/projects/example-project-123/roles/customRole123",
      "state": "ACTIVE",
      "severity": "LOW",
      "finding": {
        "description": "Custom role has not been used in 90 days",
        "recommendation": "Review and remove unused custom roles"
      }
    }
  ]
}"#;

    fs::write(path, sample_data)
        .with_context(|| format!("Failed to create sample file: {}", path))?;

    Ok(())
}
