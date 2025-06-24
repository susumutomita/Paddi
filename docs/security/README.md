# Security Documentation

This directory contains security-related documentation for the Paddi project.

## Contents

- [Best Practices](./best-practices.md) - Security best practices for cloud auditing
- [Secrets Detection](./secrets-detection.md) - Configuration and usage of secrets detection
- [GCP Service Account Management](./service-account-management.md) - Managing GCP service accounts securely

## Quick Security Checklist

### Before Committing Code

- [ ] Run `make lint-security` to check for security issues
- [ ] Ensure no secrets are hardcoded (API keys, passwords, tokens)
- [ ] Verify `.gitignore` includes all sensitive files
- [ ] Use environment variables for configuration

### Service Account Security

- [ ] Use separate service accounts for each environment
- [ ] Apply least privilege principle
- [ ] Rotate keys regularly
- [ ] Never commit service account keys

### Secrets Management

- [ ] detect-secrets is configured and running
- [ ] Pre-commit hooks are installed
- [ ] `.secrets.baseline` is up to date
- [ ] All team members know how to handle false positives

## Security Tools

1. **bandit** - Finds common security issues in Python code
2. **detect-secrets** - Prevents secrets from being committed
3. **Pre-commit hooks** - Automated security checks before commit

## Running Security Checks

```bash
# Run all security checks
make lint-security

# Run specific tools
bandit -c pyproject.toml -r app/
detect-secrets scan --baseline .secrets.baseline

# Install pre-commit hooks
pre-commit install
```

## Reporting Security Issues

If you discover a security vulnerability:

1. Do not create a public issue
2. Contact the maintainers directly
3. Provide detailed information about the vulnerability
4. Allow time for a fix before public disclosure
