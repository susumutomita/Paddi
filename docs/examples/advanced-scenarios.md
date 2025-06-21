# Advanced Scenarios

This guide covers advanced use cases and complex scenarios for Paddi.

## Multi-Project Organization Audits

### Auditing an Entire Organization

```python
#!/usr/bin/env python3
# org_audit.py

import subprocess
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

def audit_project(project_id):
    """Run audit for a single project."""
    print(f"Auditing {project_id}...")
    
    result = subprocess.run(
        ["paddi", "audit", 
         f"--project-id={project_id}",
         f"--output-dir=./audits/{project_id}",
         "--output-format=json"],
        capture_output=True,
        text=True
    )
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        return {
            "project_id": project_id,
            "status": "success",
            "findings": data["findings"],
            "summary": data["summary"]
        }
    else:
        return {
            "project_id": project_id,
            "status": "failed",
            "error": result.stderr
        }

def generate_org_report(results):
    """Generate organization-wide report."""
    total_findings = sum(r["summary"]["total"] for r in results if r["status"] == "success")
    critical_projects = [r for r in results if r["status"] == "success" 
                        and r["summary"]["by_severity"].get("CRITICAL", 0) > 0]
    
    report = f"""# Organization Security Audit Report
    
Generated: {datetime.now().isoformat()}

## Executive Summary

- **Projects Audited:** {len(results)}
- **Total Findings:** {total_findings}
- **Projects with Critical Issues:** {len(critical_projects)}

## Critical Projects Requiring Immediate Attention

"""
    
    for project in critical_projects:
        critical_count = project["summary"]["by_severity"]["CRITICAL"]
        report += f"- **{project['project_id']}**: {critical_count} critical findings\n"
    
    return report

# Main execution
if __name__ == "__main__":
    # Get all projects
    result = subprocess.run(
        ["gcloud", "projects", "list", "--format=value(projectId)"],
        capture_output=True,
        text=True
    )
    
    project_ids = result.stdout.strip().split('\n')
    
    # Audit projects in parallel
    results = []
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(audit_project, pid): pid for pid in project_ids}
        
        for future in as_completed(futures):
            results.append(future.result())
    
    # Generate organization report
    org_report = generate_org_report(results)
    
    with open("org_audit_report.md", "w") as f:
        f.write(org_report)
    
    print("Organization audit complete! See org_audit_report.md")
```

### Cross-Project Resource Analysis

```python
# cross_project_analysis.py

from python_agents.collector.agent_collector import CollectorAgent
from python_agents.explainer.agent_explainer import ExplainerAgent
import json

class CrossProjectAnalyzer:
    """Analyze security issues across multiple projects."""
    
    def __init__(self, project_ids):
        self.project_ids = project_ids
        self.all_data = {}
    
    def collect_all_projects(self):
        """Collect data from all projects."""
        for project_id in self.project_ids:
            print(f"Collecting from {project_id}...")
            collector = CollectorAgent({"project_id": project_id})
            self.all_data[project_id] = collector.collect()
    
    def analyze_cross_project_risks(self):
        """Identify risks that span multiple projects."""
        findings = []
        
        # Check for cross-project IAM issues
        service_accounts = {}
        for project_id, data in self.all_data.items():
            for policy in data.get("iam_policies", []):
                for binding in policy["policy"]["bindings"]:
                    for member in binding["members"]:
                        if member.startswith("serviceAccount:"):
                            sa = member.split(":")[1]
                            if sa not in service_accounts:
                                service_accounts[sa] = []
                            service_accounts[sa].append({
                                "project": project_id,
                                "role": binding["role"]
                            })
        
        # Flag service accounts with access to multiple projects
        for sa, access_list in service_accounts.items():
            if len(access_list) > 1:
                projects = [a["project"] for a in access_list]
                findings.append({
                    "title": f"Service Account with Cross-Project Access",
                    "severity": "HIGH",
                    "explanation": f"Service account {sa} has access to multiple projects: {', '.join(projects)}",
                    "recommendation": "Review if cross-project access is necessary. Consider using separate service accounts per project.",
                    "affected_projects": projects
                })
        
        return findings

# Usage
analyzer = CrossProjectAnalyzer(["project-1", "project-2", "project-3"])
analyzer.collect_all_projects()
cross_project_findings = analyzer.analyze_cross_project_risks()
```

## Custom Security Policies

### Implementing Organization-Specific Rules

