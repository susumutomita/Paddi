use anyhow::Result;
use clap::{Parser, Subcommand};
use std::path::PathBuf;
use tracing::info;

use crate::config::Config;

#[derive(Parser, Debug)]
pub struct ConfigArgs {
    #[command(subcommand)]
    command: ConfigCommands,
}

#[derive(Subcommand, Debug)]
enum ConfigCommands {
    #[command(about = "Show current configuration")]
    Show,

    #[command(about = "Initialize a new configuration file")]
    Init {
        #[arg(
            long,
            help = "Output path for config file",
            default_value = "paddi.toml"
        )]
        output: PathBuf,

        #[arg(long, help = "Overwrite existing file")]
        force: bool,
    },

    #[command(about = "Validate configuration")]
    Validate {
        #[arg(long, help = "Path to config file")]
        file: Option<PathBuf>,
    },
}

pub async fn run(args: ConfigArgs, config: Config) -> Result<()> {
    match args.command {
        ConfigCommands::Show => show_config(config).await,
        ConfigCommands::Init { output, force } => init_config(output, force).await,
        ConfigCommands::Validate { file } => validate_config(file, config).await,
    }
}

async fn show_config(config: Config) -> Result<()> {
    info!("Showing current configuration");

    let toml_str = toml::to_string_pretty(&config)?;
    println!("Current configuration:\n");
    println!("{}", toml_str);

    Ok(())
}

async fn init_config(output: PathBuf, force: bool) -> Result<()> {
    info!("Initializing configuration file");

    // Check if file exists
    if tokio::fs::try_exists(&output).await.unwrap_or(false) && !force {
        anyhow::bail!(
            "Configuration file already exists: {}. Use --force to overwrite.",
            output.display()
        );
    }

    // Create default config
    let config = Config::default();

    // Save to file
    config.save(&output)?;

    println!("✅ Configuration file created: {}", output.display());
    println!("\nExample configuration:");
    println!("{}", toml::to_string_pretty(&config)?);

    Ok(())
}

async fn validate_config(file: Option<PathBuf>, default_config: Config) -> Result<()> {
    info!("Validating configuration");

    let config = if let Some(file) = file {
        Config::from_file(&file)?
    } else {
        default_config
    };

    // Validate Python command
    println!("🔍 Checking Python command: {}", config.python.command);
    match crate::orchestrator::check_python_available(&config.python.command).await {
        Ok(_) => println!("✅ Python command is available"),
        Err(e) => println!("❌ Python command check failed: {}", e),
    }

    // Validate agents path
    println!(
        "\n🔍 Checking agents path: {}",
        config.python.agents_path.display()
    );
    match crate::orchestrator::check_agents_exist(&config.python.agents_path).await {
        Ok(_) => println!("✅ All agents found"),
        Err(e) => println!("❌ Agents check failed: {}", e),
    }

    // Validate directories
    println!("\n🔍 Checking directories:");
    println!("   Data directory: {}", config.paths.data_dir.display());
    println!("   Output directory: {}", config.paths.output_dir.display());

    // Show other settings
    println!("\n📋 Other settings:");
    println!(
        "   GCP Project ID: {}",
        config.gcp.project_id.as_deref().unwrap_or("Not set")
    );
    println!("   Use mock data: {}", config.gcp.use_mock);
    println!("   Parallel execution: {}", config.execution.parallel);
    println!("   Timeout: {} seconds", config.execution.timeout_seconds);

    println!("\n✅ Configuration is valid");

    Ok(())
}
