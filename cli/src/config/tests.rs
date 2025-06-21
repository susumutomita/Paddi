#[cfg(test)]
mod tests {
    use super::super::*;
    use tempfile::TempDir;

    #[test]
    fn test_default_config() {
        let config = Config::default();
        assert_eq!(config.python.command, "python3");
        assert_eq!(config.gcp.use_mock, true);
        assert_eq!(config.execution.timeout_seconds, 300);
    }

    #[test]
    fn test_config_save_and_load() {
        let temp_dir = TempDir::new().unwrap();
        let config_path = temp_dir.path().join("test.toml");
        
        let config = Config::default();
        config.save(&config_path).unwrap();
        
        let loaded = Config::from_file(&config_path).unwrap();
        assert_eq!(config.python.command, loaded.python.command);
        assert_eq!(config.gcp.use_mock, loaded.gcp.use_mock);
    }

    #[test]
    fn test_partial_config() {
        let toml_str = r#"
        [python]
        command = "python"
        
        [gcp]
        project_id = "test-project"
        "#;
        
        let config: Config = toml::from_str(toml_str).unwrap();
        assert_eq!(config.python.command, "python");
        assert_eq!(config.gcp.project_id, Some("test-project".to_string()));
        // Check defaults are applied
        assert_eq!(config.paths.data_dir, PathBuf::from("data"));
    }
}