```python
# custom_policies.py

from typing import List, Dict
from dataclasses import dataclass

@dataclass
class SecurityPolicy:
    """Define a custom security policy."""
    name: str
    description: str
    severity: str
    check_function: callable

class CustomPolicyEngine:
    """Engine for custom security policies."""
    
    def __init__(self):
        self.policies = []
    
    def add_policy(self, policy: SecurityPolicy):
        """Add a custom policy."""
        self.policies.append(policy)
    
    def evaluate(self, resource: Dict) -> List[Dict]:
        """Evaluate resource against all policies."""
        findings = []
        
        for policy in self.policies:
            if policy.check_function(resource):
                findings.append({
                    "title": policy.name,
                    "severity": policy.severity,
                    "explanation": policy.description,
                    "policy_id": f"CUSTOM-{policy.name.replace(' ', '-').upper()}"
                })
        
        return findings

# Define custom policies
engine = CustomPolicyEngine()

# Policy: No external Gmail accounts
engine.add_policy(SecurityPolicy(
    name="No External Gmail Accounts",
    description="IAM policies should not include external gmail.com accounts",
    severity="HIGH",
    check_function=lambda r: any(
        "@gmail.com" in member 
        for binding in r.get("policy", {}).get("bindings", [])
        for member in binding.get("members", [])
    )
))

# Policy: Enforce resource labeling
engine.add_policy(SecurityPolicy(
    name="Missing Required Labels",
    description="All resources must have 'environment' and 'owner' labels",
    severity="MEDIUM",
    check_function=lambda r: not all(
        label in r.get("labels", {}) 
        for label in ["environment", "owner"]
    )
))

# Policy: Service account key age
engine.add_policy(SecurityPolicy(
    name="Old Service Account Keys",
    description="Service account keys older than 90 days should be rotated",
    severity="HIGH",
    check_function=lambda r: r.get("type") == "service_account_key" 
        and r.get("age_days", 0) > 90
))
```

### Integrating Custom Policies with Paddi

```python
# integrated_custom_audit.py

from python_agents.explainer.agent_explainer import ExplainerAgent
from custom_policies import CustomPolicyEngine

class CustomExplainerAgent(ExplainerAgent):
    """Extended explainer with custom policies."""
    
    def __init__(self, config, custom_engine):
        super().__init__(config)
        self.custom_engine = custom_engine
    
    def analyze(self, collected_data):
        """Analyze with both AI and custom policies."""
        # Get AI-based findings
        ai_findings = super().analyze(collected_data)
        
        # Apply custom policies
        custom_findings = []
        for resource in collected_data.get("resources", []):
            findings = self.custom_engine.evaluate(resource)
            custom_findings.extend(findings)
        
        # Combine and deduplicate
        all_findings = ai_findings + custom_findings
        return self.deduplicate_findings(all_findings)
```

## Advanced Reporting

### Interactive Dashboard Generation

```python
# dashboard_generator.py

import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

class DashboardGenerator:
    """Generate interactive security dashboards."""
    
    def __init__(self, findings_data):
        self.findings = findings_data
        self.df = pd.DataFrame(findings_data)
    
    def generate_severity_chart(self):
        """Create severity distribution chart."""
        severity_counts = self.df['severity'].value_counts()
        
        fig = go.Figure(data=[go.Pie(
            labels=severity_counts.index,
            values=severity_counts.values,
            hole=0.3,
            marker_colors=['#d32f2f', '#f57c00', '#fbc02d', '#388e3c']
        )])
        
        fig.update_layout(title="Findings by Severity")
        return fig
    
    def generate_timeline_chart(self):
        """Create findings timeline."""
        # Group by date and severity
        timeline_data = self.df.groupby(['date', 'severity']).size().reset_index(name='count')
        
        fig = go.Figure()
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            data = timeline_data[timeline_data['severity'] == severity]
            fig.add_trace(go.Scatter(
                x=data['date'],
                y=data['count'],
                mode='lines+markers',
                name=severity,
                stackgroup='one'
            ))
        
        fig.update_layout(title="Security Findings Over Time")
        return fig
    
    def generate_resource_heatmap(self):
        """Create resource risk heatmap."""
        pivot = self.df.pivot_table(
            index='resource_type',
            columns='severity',
            values='risk_score',
            aggfunc='sum',
            fill_value=0
        )
        
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=pivot.columns,
            y=pivot.index,
            colorscale='Reds'
        ))
        
        fig.update_layout(title="Resource Risk Heatmap")
        return fig
    
    def generate_full_dashboard(self, output_file="dashboard.html"):
        """Generate complete interactive dashboard."""
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Severity Distribution', 'Risk Timeline', 
                          'Resource Heatmap', 'Top Risks'),
            specs=[[{'type': 'pie'}, {'type': 'scatter'}],
                   [{'type': 'heatmap'}, {'type': 'bar'}]]
        )
        
        # Add all charts
        # ... (implementation details)
        
        # Save to HTML
        fig.write_html(output_file, include_plotlyjs='cdn')
        print(f"Dashboard saved to {output_file}")
```

