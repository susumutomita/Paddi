.PHONY: all build test clean install lint fmt check release

# Default target
all: build

# Build the CLI
build:
	cargo build

# Build release version
release:
	cargo build --release

# Run tests
test:
	cargo test

# Run integration tests
test-integration:
	cargo test --test '*' -- --test-threads=1

# Clean build artifacts
clean:
	cargo clean
	rm -rf dist/

# Install locally
install: release
	cargo install --path .

# Format code
fmt:
	cargo fmt

# Check formatting
fmt-check:
	cargo fmt -- --check

# Run clippy
lint:
	cargo clippy -- -D warnings

# Run all checks (for CI)
check: fmt-check lint test

# Build for all platforms
build-all:
	./scripts/build.sh

# Create distribution packages
dist: build-all
	@echo "Distribution packages created in dist/"

# Generate documentation
doc:
	cargo doc --no-deps --open

# Run benchmarks
bench:
	cargo bench

# Update dependencies
update:
	cargo update

# Security audit
audit:
	cargo audit