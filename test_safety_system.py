#!/usr/bin/env python3
"""Quick test script to verify the safety system is working correctly."""

import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.main import PaddiCLI
from app.safety.models import RiskLevel, ApprovalStatus


def test_safety_system():
    """Run basic tests to verify safety system functionality."""
    print("🧪 Testing Paddi Safety System...\n")
    
    # Initialize CLI
    cli = PaddiCLI()
    print("✅ CLI initialized with safety system")
    
    # Test 1: Safe command validation
    print("\n📝 Test 1: Validating safe command...")
    command = "gcloud projects list"
    is_safe, message, approval = cli.safety_check.validate_command(
        command=command,
        user="test-user",
        dry_run=True
    )
    assert is_safe, "Safe command should be validated"
    assert "Safe to execute" in message
    print(f"✅ Safe command validated correctly: {command}")
    
    # Test 2: Dangerous command detection
    print("\n📝 Test 2: Detecting dangerous command...")
    command = "firewall-cmd --permanent --remove-port=443/tcp"
    is_safe, message, approval = cli.safety_check.validate_command(
        command=command,
        user="test-user",
        dry_run=True
    )
    assert not is_safe, "Dangerous command should be flagged"
    assert approval is not None, "Should require approval"
    assert approval.validation.risk_level == RiskLevel.CRITICAL
    print(f"✅ Dangerous command detected: {command}")
    print(f"   Risk level: {approval.validation.risk_level.value}")
    
    # Test 3: Dry-run simulation
    print("\n📝 Test 3: Testing dry-run simulation...")
    success, result = cli.safety_check.execute_command(
        command="systemctl stop nginx",
        user="test-user",
        dry_run=True
    )
    assert success, "Dry-run should succeed"
    assert "DRY-RUN MODE" in result
    print("✅ Dry-run simulation working correctly")
    
    # Test 4: Approval workflow
    print("\n📝 Test 4: Testing approval workflow...")
    # Create approval request
    command = "rm -rf /test-data"
    is_safe, message, approval_request = cli.safety_check.validate_command(
        command=command,
        user="test-user",
        dry_run=True
    )
    
    if approval_request and approval_request.status == ApprovalStatus.PENDING:
        # Approve it
        approved = cli.safety_check.approve_command(
            approval_request.id,
            "admin-user"
        )
        assert approved.status == ApprovalStatus.APPROVED
        print("✅ Approval workflow working correctly")
        print(f"   Command approved by: {approved.approved_by}")
    
    # Test 5: Audit logging
    print("\n📝 Test 5: Testing audit logging...")
    logs = cli.safety_check.search_audit_logs(user="test-user")
    assert len(logs) > 0, "Should have audit logs"
    print(f"✅ Audit logging working correctly")
    print(f"   Found {len(logs)} audit log entries")
    
    # Test 6: Impact analysis
    print("\n📝 Test 6: Testing impact analysis...")
    command = "gsutil rm -r gs://production-bucket/"
    validation = cli.safety_check.validator.validate_command(command)
    impact = cli.safety_check.impact_analyzer.analyze_impact(
        command,
        validation.command_type,
        validation.risk_level
    )
    assert impact.data_loss_risk, "Should identify data loss risk"
    assert not impact.reversible, "Should identify as irreversible"
    assert len(impact.affected_resources) > 0
    print("✅ Impact analysis working correctly")
    print(f"   Data loss risk: {impact.data_loss_risk}")
    print(f"   Reversible: {impact.reversible}")
    print(f"   Affected resources: {len(impact.affected_resources)}")
    
    print("\n✨ All safety system tests passed!")
    print("\nSafety Features Summary:")
    print("- Command validation with risk assessment")
    print("- Dry-run simulation for safe testing")
    print("- Human approval workflow for high-risk commands")
    print("- Comprehensive audit logging")
    print("- Impact analysis with rollback suggestions")
    print("- Integration with Paddi CLI")
    
    return True


def main():
    """Run the test."""
    try:
        success = test_safety_system()
        if success:
            print("\n🎉 Safety system is working correctly!")
            sys.exit(0)
        else:
            print("\n❌ Safety system tests failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error testing safety system: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()