### Custom Report Templates

```jinja2
{# executive_briefing.md.j2 #}
# Executive Security Briefing

**Date:** {{ metadata.generated_at | format_date }}  
**Prepared for:** {{ metadata.organization_name }}

## 🎯 Key Metrics

| Metric | Value | Change |
|--------|-------|---------|
| Risk Score | {{ summary.total_risk_score }} | {{ summary.risk_change }}% |
| Critical Findings | {{ summary.critical_count }} | {{ summary.critical_change }} |
| Compliance Score | {{ summary.compliance_score }}% | {{ summary.compliance_change }}% |

## 🚨 Immediate Actions Required

{% for finding in findings | selectattr('severity', 'equalto', 'CRITICAL') | list[:3] %}
### {{ loop.index }}. {{ finding.title }}
- **Impact:** {{ finding.business_impact }}
- **Estimated Fix Time:** {{ finding.remediation_effort }}
- **Owner:** {{ finding.assigned_to | default('Unassigned') }}
{% endfor %}

## 📊 Risk Trends

{{ chart_risk_trends | safe }}

## 🔒 Compliance Status

{% for framework in compliance_frameworks %}
### {{ framework.name }}
- **Score:** {{ framework.score }}%
- **Gap Analysis:** {{ framework.gaps | length }} controls need attention
- **Next Audit:** {{ framework.next_audit_date }}
{% endfor %}

## 📋 Recommendations

1. **Immediate (This Week)**
   {% for rec in recommendations.immediate %}
   - {{ rec }}
   {% endfor %}

2. **Short Term (This Month)**
   {% for rec in recommendations.short_term %}
   - {{ rec }}
   {% endfor %}

3. **Long Term (This Quarter)**
   {% for rec in recommendations.long_term %}
   - {{ rec }}
   {% endfor %}
```

## Continuous Monitoring

### Real-Time Alerting System

```python
# realtime_monitor.py

import asyncio
from datetime import datetime
import aiohttp
from google.cloud import securitycenter

class SecurityMonitor:
    """Real-time security monitoring system."""
    
    def __init__(self, project_id, webhook_url):
        self.project_id = project_id
        self.webhook_url = webhook_url
        self.scc_client = securitycenter.SecurityCenterClient()
        self.known_findings = set()
    
    async def check_new_findings(self):
        """Check for new security findings."""
        parent = f"projects/{self.project_id}/sources/-"
        
        findings = self.scc_client.list_findings(
            request={
                "parent": parent,
                "filter": 'state="ACTIVE"'
            }
        )
        
        new_findings = []
        for finding in findings:
            if finding.name not in self.known_findings:
                self.known_findings.add(finding.name)
                new_findings.append(finding)
        
        return new_findings
    
    async def send_alert(self, finding):
        """Send alert for new finding."""
        alert = {
            "text": f"🚨 New Security Finding",
            "attachments": [{
                "color": "danger" if finding.severity == "CRITICAL" else "warning",
                "title": finding.category,
                "text": finding.source_properties.get("explanation", ""),
                "fields": [
                    {"title": "Severity", "value": finding.severity, "short": True},
                    {"title": "Resource", "value": finding.resource_name, "short": True}
                ],
                "ts": int(datetime.now().timestamp())
            }]
        }
        
        async with aiohttp.ClientSession() as session:
            await session.post(self.webhook_url, json=alert)
    
    async def monitor_loop(self):
        """Main monitoring loop."""
        while True:
            try:
                new_findings = await self.check_new_findings()
                
                for finding in new_findings:
                    if finding.severity in ["CRITICAL", "HIGH"]:
                        await self.send_alert(finding)
                        
                        # Run Paddi analysis on the finding
                        await self.analyze_finding(finding)
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            # Check every 5 minutes
            await asyncio.sleep(300)
    
    async def analyze_finding(self, finding):
        """Run Paddi analysis on new finding."""
        # Convert finding to Paddi format
        paddi_data = {
            "scc_findings": [{
                "name": finding.name,
                "category": finding.category,
                "severity": finding.severity,
                "resource_name": finding.resource_name,
                "state": "ACTIVE"
            }]
        }
        
        # Run explainer
        from python_agents.explainer.agent_explainer import ExplainerAgent
        explainer = ExplainerAgent({"use_mock": False})
        
        enhanced_findings = explainer.analyze_scc_findings(paddi_data["scc_findings"])
        
        # Send enhanced analysis
        if enhanced_findings:
            await self.send_detailed_analysis(enhanced_findings[0])

# Start monitoring
monitor = SecurityMonitor("my-project", "https://hooks.slack.com/...")
asyncio.run(monitor.monitor_loop())
```

