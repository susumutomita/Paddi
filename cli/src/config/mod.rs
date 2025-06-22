use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::path::{Path, PathBuf};

#[cfg(test)]
mod tests;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Config {
    #[serde(default)]
    pub python: PythonConfig,

    #[serde(default)]
    pub gcp: GcpConfig,

    #[serde(default)]
    pub paths: PathsConfig,

    #[serde(default)]
    pub execution: ExecutionConfig,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PythonConfig {
    #[serde(default = "default_python_command")]
    pub command: String,

    #[serde(default = "default_agents_path")]
    pub agents_path: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GcpConfig {
    pub project_id: Option<String>,
    pub use_mock: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PathsConfig {
    #[serde(default = "default_data_dir")]
    pub data_dir: PathBuf,

    #[serde(default = "default_output_dir")]
    pub output_dir: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExecutionConfig {
    #[serde(default = "default_parallel")]
    pub parallel: bool,

    #[serde(default = "default_timeout")]
    pub timeout_seconds: u64,
}

impl Default for Config {
    fn default() -> Self {
        Self {
            python: PythonConfig::default(),
            gcp: GcpConfig::default(),
            paths: PathsConfig::default(),
            execution: ExecutionConfig::default(),
        }
    }
}

impl Default for PythonConfig {
    fn default() -> Self {
        Self {
            command: default_python_command(),
            agents_path: default_agents_path(),
        }
    }
}

impl Default for GcpConfig {
    fn default() -> Self {
        Self {
            project_id: None,
            use_mock: true,
        }
    }
}

impl Default for PathsConfig {
    fn default() -> Self {
        Self {
            data_dir: default_data_dir(),
            output_dir: default_output_dir(),
        }
    }
}

impl Default for ExecutionConfig {
    fn default() -> Self {
        Self {
            parallel: default_parallel(),
            timeout_seconds: default_timeout(),
        }
    }
}

fn default_python_command() -> String {
    "python3".to_string()
}

fn default_agents_path() -> PathBuf {
    PathBuf::from("python_agents")
}

fn default_data_dir() -> PathBuf {
    PathBuf::from("data")
}

fn default_output_dir() -> PathBuf {
    PathBuf::from("output")
}

fn default_parallel() -> bool {
    false
}

fn default_timeout() -> u64 {
    300 // 5 minutes
}

impl Config {
    pub fn load() -> Result<Self> {
        // Try to load from default locations
        let config_paths = vec![
            PathBuf::from("paddi.toml"),
            PathBuf::from(".paddi.toml"),
            dirs::config_dir()
                .map(|p| p.join("paddi").join("config.toml"))
                .unwrap_or_default(),
        ];

        for path in config_paths {
            if path.exists() {
                return Self::from_file(&path);
            }
        }

        // Return default config if no file found
        Ok(Self::default())
    }

    pub fn from_file(path: impl AsRef<Path>) -> Result<Self> {
        let path = path.as_ref();
        let content = std::fs::read_to_string(path)
            .with_context(|| format!("Failed to read config file: {}", path.display()))?;

        let config: Config = toml::from_str(&content)
            .with_context(|| format!("Failed to parse config file: {}", path.display()))?;

        Ok(config)
    }

    pub fn save(&self, path: impl AsRef<Path>) -> Result<()> {
        let path = path.as_ref();

        // Create parent directories if they don't exist
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent).with_context(|| {
                format!("Failed to create config directory: {}", parent.display())
            })?;
        }

        let content = toml::to_string_pretty(self).context("Failed to serialize config")?;

        std::fs::write(path, content)
            .with_context(|| format!("Failed to write config file: {}", path.display()))?;

        Ok(())
    }
}
