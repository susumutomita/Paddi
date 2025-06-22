"""Paddi Web Dashboard Application."""

import os
import json
import asyncio
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import logging

# Import Paddi agents
import sys
sys.path.append(str(Path(__file__).parent.parent))
from app.collector.agent_collector import CollectorAgent
from app.explainer.agent_explainer import ExplainerAgent
from app.reporter.agent_reporter import ReporterAgent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['GEMINI_API_KEY'] = os.environ.get('GEMINI_API_KEY', '')

# Data storage (in production, use a database)
audit_results = []
current_audit = None


@app.route('/')
def index():
    """Render the main dashboard."""
    return render_template('dashboard.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint for Cloud Run."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat()
    })


@app.route('/api/audit/start', methods=['POST'])
def start_audit():
    """Start a new security audit."""
    global current_audit
    
    try:
        # Get project ID from request
        data = request.get_json()
        project_id = data.get('project_id', 'demo-project')
        
        # Initialize audit
        current_audit = {
            'id': f"audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            'project_id': project_id,
            'status': 'running',
            'started_at': datetime.utcnow().isoformat(),
            'findings': []
        }
        
        # In a real implementation, this would run asynchronously
        # For now, we'll use mock data
        logger.info(f"Starting audit for project: {project_id}")
        
        return jsonify({
            'success': True,
            'audit_id': current_audit['id'],
            'message': 'Audit started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting audit: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/audit/status/<audit_id>')
def get_audit_status(audit_id):
    """Get the status of an ongoing audit."""
    if current_audit and current_audit['id'] == audit_id:
        return jsonify(current_audit)
    
    # Check historical audits
    for audit in audit_results:
        if audit['id'] == audit_id:
            return jsonify(audit)
    
    return jsonify({'error': 'Audit not found'}), 404


@app.route('/api/findings')
def get_findings():
    """Get security findings from the latest audit."""
    # For demo purposes, return mock data
    # In production, this would fetch from the explained.json file
    mock_findings = [
        {
            "title": "Excessive Owner Role Permissions",
            "severity": "HIGH",
            "explanation": "Service account has 'roles/owner' which grants excessive permissions.",
            "recommendation": "Follow principle of least privilege and remove owner role.",
            "count": 3
        },
        {
            "title": "Public Storage Buckets",
            "severity": "MEDIUM",
            "explanation": "Some storage buckets are publicly accessible.",
            "recommendation": "Review and restrict bucket access policies.",
            "count": 5
        },
        {
            "title": "Unused Service Accounts",
            "severity": "LOW",
            "explanation": "Several service accounts haven't been used in 90+ days.",
            "recommendation": "Consider disabling or removing unused service accounts.",
            "count": 12
        }
    ]
    
    return jsonify({
        'findings': mock_findings,
        'total': len(mock_findings),
        'last_updated': datetime.utcnow().isoformat()
    })


@app.route('/api/findings/severity-distribution')
def get_severity_distribution():
    """Get distribution of findings by severity."""
    # Mock data for visualization
    return jsonify({
        'labels': ['Critical', 'High', 'Medium', 'Low'],
        'data': [2, 8, 15, 23],
        'colors': ['#dc3545', '#fd7e14', '#ffc107', '#28a745']
    })


@app.route('/api/findings/timeline')
def get_findings_timeline():
    """Get timeline of security findings."""
    # Mock timeline data
    timeline = []
    for i in range(7):
        date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        date = date.replace(day=date.day - i)
        timeline.append({
            'date': date.isoformat(),
            'critical': 2 + (i % 3),
            'high': 5 + (i % 4),
            'medium': 10 + (i % 5),
            'low': 20 + (i % 6)
        })
    
    return jsonify(timeline[::-1])  # Reverse to show oldest first


@app.route('/api/export/<format>')
def export_report(format):
    """Export audit report in specified format."""
    if format not in ['pdf', 'markdown', 'html']:
        return jsonify({'error': 'Invalid format'}), 400
    
    # In production, this would generate actual reports
    return jsonify({
        'success': True,
        'message': f'Report exported as {format}',
        'download_url': f'/download/report.{format}'
    })


@app.route('/api/chat', methods=['POST'])
def chat_with_paddi():
    """AI chat interface for asking questions about findings."""
    data = request.get_json()
    question = data.get('question', '')
    
    # Mock response - in production, this would use Gemini
    mock_response = f"Based on your security audit, I can see that {question}. " \
                   f"The most critical issue is the excessive owner role permissions. " \
                   f"I recommend starting with addressing the high-severity findings first."
    
    return jsonify({
        'response': mock_response,
        'timestamp': datetime.utcnow().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)