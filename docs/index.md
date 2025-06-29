# Paddi Documentation

Welcome to Paddi's documentation! Paddi is a multi-cloud security audit automation tool that uses AI agents to analyze and report security risks across multiple cloud environments.

## Overview

Paddi automates cloud security auditing across GCP, AWS, and Azure by leveraging Vertex AI (Gemini) to identify and explain security risks in natural language. It features autonomous AI agents that can recursively investigate security issues and generate comprehensive reports.

## Contents

```{toctree}
:maxdepth: 2
:caption: Getting Started

getting-started/installation
getting-started/quick-start
getting-started/configuration
getting-started/ollama-setup
```

```{toctree}
:maxdepth: 2
:caption: Architecture

architecture-mermaid
agents/collector
agents/explainer
agents/reporter
```

```{toctree}
:maxdepth: 2
:caption: Usage

cli/commands
examples/basic-audit
examples/advanced-scenarios
usage-scenarios
```

```{toctree}
:maxdepth: 2
:caption: API Reference

api/reference
api/modules
```

```{toctree}
:maxdepth: 2
:caption: Deployment

cloud-run-deployment
gcp-permissions
setup-real-data
```

```{toctree}
:maxdepth: 2
:caption: Security

security/README
security/best-practices
security/secrets-detection
safety_system
```

```{toctree}
:maxdepth: 2
:caption: Contributing

contributing/development
contributing/code-style
```

## Indices and tables

* {ref}`genindex`
* {ref}`modindex`
* {ref}`search`