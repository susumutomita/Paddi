# Secrets Detection Configuration

This document describes the secrets detection setup for the Paddi project.

## Overview

We use [`detect-secrets`](https://github.com/Yelp/detect-secrets) to prevent accidental commits of sensitive information such as passwords, API keys, and tokens.

## Configuration

### Pre-commit Hook

The secrets detection is integrated into our pre-commit workflow via `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: ['--baseline', '.secrets.baseline']
      exclude: '^(docs/.*\.md|.*\.example|.*\.sample)$'
```

### Baseline File

The `.secrets.baseline` file contains:

- Known false positives (e.g., example credentials in documentation)
- Configuration for active plugins
- Exclusion patterns

### Excluded Files

We exclude the following patterns from secrets scanning:

- `docs/*.md` - Documentation files often contain example credentials
- `*.example` - Example configuration files
- `*.sample` - Sample files

## Usage

### Running Manually

```bash
# Scan the entire codebase
detect-secrets scan --baseline .secrets.baseline --exclude-files '(docs/.*\.md|.*\.example|.*\.sample)'

# Audit the baseline to review findings
detect-secrets audit .secrets.baseline
```

### Integration with Make

Run security checks including secrets detection:

```bash
make lint-security
```

### Pre-commit

The hook runs automatically on git commit. To run manually:

```bash
pre-commit run detect-secrets --all-files
```

## Adding New Secrets

If you need to add legitimate secrets (rare):

1. Never commit actual secrets to the repository
2. Use environment variables or secure secret management
3. Document the secret's purpose in `.env.example`
4. Add patterns to `.gitignore` to prevent accidental commits

## Handling False Positives

If detect-secrets flags a false positive:

1. Review the finding carefully
2. If it's truly a false positive (e.g., example in docs):
   - Run `detect-secrets audit .secrets.baseline`
   - Mark it as a false positive when prompted
3. Commit the updated `.secrets.baseline`

## Security Best Practices

1. **Never commit real credentials** - Use environment variables
2. **Use `.env` files locally** - Never commit them
3. **Rotate credentials regularly** - Especially after potential exposure
4. **Use least privilege** - Grant minimal necessary permissions
5. **Encrypt sensitive data** - Use encryption for stored credentials

## Troubleshooting

### "Secret detected" error on commit

1. Check if it's a real secret that needs removal
2. If false positive, update the baseline:

   ```bash
   detect-secrets scan --baseline .secrets.baseline
   detect-secrets audit .secrets.baseline
   ```

### Baseline out of sync

```bash
# Regenerate the baseline
detect-secrets scan --baseline .secrets.baseline --exclude-files '(docs/.*\.md|.*\.example|.*\.sample)'
```

## Additional Resources

- [detect-secrets documentation](https://github.com/Yelp/detect-secrets)
- [Pre-commit hooks](https://pre-commit.com/)
- [Security best practices](./best-practices.md)
