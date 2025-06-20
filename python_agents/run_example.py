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
    print("Running agents with mock data...\n")
    
    # Ensure data directory exists
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    
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
    
    print(f"\n{'='*60}")
    print("✅ All agents completed successfully!")
    print(f"{'='*60}")
    print("\nResults:")
    print("  - Configuration data: data/collected.json")
    print("  - Security findings: data/explained.json")
    print("\nNext step: Agent C will generate reports (coming soon)")


if __name__ == "__main__":
    main()