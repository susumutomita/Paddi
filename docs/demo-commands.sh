#!/bin/bash
# Paddi Demo Commands for Video Recording
# These commands should be run in sequence during the demo

echo "=== Paddi Demo Video - Command Sequence ==="
echo "Follow these commands for the live demo section"
echo ""

# Scene 3: Setup (1:00-1:15)
echo "# 1. Navigate to demo directory"
echo "cd ~/projects/paddi-demo"
echo "ls -la"
echo ""
echo "# 2. Show configuration"
echo "cat paddi.toml"
echo ""

# Scene 4: Initialize (1:15-1:30)
echo "# 3. Initialize Paddi"
echo "paddi init"
echo ""
echo "# When prompted:"
echo "#   - Select: gcp"
echo "#   - Enter project ID: your-gcp-project-id"
echo "#   - Confirm Vertex AI settings"
echo ""

# Scene 5: Run Audit (1:30-2:00)
echo "# 4. Run security audit"
echo "paddi audit --provider gcp --format all"
echo ""
echo "# Expected output:"
echo "# ✓ Collecting IAM policies..."
echo "# ✓ Fetching Security Command Center findings..."
echo "# ✓ Analyzing with Gemini AI..."
echo "# ✓ Generating reports..."
echo "# Audit completed successfully!"
echo ""

# Scene 6: View Reports (2:00-2:20)
echo "# 5. Open HTML report in browser"
echo "open output/audit.html  # macOS"
echo "xdg-open output/audit.html  # Linux"
echo "start output/audit.html  # Windows"
echo ""
echo "# 6. View Markdown report"
echo "code output/audit.md  # VS Code"
echo "cat output/audit.md   # Terminal"
echo ""

# Additional commands for testing
echo "=== Additional Commands for Testing ==="
echo ""
echo "# Check Paddi version"
echo "paddi --version"
echo ""
echo "# Get help"
echo "paddi --help"
echo "paddi audit --help"
echo ""
echo "# Run with specific output format"
echo "paddi audit --provider gcp --format html"
echo "paddi audit --provider gcp --format markdown"
echo ""
echo "# Clean up outputs"
echo "rm -rf output/"
echo ""

# Sample output structure
echo "=== Expected Output Structure ==="
echo "output/"
echo "├── audit.html"
echo "├── audit.md"
echo "└── audit.json"