#!/usr/bin/env python3
"""
Example script to run Paddi agents in sequence with mock data
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str):
    """Run a command and print status"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(result.stdout)
        if result.stderr:
            print(f"Warnings: {result.stderr}")
    else:
        print(f"❌ Error: {result.stderr}")
        sys.exit(1)


def main():
    """Run all agents in sequence"""
    print("🎯 Paddi - GCP Security Audit Automation")
    print("Running complete pipeline with mock data...\n")
    
    # Ensure directories exist
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Run Agent A: Collector
    run_command(
        [sys.executable, "collector/agent_collector.py", "--use_mock=True"],
        "Agent A: Collecting GCP configurations"
    )
    
    # Run Agent B: Explainer
    run_command(
        [sys.executable, "explainer/agent_explainer.py", "--use_mock=True"],
        "Agent B: Analyzing security risks with Gemini"
    )
    
    # Run Agent C: Reporter
    run_command(
        [sys.executable, "reporter/agent_reporter.py"],
        "Agent C: Generating audit reports"
    )
    
    print(f"\n{'='*60}")
    print("✅ All agents completed successfully!")
    print(f"{'='*60}")
    print("\n📁 Generated Files:")
    print("  📊 data/collected.json    - Raw GCP configuration data")
    print("  🔍 data/explained.json    - Security findings from Gemini")
    print("  📄 output/audit.md        - Markdown report (Obsidian-compatible)")
    print("  🌐 output/audit.html      - HTML report (browser-viewable)")
    print("\n🎯 Next Steps:")
    print("  1. View the HTML report: open output/audit.html")
    print("  2. Import the Markdown into Obsidian: output/audit.md")
    print("  3. Review and act on the security findings!")


if __name__ == "__main__":
    main()