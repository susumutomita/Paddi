#!/bin/bash
# Script to test real data collection from GCP and GitHub

echo "🔧 Testing Paddi with Real Data Collection"
echo "=========================================="

# Check if running in mock mode or real mode
USE_MOCK=${USE_MOCK:-false}

if [ "$USE_MOCK" = "true" ]; then
    echo "⚠️  Running in MOCK mode (no real API calls)"
else
    echo "🌐 Running in REAL mode (will make API calls)"
fi

echo ""
echo "1️⃣  Testing GCP Collection..."
echo "------------------------------"

if [ "$USE_MOCK" = "false" ]; then
    # Real GCP collection
    if [ -z "$GCP_PROJECT_ID" ]; then
        echo "❌ GCP_PROJECT_ID not set. Please export GCP_PROJECT_ID=your-project-id"
        echo "   Or run with USE_MOCK=true for mock data"
    else
        echo "📊 Collecting from GCP project: $GCP_PROJECT_ID"
        python main.py collect --provider gcp --project-id "$GCP_PROJECT_ID" --use-mock false
    fi
else
    # Mock GCP collection
    echo "📊 Collecting mock GCP data..."
    python main.py collect --provider gcp --use-mock true
fi

echo ""
echo "2️⃣  Testing GitHub Collection..."
echo "--------------------------------"

if [ "$USE_MOCK" = "false" ]; then
    # Real GitHub collection
    if [ -z "$GITHUB_ACCESS_TOKEN" ] || [ -z "$GITHUB_OWNER" ] || [ -z "$GITHUB_REPO" ]; then
        echo "❌ GitHub credentials not set. Please export:"
        echo "   GITHUB_ACCESS_TOKEN=your-token"
        echo "   GITHUB_OWNER=your-org-or-username"
        echo "   GITHUB_REPO=your-repo-name"
        echo "   Or run with USE_MOCK=true for mock data"
    else
        echo "📊 Collecting from GitHub repo: $GITHUB_OWNER/$GITHUB_REPO"
        python main.py collect --provider github \
            --github-token "$GITHUB_ACCESS_TOKEN" \
            --github-owner "$GITHUB_OWNER" \
            --github-repo "$GITHUB_REPO" \
            --use-mock false
    fi
else
    # Mock GitHub collection
    echo "📊 Collecting mock GitHub data..."
    python main.py collect --provider github --use-mock true
fi

echo ""
echo "3️⃣  Testing Multi-Provider Collection..."
echo "---------------------------------------"

if [ "$USE_MOCK" = "true" ]; then
    echo "📊 Collecting from multiple providers (mock)..."
    python main.py collect --providers '[
        {"provider": "gcp", "project_id": "test-project"},
        {"provider": "github", "owner": "test-org", "repo": "test-repo"}
    ]' --use-mock true
else
    echo "⚠️  Skipping multi-provider test in real mode (requires all credentials)"
fi

echo ""
echo "4️⃣  Running Full Audit Pipeline..."
echo "----------------------------------"

if [ "$USE_MOCK" = "true" ]; then
    echo "🔍 Running full audit with mock data..."
    python main.py audit --use-mock true
else
    echo "🔍 Running full audit with real data..."
    # This will use whatever data was collected above
    python main.py audit --use-mock false
fi

echo ""
echo "✅ Testing complete! Check the following:"
echo "  - data/collected.json - Raw collected data"
echo "  - data/explained.json - AI-analyzed findings"
echo "  - output/audit.md - Markdown report"
echo "  - output/audit.html - HTML report"