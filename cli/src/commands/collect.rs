use anyhow::Result;
use clap::Parser;
use tracing::info;

use crate::config::Config;
use crate::orchestrator::{check_agents_exist, check_python_available, AgentOrchestrator};

#[derive(Parser, Debug)]
pub struct CollectArgs {
    #[arg(long, help = "Use mock data instead of real GCP APIs")]
    use_mock: Option<bool>,

    #[arg(long, help = "GCP project ID")]
    project_id: Option<String>,

    #[arg(long, help = "Skip validation checks")]
    skip_validation: bool,
}

pub async fn run(args: CollectArgs, config: Config) -> Result<()> {
    info!("Running collector agent");

    // Validation checks
    if !args.skip_validation {
        check_python_available(&config.python.command).await?;
        check_agents_exist(&config.python.agents_path).await?;
    }

    // Create orchestrator
    let orchestrator = AgentOrchestrator::new(config).with_progress();

    // Ensure data directory exists
    tokio::fs::create_dir_all("data").await?;

    // Run collector
    let result = orchestrator
        .run_collector(args.use_mock, args.project_id)
        .await?;

    if result.success {
        info!("Collection completed successfully");
        println!("\n✅ Collection completed successfully!");
        println!("📄 Data saved to 'data/collected.json'");
    } else {
        anyhow::bail!("Collection failed: {}", result.error);
    }

    Ok(())
}