## Performance Optimization

### Distributed Auditing

```python
# distributed_audit.py

from celery import Celery
from python_agents.collector.agent_collector import CollectorAgent
from python_agents.explainer.agent_explainer import ExplainerAgent
from python_agents.reporter.agent_reporter import ReporterAgent

# Configure Celery
app = Celery('paddi', broker='redis://localhost:6379')

@app.task
def audit_project_task(project_id):
    """Celery task for auditing a single project."""
    # Collect
    collector = CollectorAgent({"project_id": project_id})
    collected_data = collector.collect()
    
    # Analyze
    explainer = ExplainerAgent({"project_id": project_id})
    findings = explainer.analyze(collected_data)
    
    # Report
    reporter = ReporterAgent({})
    reports = reporter.generate_reports(findings)
    
    return {
        "project_id": project_id,
        "findings_count": len(findings),
        "reports": reports
    }

# Distribute work across multiple workers
def audit_organization(org_id):
    """Audit entire organization using distributed workers."""
    projects = get_projects_in_org(org_id)
    
    # Create tasks
    job = group(audit_project_task.s(p) for p in projects)
    result = job.apply_async()
    
    # Wait for completion
    results = result.get()
    
    # Aggregate results
    return aggregate_org_results(results)
```

### Caching and Incremental Updates

```python
# incremental_audit.py

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path

class IncrementalAuditor:
    """Perform incremental audits with caching."""
    
    def __init__(self, cache_dir="./cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def get_resource_hash(self, resource):
        """Generate hash for resource state."""
        return hashlib.sha256(
            json.dumps(resource, sort_keys=True).encode()
        ).hexdigest()
    
    def is_cached(self, resource_id, resource_hash):
        """Check if resource analysis is cached."""
        cache_file = self.cache_dir / f"{resource_id}.json"
        
        if not cache_file.exists():
            return False
        
        cache_data = json.loads(cache_file.read_text())
        
        # Check if hash matches and cache is fresh
        if cache_data["hash"] == resource_hash:
            cached_time = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - cached_time < timedelta(days=7):
                return True
        
        return False
    
    def get_cached_findings(self, resource_id):
        """Retrieve cached findings."""
        cache_file = self.cache_dir / f"{resource_id}.json"
        data = json.loads(cache_file.read_text())
        return data["findings"]
    
    def cache_findings(self, resource_id, resource_hash, findings):
        """Cache analysis results."""
        cache_file = self.cache_dir / f"{resource_id}.json"
        cache_data = {
            "hash": resource_hash,
            "timestamp": datetime.now().isoformat(),
            "findings": findings
        }
        cache_file.write_text(json.dumps(cache_data))
    
    def audit_with_cache(self, resources):
        """Perform audit using cache where possible."""
        all_findings = []
        resources_to_analyze = []
        
        # Check cache for each resource
        for resource in resources:
            resource_id = resource["id"]
            resource_hash = self.get_resource_hash(resource)
            
            if self.is_cached(resource_id, resource_hash):
                # Use cached findings
                cached_findings = self.get_cached_findings(resource_id)
                all_findings.extend(cached_findings)
                print(f"Using cached analysis for {resource_id}")
            else:
                # Need fresh analysis
                resources_to_analyze.append(resource)
        
        # Analyze uncached resources
        if resources_to_analyze:
            print(f"Analyzing {len(resources_to_analyze)} resources...")
            explainer = ExplainerAgent({})
            new_findings = explainer.analyze({"resources": resources_to_analyze})
            
            # Cache new findings
            for resource, findings in zip(resources_to_analyze, new_findings):
                resource_id = resource["id"]
                resource_hash = self.get_resource_hash(resource)
                self.cache_findings(resource_id, resource_hash, findings)
            
            all_findings.extend(new_findings)
        
        return all_findings
```

