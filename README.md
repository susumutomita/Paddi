# 🩹 Paddi: AI-Powered Multi-Agent Cloud Audit System

[![CI](https://github.com/susumutomita/Paddi/actions/workflows/ci.yml/badge.svg)](https://github.com/susumutomita/Paddi)
![Last commit](https://img.shields.io/github/last-commit/susumutomita/Paddi)
![Top language](https://img.shields.io/github/languages/top/susumutomita/Paddi)
![Pull requests](https://img.shields.io/github/issues-pr/susumutomita/Paddi)
![Code size](https://img.shields.io/github/languages/code-size/susumutomita/Paddi)
![Repo size](https://img.shields.io/github/repo-size/susumutomita/Paddi)

**Paddi** is a multi-agent system that automates cloud security audits using Google Cloud AI and CLI.
It uses three lightweight agents to collect configurations and analyze risks.
These agents work together to generate human-readable reports.

Built for the [Google Cloud AI Hackathon: Multi-Agent Edition](https://googlecloudmultiagents.devpost.com/).
This project demonstrates how AI agents can assist security workflows by reducing manual effort.

---

## 🚀 Features

- ✅ **Google Cloud native** (uses IAM, SCC, and Gemini via Vertex AI)
- 🧠 **Multi-agent architecture**: modular and composable
- 📝 **Report generation** in Markdown and HTML
- 💡 CLI-first, no frontend dependencies
- 🐍 Python for rapid iteration (will migrate to Rust CLI later)
- 🔐 Ideal for internal auditors and DevSecOps teams

---

## 🧩 Architecture

```text
+----------------+       +----------------+       +-----------------+
| Agent A:       | --->  | Agent B:       | --->  | Agent C:        |
|  Collector     |       |  Explainer     |       |  Reporter       |
|  (GCP config)  |       |  (Gemini LLM)  |       |  (Markdown/HTML)|
+----------------+       +----------------+       +-----------------+

Each agent is an independent Python script and can be run locally or integrated into automation pipelines.

⸻

📁 Repository Layout

paddi/
├── python_agents/
│   ├── collector/         # Agent A: GCP config retriever
│   ├── explainer/         # Agent B: Gemini-based LLM analyzer
│   ├── reporter/          # Agent C: Markdown/HTML renderer
│   └── requirements.txt   # Shared dependencies
├── cli/                   # Future Rust-based CLI
├── templates/             # Jinja2 templates for output
├── examples/              # Example IAM and SCC data
└── README.md              # This file


⸻

⚙️ How to Run

1. Set up

cd paddi/python_agents
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

Ensure gcloud auth application-default login is configured if using Gemini (Vertex AI).

2. Run Agents

# Step 1: Collect GCP configs (mocked for now)
python collector/agent_collector.py

# Step 2: Explain security risks using Gemini
python explainer/agent_explainer.py

# Step 3: Generate Markdown and HTML reports
python reporter/agent_reporter.py


⸻

📄 Sample Output
- output/audit.md: Markdown-formatted audit report
- output/audit.html: Web-friendly version
- YAML frontmatter includes metadata

⸻

🌐 Tech Stack
- Python 3.10+
- Google Vertex AI (Gemini Pro via google-cloud-aiplatform)
- Jinja2 templating
- CLI integration planned with Rust (via cargo build --release)
- Markdown + HTML output for compatibility with tools like Obsidian

⸻

🧠 Vision

While this project is a prototype, it is designed with extensibility and enterprise adoption in mind:
- Replace manual cloud audits with reproducible, code-based checks
- Allow pluggable rules, agent chaining, and version-controlled evidence
- Future-proof CLI for multi-platform distribution (macOS/Linux/Windows)

⸻

👥 Authors
- Strategy & Architecture: [Susumu Tomita](https://susumutomita.netlify.app/) - Full Stack Developer
- Implementation: Claude Code + AI collaboration

## Contribution

We welcome contributions. Please submit proposals via pull requests or issues.

## License

MissionChain is licensed under the [MIT License](LICENSE).
