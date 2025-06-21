# Paddi CLI

A Rust-based CLI tool for orchestrating multi-agent cloud security audits.

## Features

- 🚀 Fast and efficient orchestration of Python agents
- 📊 Progress indicators and detailed logging
- ⚙️ Flexible configuration management (TOML/YAML)
- 🔧 Modular command structure
- 🌍 Cross-platform support (Linux, macOS, Windows)
- 🐚 Shell completion support

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/susumutomita/Paddi
cd Paddi/cli

# Build and install
cargo build --release
cargo install --path .
```

### Using Install Script

```bash
cd cli
chmod +x scripts/install.sh
./scripts/install.sh
```

## Usage

### Run Full Audit Pipeline

```bash
# Run with default settings (mock data)
paddi audit

# Run with real GCP data
paddi audit --project-id=my-project --no-use-mock

# Run with custom config
paddi --config=custom.toml audit
```

### Run Individual Agents

```bash
# Collect GCP configuration data
paddi collect --project-id=my-project

# Analyze security risks
paddi analyze --use-mock

# Generate reports
paddi report --output-dir=./reports
```

### Configuration Management

```bash
# Create a new config file
paddi config init

# Show current configuration
paddi config show

# Validate configuration
paddi config validate --file=paddi.toml
```

## Configuration

Create a `paddi.toml` file:

```toml
[python]
command = "python3"
agents_path = "python_agents"

[gcp]
project_id = "my-gcp-project"
use_mock = false

[paths]
data_dir = "data"
output_dir = "output"

[execution]
parallel = false
timeout_seconds = 300
```

## Development

### Building

```bash
# Build for current platform
cargo build --release

# Build for all platforms
./scripts/build.sh
```

### Testing

```bash
# Run unit tests
cargo test

# Run integration tests
cargo test --test '*' -- --test-threads=1
```

### Adding Shell Completions

```bash
# Bash
paddi completions bash > ~/.local/share/bash-completion/completions/paddi

# Zsh
paddi completions zsh > ~/.zsh/completions/_paddi

# Fish
paddi completions fish > ~/.config/fish/completions/paddi.fish
```

## Architecture

The CLI is structured as follows:

- `src/main.rs` - Entry point and CLI argument parsing
- `src/config/` - Configuration management
- `src/orchestrator/` - Python agent orchestration logic
- `src/commands/` - Individual command implementations
  - `audit.rs` - Full pipeline execution
  - `collect.rs` - Data collection
  - `analyze.rs` - Security analysis
  - `report.rs` - Report generation
  - `config.rs` - Configuration management

## Environment Variables

- `PADDI_CONFIG` - Path to configuration file
- `RUST_LOG` - Logging level (trace, debug, info, warn, error)

## License

MIT