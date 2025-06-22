use anyhow::Result;
use clap::Parser;
use std::path::PathBuf;
use tracing::info;

use crate::config::Config;
use crate::orchestrator::{check_agents_exist, check_python_available, AgentOrchestrator};

#[derive(Parser, Debug)]
pub struct ReportArgs {
    #[arg(long, help = "Input directory containing explained.json")]
    input_dir: Option<PathBuf>,

    #[arg(long, help = "Output directory for reports")]
    output_dir: Option<PathBuf>,

    #[arg(long, help = "Report formats to generate", value_delimiter = ',')]
    format: Option<Vec<String>>,

    #[arg(long, help = "Skip validation checks")]
    skip_validation: bool,
}

pub async fn run(args: ReportArgs, config: Config) -> Result<()> {
    info!("Running reporter agent");

    // Validation checks
    if !args.skip_validation {
        check_python_available(&config.python.command).await?;
        check_agents_exist(&config.python.agents_path).await?;
    }

    // Check if input data exists
    let input_dir = args.input_dir.as_ref().unwrap_or(&config.paths.data_dir);
    let input_file = input_dir.join("explained.json");
    if !tokio::fs::try_exists(&input_file).await.unwrap_or(false) {
        anyhow::bail!(
            "Input file not found: {}. Please run 'paddi analyze' first.",
            input_file.display()
        );
    }

    // Create orchestrator
    let orchestrator = AgentOrchestrator::new(config.clone()).with_progress();

    // Ensure output directory exists
    let output_dir = args.output_dir.as_ref().unwrap_or(&config.paths.output_dir);
    tokio::fs::create_dir_all(output_dir).await?;

    // Run reporter
    let result = orchestrator
        .run_reporter(args.input_dir.clone(), args.output_dir.clone(), args.format)
        .await?;

    if result.success {
        info!("Report generation completed successfully");
        println!("\n✅ Report generation completed successfully!");
        println!("📄 Reports generated:");
        println!("   - {}/audit.md", output_dir.display());
        println!("   - {}/audit.html", output_dir.display());

        // Check if HonKit docs were generated
        let docs_dir = output_dir.parent().unwrap_or(output_dir).join("docs");
        if tokio::fs::try_exists(&docs_dir).await.unwrap_or(false) {
            println!("   - {}/", docs_dir.display());
            println!("\n📚 To preview HonKit documentation:");
            println!("   npx honkit serve {}", docs_dir.display());
        }
    } else {
        anyhow::bail!("Report generation failed: {}", result.error);
    }

    Ok(())
}
