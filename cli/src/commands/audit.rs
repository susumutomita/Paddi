use anyhow::Result;
use clap::Parser;
use tracing::info;

use crate::config::Config;
use crate::orchestrator::{check_agents_exist, check_python_available, AgentOrchestrator};

#[derive(Parser, Debug)]
pub struct AuditArgs {
    #[arg(long, help = "Use mock data instead of real GCP APIs")]
    use_mock: Option<bool>,

    #[arg(long, help = "GCP project ID")]
    project_id: Option<String>,

    #[arg(long, help = "Skip validation checks")]
    skip_validation: bool,
}

pub async fn run(args: AuditArgs, config: Config) -> Result<()> {
    info!("Running full audit pipeline");

    // Validation checks
    if !args.skip_validation {
        check_python_available(&config.python.command).await?;
        check_agents_exist(&config.python.agents_path).await?;
    }

    // Create orchestrator
    let orchestrator = AgentOrchestrator::new(config).with_progress();

    // Run full audit
    orchestrator
        .run_full_audit(args.use_mock, args.project_id)
        .await?;

    info!("Audit completed successfully");
    println!("\n✅ Audit completed successfully!");
    println!("📄 Reports generated in 'output/' directory");

    Ok(())
}
