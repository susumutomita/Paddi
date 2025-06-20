use anyhow::{Context, Result};
use indicatif::{ProgressBar, ProgressStyle};
use std::path::PathBuf;
use std::process::Stdio;
use std::time::Duration;
use tokio::process::Command;
use tokio::time::timeout;
use tracing::{debug, error, info};

use crate::config::Config;

pub struct AgentOrchestrator {
    config: Config,
    progress: Option<ProgressBar>,
}

#[derive(Debug)]
pub struct AgentResult {
    pub success: bool,
    pub output: String,
    pub error: String,
}

impl AgentOrchestrator {
    pub fn new(config: Config) -> Self {
        Self {
            config,
            progress: None,
        }
    }

    pub fn with_progress(mut self) -> Self {
        let pb = ProgressBar::new_spinner();
        pb.set_style(
            ProgressStyle::default_spinner()
                .template("{spinner:.green} {msg}")
                .unwrap(),
        );
        pb.enable_steady_tick(Duration::from_millis(100));
        self.progress = Some(pb);
        self
    }

    pub async fn run_collector(&self, use_mock: Option<bool>, project_id: Option<String>) -> Result<AgentResult> {
        self.set_progress_message("Running collector agent...");
        
        let mut args = vec![];
        
        if let Some(use_mock) = use_mock.or(Some(self.config.gcp.use_mock)) {
            args.push(format!("--use_mock={}", use_mock));
        }
        
        if let Some(project_id) = project_id.or(self.config.gcp.project_id.clone()) {
            args.push(format!("--project_id={}", project_id));
        }
        
        self.run_python_agent("collector/agent_collector.py", &args).await
    }

    pub async fn run_explainer(&self, use_mock: Option<bool>, project_id: Option<String>) -> Result<AgentResult> {
        self.set_progress_message("Running explainer agent...");
        
        let mut args = vec![];
        
        if let Some(use_mock) = use_mock.or(Some(self.config.gcp.use_mock)) {
            args.push(format!("--use_mock={}", use_mock));
        }
        
        if let Some(project_id) = project_id.or(self.config.gcp.project_id.clone()) {
            args.push(format!("--project_id={}", project_id));
        }
        
        self.run_python_agent("explainer/agent_explainer.py", &args).await
    }

    pub async fn run_reporter(&self, input_dir: Option<PathBuf>, output_dir: Option<PathBuf>) -> Result<AgentResult> {
        self.set_progress_message("Running reporter agent...");
        
        let mut args = vec![];
        
        if let Some(input_dir) = input_dir.or(Some(self.config.paths.data_dir.clone())) {
            args.push(format!("--input_dir={}", input_dir.display()));
        }
        
        if let Some(output_dir) = output_dir.or(Some(self.config.paths.output_dir.clone())) {
            args.push(format!("--output_dir={}", output_dir.display()));
        }
        
        self.run_python_agent("reporter/agent_reporter.py", &args).await
    }

    pub async fn run_full_audit(
        &self,
        use_mock: Option<bool>,
        project_id: Option<String>,
    ) -> Result<()> {
        info!("Starting full audit pipeline");
        
        // Ensure directories exist
        self.ensure_directories().await?;
        
        // Run collector
        let collector_result = self.run_collector(use_mock.clone(), project_id.clone()).await?;
        if !collector_result.success {
            error!("Collector agent failed: {}", collector_result.error);
            anyhow::bail!("Collector agent failed");
        }
        info!("Collector agent completed successfully");
        
        // Run explainer
        let explainer_result = self.run_explainer(use_mock, project_id).await?;
        if !explainer_result.success {
            error!("Explainer agent failed: {}", explainer_result.error);
            anyhow::bail!("Explainer agent failed");
        }
        info!("Explainer agent completed successfully");
        
        // Run reporter
        let reporter_result = self.run_reporter(None, None).await?;
        if !reporter_result.success {
            error!("Reporter agent failed: {}", reporter_result.error);
            anyhow::bail!("Reporter agent failed");
        }
        info!("Reporter agent completed successfully");
        
        self.finish_progress();
        info!("Full audit pipeline completed successfully");
        
        Ok(())
    }

    async fn run_python_agent(&self, script: &str, args: &[String]) -> Result<AgentResult> {
        let script_path = self.config.python.agents_path.join(script);
        
        debug!("Running Python agent: {} with args: {:?}", script_path.display(), args);
        
        let mut cmd = Command::new(&self.config.python.command);
        cmd.arg(&script_path)
            .args(args)
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .kill_on_drop(true);
        
        let timeout_duration = Duration::from_secs(self.config.execution.timeout_seconds);
        
        let output = timeout(timeout_duration, cmd.output())
            .await
            .context("Agent execution timed out")?
            .context("Failed to execute Python agent")?;
        
        let stdout = String::from_utf8_lossy(&output.stdout).to_string();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        
        if !stderr.is_empty() {
            debug!("Agent stderr: {}", stderr);
        }
        
        Ok(AgentResult {
            success: output.status.success(),
            output: stdout,
            error: stderr,
        })
    }

    async fn ensure_directories(&self) -> Result<()> {
        tokio::fs::create_dir_all(&self.config.paths.data_dir)
            .await
            .context("Failed to create data directory")?;
        
        tokio::fs::create_dir_all(&self.config.paths.output_dir)
            .await
            .context("Failed to create output directory")?;
        
        Ok(())
    }

    fn set_progress_message(&self, msg: &str) {
        if let Some(pb) = &self.progress {
            pb.set_message(msg.to_string());
        }
    }

    fn finish_progress(&self) {
        if let Some(pb) = &self.progress {
            pb.finish_and_clear();
        }
    }
}

pub async fn check_python_available(python_cmd: &str) -> Result<()> {
    let output = Command::new(python_cmd)
        .arg("--version")
        .output()
        .await
        .context("Failed to check Python availability")?;
    
    if !output.status.success() {
        anyhow::bail!("Python command '{}' is not available", python_cmd);
    }
    
    let version = String::from_utf8_lossy(&output.stdout);
    info!("Found Python: {}", version.trim());
    
    Ok(())
}

pub async fn check_agents_exist(agents_path: &PathBuf) -> Result<()> {
    let agents = vec![
        "collector/agent_collector.py",
        "explainer/agent_explainer.py",
        "reporter/agent_reporter.py",
    ];
    
    for agent in agents {
        let path = agents_path.join(agent);
        if !tokio::fs::try_exists(&path).await.unwrap_or(false) {
            anyhow::bail!("Agent not found: {}", path.display());
        }
    }
    
    Ok(())
}