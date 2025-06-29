"""Paddi Web Dashboard Application."""

import logging
import os

# Import Paddi agents
import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from flask import Flask, jsonify, render_template, request  # noqa: E402
from flask_cors import CORS  # noqa: E402

# Import the agent manager and async executor
from app.api.agent_manager import AgentManager  # noqa: E402
from app.api.async_executor import AsyncExecutor  # noqa: E402

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")
app.config["GEMINI_API_KEY"] = os.environ.get("GEMINI_API_KEY", "")

# Initialize agent manager and async executor
agent_manager = AgentManager(data_dir="data", output_dir="output")
async_executor = AsyncExecutor(max_workers=3)


@app.route("/")
def index():
    """Render the main dashboard."""
    return render_template("dashboard.html")


@app.route("/api/health")
def health_check():
    """Health check endpoint for Cloud Run."""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/audit/start", methods=["POST"])
def start_audit():
    """Start a new security audit."""
    try:
        # Get parameters from request
        data = request.get_json() or {}
        project_id = data.get("project_id", "demo-project")
        organization_id = data.get("organization_id")
        use_mock = data.get("use_mock", True)
        location = data.get("location", "us-central1")
        ai_provider = data.get("ai_provider")
        ollama_model = data.get("ollama_model")
        ollama_endpoint = data.get("ollama_endpoint")

        # Start audit through agent manager
        audit_id = agent_manager.start_audit(
            project_id=project_id,
            organization_id=organization_id,
            use_mock=use_mock,
            location=location,
            ai_provider=ai_provider,
            ollama_model=ollama_model,
            ollama_endpoint=ollama_endpoint,
        )

        # Submit for async execution
        async_executor.submit_audit(audit_id, agent_manager.run_audit_sync, audit_id)

        logger.info(f"Started audit {audit_id} for project: {project_id}")

        return jsonify(
            {
                "success": True,
                "audit_id": audit_id,
                "message": "Audit started successfully",
            }
        )

    except Exception as e:
        logger.error("Error starting audit: %s", str(e))
        return (
            jsonify(
                {"success": False, "message": "An internal error occurred. Please try again later."}
            ),
            500,
        )


@app.route("/api/audit/status/<audit_id>")
def get_audit_status(audit_id):
    """Get the status of an ongoing audit."""
    # Get audit status from agent manager
    audit = agent_manager.get_audit_status(audit_id)

    if not audit:
        return jsonify({"error": "Audit not found"}), 404

    # Check if audit is still running
    if async_executor.is_running(audit_id):
        audit["status"] = "running"

    return jsonify(audit)


@app.route("/api/findings")
def get_findings():
    """Get security findings from the latest audit."""
    # Get real findings from agent manager
    findings_data = agent_manager.get_findings()

    if findings_data:
        return jsonify(findings_data)

    # Fall back to mock data if no real data available
    mock_findings = [
        {
            "title": "Excessive Owner Role Permissions",
            "severity": "HIGH",
            "explanation": "Service account has 'roles/owner' which grants excessive permissions.",
            "recommendation": "Follow principle of least privilege and remove owner role.",
            "count": 3,
        },
        {
            "title": "Public Storage Buckets",
            "severity": "MEDIUM",
            "explanation": "Some storage buckets are publicly accessible.",
            "recommendation": "Review and restrict bucket access policies.",
            "count": 5,
        },
        {
            "title": "Unused Service Accounts",
            "severity": "LOW",
            "explanation": "Several service accounts haven't been used in 90+ days.",
            "recommendation": "Consider disabling or removing unused service accounts.",
            "count": 12,
        },
    ]

    return jsonify(
        {
            "findings": mock_findings,
            "total": len(mock_findings),
            "last_updated": datetime.utcnow().isoformat(),
        }
    )


@app.route("/api/findings/severity-distribution")
def get_severity_distribution():
    """Get distribution of findings by severity."""
    # Try to get real data first
    findings_data = agent_manager.get_findings()

    if findings_data and "severity_distribution" in findings_data:
        dist = findings_data["severity_distribution"]
        return jsonify(
            {
                "labels": ["Critical", "High", "Medium", "Low"],
                "data": [
                    dist.get("CRITICAL", 0),
                    dist.get("HIGH", 0),
                    dist.get("MEDIUM", 0),
                    dist.get("LOW", 0),
                ],
                "colors": ["#dc3545", "#fd7e14", "#ffc107", "#28a745"],
            }
        )

    # Fall back to mock data
    return jsonify(
        {
            "labels": ["Critical", "High", "Medium", "Low"],
            "data": [2, 8, 15, 23],
            "colors": ["#dc3545", "#fd7e14", "#ffc107", "#28a745"],
        }
    )


@app.route("/api/findings/timeline")
def get_findings_timeline():
    """Get timeline of security findings."""
    # Mock timeline data
    timeline = []
    for i in range(7):
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        date = date.replace(day=date.day - i)
        timeline.append(
            {
                "date": date.isoformat(),
                "critical": 2 + (i % 3),
                "high": 5 + (i % 4),
                "medium": 10 + (i % 5),
                "low": 20 + (i % 6),
            }
        )

    return jsonify(timeline[::-1])  # Reverse to show oldest first


@app.route("/api/export/<format>")
def export_report(format):
    """Export audit report in specified format."""
    if format not in ["pdf", "markdown", "html"]:
        return jsonify({"error": "Invalid format"}), 400

    # In production, this would generate actual reports
    return jsonify(
        {
            "success": True,
            "message": f"Report exported as {format}",
            "download_url": f"/download/report.{format}",
        }
    )


@app.route("/api/chat", methods=["POST"])
def chat_with_paddi():
    """AI chat interface for asking questions about findings."""
    data = request.get_json()
    question = data.get("question", "")

    # TODO: Integrate with Ollama/Gemini through the explainer
    # For now, provide a contextual response based on real findings
    findings_data = agent_manager.get_findings()

    if findings_data and findings_data["findings"]:
        high_severity = sum(
            1 for f in findings_data["findings"] if f["severity"] in ["HIGH", "CRITICAL"]
        )
        response = (
            f"Based on your security audit, I found {findings_data['total']} security issues. "
            f"There are {high_severity} high-severity findings that require immediate attention. "
            f"Regarding your question: {question} - I recommend reviewing the findings in the "
            f"dashboard and addressing the critical issues first."
        )
    else:
        response = (
            f"I understand you're asking about: {question}. "
            f"Please run an audit first to get specific security findings for your project."
        )

    return jsonify({"response": response, "timestamp": datetime.utcnow().isoformat()})


@app.route("/api/audit", methods=["POST"])
def run_audit_api():
    """Run a complete audit via API."""
    try:
        data = request.get_json()
        provider = data.get("provider", "gcp")

        # For Cloud Run demo, always use mock data
        result = {
            "status": "success",
            "provider": provider,
            "findings": [
                {
                    "title": "Service Account with Owner Role",
                    "severity": "CRITICAL",
                    "description": "Service account has excessive permissions",
                    "recommendation": "Apply principle of least privilege",
                },
                {
                    "title": "Public Storage Bucket",
                    "severity": "HIGH",
                    "description": "Storage bucket is publicly accessible",
                    "recommendation": "Restrict bucket access",
                },
            ],
            "summary": {"total_findings": 2, "critical": 1, "high": 1, "medium": 0, "low": 0},
            "report_url": "/api/export/html",
        }

        return jsonify(result)
    except Exception as e:
        logger.error(f"Error running audit: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "An internal error occurred. Please try again later.",
                }
            ),
            500,
        )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