## Integration with Security Tools

### SIEM Integration

```python
# siem_integration.py

import json
from datetime import datetime
import requests

class SIEMConnector:
    """Send Paddi findings to SIEM systems."""
    
    def __init__(self, siem_type, endpoint, api_key):
        self.siem_type = siem_type
        self.endpoint = endpoint
        self.api_key = api_key
    
    def format_for_splunk(self, finding):
        """Format finding for Splunk."""
        return {
            "time": datetime.now().timestamp(),
            "source": "paddi",
            "sourcetype": "security:finding",
            "event": {
                "severity": finding["severity"],
                "title": finding["title"],
                "category": finding["category"],
                "resource": finding["resource"],
                "risk_score": finding.get("risk_score", 0),
                "explanation": finding["explanation"],
                "recommendation": finding["recommendation"]
            }
        }
    
    def format_for_elastic(self, finding):
        """Format finding for Elasticsearch."""
        return {
            "@timestamp": datetime.now().isoformat(),
            "event.kind": "alert",
            "event.category": "security",
            "event.severity": self.severity_to_numeric(finding["severity"]),
            "paddi.finding": finding
        }
    
    def send_to_siem(self, findings):
        """Send findings to SIEM."""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        for finding in findings:
            if self.siem_type == "splunk":
                data = self.format_for_splunk(finding)
                endpoint = f"{self.endpoint}/services/collector/event"
            elif self.siem_type == "elastic":
                data = self.format_for_elastic(finding)
                endpoint = f"{self.endpoint}/_doc"
            
            response = requests.post(endpoint, json=data, headers=headers)
            
            if response.status_code != 200:
                print(f"Failed to send finding to SIEM: {response.text}")
```

### Jira Integration

```python
# jira_integration.py

from jira import JIRA

class JiraIntegration:
    """Create Jira tickets for security findings."""
    
    def __init__(self, server, username, token, project_key):
        self.jira = JIRA(server=server, basic_auth=(username, token))
        self.project_key = project_key
    
    def create_security_ticket(self, finding):
        """Create Jira ticket for finding."""
        # Determine priority based on severity
        priority_map = {
            "CRITICAL": "Highest",
            "HIGH": "High",
            "MEDIUM": "Medium",
            "LOW": "Low"
        }
        
        issue_dict = {
            'project': {'key': self.project_key},
            'summary': f"[Security] {finding['title']}",
            'description': self.format_description(finding),
            'issuetype': {'name': 'Security Issue'},
            'priority': {'name': priority_map.get(finding['severity'], 'Medium')},
            'labels': ['security', 'paddi', finding['category'].lower()],
            'customfield_10001': finding.get('risk_score', 0),  # Risk score field
        }
        
        # Create issue
        issue = self.jira.create_issue(fields=issue_dict)
        
        # Add remediation steps as subtasks
        if 'remediation_steps' in finding:
            for step in finding['remediation_steps']:
                self.create_subtask(issue, step)
        
        return issue.key
    
    def format_description(self, finding):
        """Format finding as Jira description."""
        return f"""
h3. Security Finding Details

*Severity:* {finding['severity']}
*Category:* {finding['category']}
*Resource:* {finding['resource']}

h3. Explanation
{finding['explanation']}

h3. Recommendation
{finding['recommendation']}

h3. References
{chr(10).join('* ' + ref for ref in finding.get('references', []))}

h3. Compliance Impact
{', '.join(finding.get('compliance_frameworks', []))}

_Generated by Paddi Security Audit_
"""
```

## Best Practices

1. **Automation Strategy**
   - Start with daily mock audits to test your setup
   - Gradually increase scope and frequency
   - Implement incremental auditing for large environments

2. **Performance Optimization**
   - Use caching for repeated analyses
   - Implement parallel processing for multiple projects
   - Consider distributed processing for organizations

3. **Integration Approach**
   - Start with simple webhook notifications
   - Add SIEM integration for centralized monitoring
   - Implement ticket creation for workflow integration

4. **Custom Policies**
   - Define organization-specific security policies
   - Regularly review and update policy rules
   - Balance between AI analysis and rule-based checks

5. **Monitoring and Alerting**
   - Set up real-time monitoring for critical resources
   - Define clear escalation paths
   - Automate initial response actions

## Next Steps

- Explore the [API Reference](../api/reference.md) for custom development
- Read [Security Best Practices](../security/best-practices.md)
- Join the community and share your advanced use cases