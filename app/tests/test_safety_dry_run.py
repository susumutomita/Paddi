"""Tests for the dry-run simulator module."""

import pytest
from app.safety.dry_run import DryRunSimulator
from app.safety.models import CommandType


class TestDryRunSimulator:
    """Test cases for DryRunSimulator."""
    
    @pytest.fixture
    def simulator(self):
        """Create a simulator instance."""
        return DryRunSimulator()
    
    def test_simulate_network_firewall_command(self, simulator):
        """Test simulation of firewall commands."""
        command = "firewall-cmd --permanent --remove-port=443/tcp"
        output = simulator.simulate_command(command, CommandType.NETWORK)
        
        assert "[DRY-RUN]" in output
        assert "443" in output
        assert "Service disruption expected" in output
        assert "web-server" in output or "api-gateway" in output
    
    def test_simulate_network_list_command(self, simulator):
        """Test simulation of firewall list command."""
        command = "firewall-cmd --list-all"
        output = simulator.simulate_command(command, CommandType.NETWORK)
        
        assert "[DRY-RUN]" in output
        assert "Current firewall configuration" in output
        assert "ports:" in output
        assert "services:" in output
    
    def test_simulate_permission_iam_command(self, simulator):
        """Test simulation of IAM commands."""
        command = 'gcloud projects remove-iam-policy-binding my-project --member="serviceAccount:app@project.iam.gserviceaccount.com" --role="roles/editor"'
        output = simulator.simulate_command(command, CommandType.PERMISSION)
        
        assert "[DRY-RUN]" in output
        assert "IAM policy modification" in output
        assert "roles/editor" in output
        assert "serviceAccount:app@project.iam.gserviceaccount.com" in output
        assert "Services affected" in output
    
    def test_simulate_permission_chmod_command(self, simulator):
        """Test simulation of chmod commands."""
        command = "chmod 000 /etc/config"
        output = simulator.simulate_command(command, CommandType.PERMISSION)
        
        assert "[DRY-RUN]" in output
        assert "file permission change" in output
        assert "755" in output  # Current permissions
        assert "Restrictive permissions may break services" in output
    
    def test_simulate_deletion_gsutil_command(self, simulator):
        """Test simulation of gsutil deletion."""
        command = "gsutil rm -r gs://my-bucket/data/"
        output = simulator.simulate_command(command, CommandType.DELETION)
        
        assert "[DRY-RUN]" in output
        assert "cloud storage deletion" in output
        assert "gs://my-bucket" in output
        assert "Files to be deleted" in output
        assert "NOT reversible" in output
        assert "backup" in output.lower()
    
    def test_simulate_deletion_rm_command(self, simulator):
        """Test simulation of rm command."""
        command = "rm -rf /var/log/*.log"
        output = simulator.simulate_command(command, CommandType.DELETION)
        
        assert "[DRY-RUN]" in output
        assert "file deletion" in output
        assert "Files matching pattern" in output
        assert "Force flag (-f)" in output
    
    def test_simulate_configuration_systemctl_command(self, simulator):
        """Test simulation of systemctl commands."""
        command = "systemctl stop nginx"
        output = simulator.simulate_command(command, CommandType.CONFIGURATION)
        
        assert "[DRY-RUN]" in output
        assert "service stop" in output
        assert "nginx" in output
        assert "Current status: active" in output
        assert "Dependent services" in output
        assert "systemctl start nginx" in output
    
    def test_simulate_readonly_command(self, simulator):
        """Test simulation of read-only commands."""
        command = "gcloud projects list"
        output = simulator.simulate_command(command, CommandType.READ_ONLY)
        
        assert "[DRY-RUN]" in output
        assert "Read-only command" in output
        assert "safe to execute" in output
        assert "No system changes" in output
    
    def test_simulate_unknown_command(self, simulator):
        """Test simulation of unknown commands."""
        command = "custom-tool --dangerous-flag"
        output = simulator.simulate_command(command, CommandType.UNKNOWN)
        
        assert "[DRY-RUN]" in output
        assert "Unknown command pattern" in output
        assert "manual review" in output
        assert "Check command documentation" in output
    
    def test_extract_port_from_command(self, simulator):
        """Test port extraction from firewall commands."""
        test_cases = [
            ("firewall-cmd --remove-port=443/tcp", "443"),
            ("firewall-cmd --remove-port 80/tcp", "80"),
            ("firewall-cmd --remove-port=8080/udp", "8080"),
            ("firewall-cmd --list-all", "unknown"),
        ]
        
        for command, expected_port in test_cases:
            port = simulator._extract_port(command)
            assert port == expected_port
    
    def test_extract_member_from_iam_command(self, simulator):
        """Test member extraction from IAM commands."""
        test_cases = [
            (
                '--member="serviceAccount:app@project.iam.gserviceaccount.com"',
                "serviceAccount:app@project.iam.gserviceaccount.com"
            ),
            (
                "--member='user:admin@example.com'",
                "user:admin@example.com"
            ),
            (
                "--member=group:devs@example.com",  # Without quotes
                "unknown-member"
            ),
        ]
        
        for command_part, expected_member in test_cases:
            member = simulator._extract_member(f"gcloud command {command_part}")
            assert member == expected_member
    
    def test_extract_service_from_systemctl(self, simulator):
        """Test service extraction from systemctl commands."""
        test_cases = [
            ("systemctl stop nginx", "nginx"),
            ("systemctl disable postgresql.service", "postgresql"),
            ("systemctl restart docker", "docker"),
            ("systemctl status", "unknown-service"),
        ]
        
        for command, expected_service in test_cases:
            service = simulator._extract_service(command)
            assert service == expected_service