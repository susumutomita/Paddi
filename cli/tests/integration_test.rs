use assert_cmd::Command;
use predicates::prelude::*;
use tempfile::TempDir;

#[test]
fn test_cli_help() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("Multi-agent cloud security audit"));
}

#[test]
fn test_cli_version() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("--version")
        .assert()
        .success()
        .stdout(predicate::str::contains("paddi"));
}

#[test]
fn test_audit_help() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("audit")
        .arg("--help")
        .assert()
        .success()
        .stdout(predicate::str::contains("Run full audit pipeline"));
}

#[test]
fn test_config_init() {
    let temp_dir = TempDir::new().unwrap();
    let config_path = temp_dir.path().join("test-config.toml");
    
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("config")
        .arg("init")
        .arg("--output")
        .arg(&config_path)
        .assert()
        .success()
        .stdout(predicate::str::contains("Configuration file created"));
    
    assert!(config_path.exists());
}

#[test]
fn test_config_show() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("config")
        .arg("show")
        .assert()
        .success()
        .stdout(predicate::str::contains("[python]"))
        .stdout(predicate::str::contains("[gcp]"));
}

#[test]
fn test_completions_generation() {
    let shells = ["bash", "zsh", "fish", "powershell"];
    
    for shell in &shells {
        let mut cmd = Command::cargo_bin("paddi").unwrap();
        cmd.arg("completions")
            .arg(shell)
            .assert()
            .success();
    }
}

#[test]
fn test_verbose_flag() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("-vv")
        .arg("--help")
        .env("RUST_LOG", "trace")
        .assert()
        .success();
}

#[test]
#[serial_test::serial]
fn test_collect_command_validation() {
    let mut cmd = Command::cargo_bin("paddi").unwrap();
    cmd.arg("collect")
        .arg("--skip-validation")
        .arg("--use-mock")
        .assert()
        .failure() // Will fail because Python agents don't exist in test environment
        .stderr(predicate::str::contains("Failed"));
}