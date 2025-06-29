# Paddi API Integration Layer

This module provides the integration layer between the Paddi CLI agents and the web dashboard.

## Components

### AgentManager (`agent_manager.py`)
- Orchestrates the execution of collector, explainer, and reporter agents
- Manages audit state and tracks execution progress
- Provides methods to retrieve findings and audit status
- Handles error conditions gracefully

### AsyncExecutor (`async_executor.py`)
- Provides asynchronous execution using ThreadPoolExecutor
- Prevents multiple concurrent audits with the same ID
- Tracks running tasks and provides status updates
- Handles cleanup of completed tasks

## Usage

### Starting an Audit

```python
from app.api.agent_manager import AgentManager
from app.api.async_executor import AsyncExecutor

# Initialize
agent_manager = AgentManager()
async_executor = AsyncExecutor()

# Start audit
audit_id = agent_manager.start_audit(
    project_id="my-project",
    use_mock=True,
    location="us-central1"
)

# Run asynchronously
async_executor.submit_audit(
    audit_id,
    agent_manager.run_audit_sync,
    audit_id
)
```

### Checking Status

```python
# Check if still running
is_running = async_executor.is_running(audit_id)

# Get audit details
audit = agent_manager.get_audit_status(audit_id)
print(f"Status: {audit['status']}")
```

### Retrieving Findings

```python
# Get findings from explained.json
findings = agent_manager.get_findings()
if findings:
    print(f"Total findings: {findings['total']}")
    for finding in findings['findings']:
        print(f"- {finding['title']} ({finding['severity']})")
```

## Integration with Flask

The web dashboard (`web/app.py`) uses these components to:
1. Start audits via `/api/audit/start`
2. Check status via `/api/audit/status/<audit_id>`
3. Retrieve findings via `/api/findings`
4. Show severity distribution via `/api/findings/severity-distribution`

## Testing

Run tests with:
```bash
python -m pytest app/tests/test_agent_manager.py
python -m pytest app/tests/test_async_executor.py
```