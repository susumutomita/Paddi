use anyhow::Result;
use clap::{Command, CommandFactory, Parser, Subcommand};
use clap_complete::{generate, Shell};
use std::io;
use tracing_subscriber::{layer::SubscriberExt, util::SubscriberInitExt};

mod commands;
mod config;
mod orchestrator;

use commands::{analyze, audit, collect, config as config_cmd, init, report};
use config::Config;

#[derive(Parser)]
#[command(
    name = "paddi",
    about = "Multi-agent cloud security audit orchestration CLI",
    version,
    author,
    long_about = None
)]
struct Cli {
    #[command(subcommand)]
    command: Commands,

    #[arg(
        short,
        long,
        global = true,
        help = "Increase logging verbosity",
        action = clap::ArgAction::Count
    )]
    verbose: u8,

    #[arg(
        short,
        long,
        global = true,
        help = "Configuration file path",
        env = "PADDI_CONFIG"
    )]
    config: Option<String>,
}

#[derive(Subcommand)]
enum Commands {
    #[command(about = "Initialize Paddi with sample data for quick trial")]
    Init(init::InitArgs),

    #[command(about = "Run full audit pipeline")]
    Audit(audit::AuditArgs),

    #[command(about = "Run only collector agent")]
    Collect(collect::CollectArgs),

    #[command(about = "Run only analysis agent", visible_alias = "analyse")]
    Analyze(analyze::AnalyzeArgs),

    #[command(about = "Run only reporter agent")]
    Report(report::ReportArgs),

    #[command(about = "Manage configuration")]
    Config(config_cmd::ConfigArgs),

    #[command(about = "Generate shell completions")]
    Completions {
        #[arg(value_enum)]
        shell: Shell,
    },
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();

    // Initialize tracing
    let log_level = match cli.verbose {
        0 => "info",
        1 => "debug",
        _ => "trace",
    };

    tracing_subscriber::registry()
        .with(
            tracing_subscriber::fmt::layer()
                .with_target(false)
                .with_thread_ids(false)
                .with_thread_names(false),
        )
        .with(tracing_subscriber::EnvFilter::try_from_default_env().unwrap_or_else(|_| {
            tracing_subscriber::EnvFilter::new(log_level)
        }))
        .init();

    // Load configuration
    let config = if let Some(config_path) = cli.config {
        Config::from_file(&config_path)?
    } else {
        Config::load()?
    };

    // Execute command
    match cli.command {
        Commands::Init(args) => init::run(args, config).await,
        Commands::Audit(args) => audit::run(args, config).await,
        Commands::Collect(args) => collect::run(args, config).await,
        Commands::Analyze(args) => analyze::run(args, config).await,
        Commands::Report(args) => report::run(args, config).await,
        Commands::Config(args) => config_cmd::run(args, config).await,
        Commands::Completions { shell } => {
            let mut cmd = Cli::command();
            let name = cmd.get_name().to_string();
            generate(shell, &mut cmd, name, &mut io::stdout());
            Ok(())
        }
    }
}