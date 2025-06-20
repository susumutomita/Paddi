use anyhow::Result;
use clap::Parser;
use tracing::info;

use crate::config::Config;
use crate::orchestrator::{check_agents_exist, check_python_available, AgentOrchestrator};

#[derive(Parser, Debug)]
pub struct AnalyzeArgs {
    #[arg(long, help = "Use mock data instead of real Vertex AI")]
    use_mock: Option<bool>,
    
    #[arg(long, help = "GCP project ID")]
    project_id: Option<String>,
    
    #[arg(long, help = "Skip validation checks")]
    skip_validation: bool,
}

pub async fn run(args: AnalyzeArgs, config: Config) -> Result<()> {
    info!("Running explainer agent");
    
    // Validation checks
    if !args.skip_validation {
        check_python_available(&config.python.command).await?;
        check_agents_exist(&config.python.agents_path).await?;
    }
    
    // Check if input data exists
    let input_file = config.paths.data_dir.join("collected.json");
    if !tokio::fs::try_exists(&input_file).await.unwrap_or(false) {
        anyhow::bail!(
            "Input file not found: {}. Please run 'paddi collect' first.",
            input_file.display()
        );
    }
    
    // Create orchestrator
    let orchestrator = AgentOrchestrator::new(config).with_progress();
    
    // Run explainer
    let result = orchestrator.run_explainer(args.use_mock, args.project_id).await?;
    
    if result.success {
        info!("Analysis completed successfully");
        println!("\n✅ Analysis completed successfully!");
        println!("📄 Results saved to 'data/explained.json'");
    } else {
        anyhow::bail!("Analysis failed: {}", result.error);
    }
    
    Ok(())
}