"""Impact analysis for commands to understand potential consequences."""

import re
from typing import List, Optional
from app.safety.models import ImpactAnalysis, CommandType, RiskLevel


class ImpactAnalyzer:
    """Analyzes the potential impact of commands on the system."""
    
    def __init__(self):
        """Initialize the impact analyzer."""
        self.resource_patterns = {
            'gcp_project': re.compile(r'projects?[/=]\s*([a-z][-a-z0-9]{4,28}[a-z0-9])', re.IGNORECASE),
            'gcp_bucket': re.compile(r'gs://([^/\s]+)', re.IGNORECASE),
            'gcp_instance': re.compile(r'instances?[/=]\s*([a-z][-a-z0-9]*)', re.IGNORECASE),
            'service_account': re.compile(r'serviceAccount:([^@]+@[^\.]+\.iam\.gserviceaccount\.com)', re.IGNORECASE),
            'iam_role': re.compile(r'roles?/([a-zA-Z0-9\._]+)', re.IGNORECASE),
            'firewall_port': re.compile(r'port[= ](\d+)', re.IGNORECASE),
            'system_service': re.compile(r'(nginx|apache|mysql|postgresql|redis|docker)', re.IGNORECASE),
        }
    
    def analyze_impact(self, command: str, command_type: CommandType, risk_level: RiskLevel) -> ImpactAnalysis:
        """Analyze the potential impact of a command."""
        affected_resources = self._identify_affected_resources(command)
        affected_services = self._identify_affected_services(command, command_type)
        downtime = self._estimate_downtime(command_type, risk_level)
        reversible = self._is_reversible(command, command_type)
        rollback_cmd = self._generate_rollback_command(command, command_type) if reversible else None
        data_loss_risk = self._assess_data_loss_risk(command, command_type)
        
        return ImpactAnalysis(
            command=command,
            affected_resources=affected_resources,
            affected_services=affected_services,
            estimated_downtime=downtime,
            reversible=reversible,
            rollback_command=rollback_cmd,
            data_loss_risk=data_loss_risk
        )
    
    def _identify_affected_resources(self, command: str) -> List[str]:
        """Identify resources that would be affected by the command."""
        resources = []
        
        for resource_type, pattern in self.resource_patterns.items():
            matches = pattern.findall(command)
            for match in matches:
                resources.append(f"{resource_type}: {match}")
        
        # Check for wildcard operations
        if '*' in command:
            resources.append("Multiple resources (wildcard operation)")
        
        return resources
    
    def _identify_affected_services(self, command: str, command_type: CommandType) -> List[str]:
        """Identify services that would be affected."""
        services = []
        
        # Service-specific patterns
        service_indicators = {
            'web': ['nginx', 'apache', 'httpd', '80', '443', 'web'],
            'database': ['mysql', 'postgresql', 'postgres', 'mongodb', '3306', '5432'],
            'cache': ['redis', 'memcached', '6379', '11211'],
            'container': ['docker', 'kubernetes', 'k8s', 'container'],
            'storage': ['storage', 'bucket', 'gs://', 's3://', 'blob'],
            'compute': ['compute', 'instance', 'vm', 'server'],
            'network': ['firewall', 'vpc', 'subnet', 'route', 'load-balancer'],
        }
        
        command_lower = command.lower()
        for service_type, indicators in service_indicators.items():
            if any(indicator in command_lower for indicator in indicators):
                services.append(service_type)
        
        # Command type specific services
        if command_type == CommandType.NETWORK:
            services.extend(['networking', 'connectivity'])
        elif command_type == CommandType.PERMISSION:
            services.extend(['authentication', 'authorization'])
        
        return list(set(services))  # Remove duplicates
    
    def _estimate_downtime(self, command_type: CommandType, risk_level: RiskLevel) -> Optional[str]:
        """Estimate potential downtime based on command type and risk."""
        downtime_matrix = {
            CommandType.NETWORK: {
                RiskLevel.LOW: None,
                RiskLevel.MEDIUM: "Brief connectivity interruption (< 1 minute)",
                RiskLevel.HIGH: "5-15 minutes",
                RiskLevel.CRITICAL: "15-60 minutes or until manual intervention",
            },
            CommandType.PERMISSION: {
                RiskLevel.LOW: None,
                RiskLevel.MEDIUM: "Service restart required (1-5 minutes)",
                RiskLevel.HIGH: "10-30 minutes for permission propagation",
                RiskLevel.CRITICAL: "Indefinite until permissions restored",
            },
            CommandType.DELETION: {
                RiskLevel.LOW: None,
                RiskLevel.MEDIUM: None,
                RiskLevel.HIGH: "Permanent - restoration from backup required",
                RiskLevel.CRITICAL: "Permanent - potential complete data loss",
            },
            CommandType.CONFIGURATION: {
                RiskLevel.LOW: None,
                RiskLevel.MEDIUM: "Service restart (1-5 minutes)",
                RiskLevel.HIGH: "5-15 minutes",
                RiskLevel.CRITICAL: "System reboot may be required (10-30 minutes)",
            },
        }
        
        return downtime_matrix.get(command_type, {}).get(risk_level)
    
    def _is_reversible(self, command: str, command_type: CommandType) -> bool:
        """Determine if a command's effects can be reversed."""
        # Deletions are generally not reversible
        if command_type == CommandType.DELETION:
            return 'backup' in command.lower() or 'archive' in command.lower()
        
        # Network and permission changes are usually reversible
        if command_type in [CommandType.NETWORK, CommandType.PERMISSION]:
            return True
        
        # Configuration changes depend on the specific command
        if command_type == CommandType.CONFIGURATION:
            return 'disable' not in command.lower()
        
        return True  # Assume reversible unless proven otherwise
    
    def _generate_rollback_command(self, command: str, command_type: CommandType) -> Optional[str]:
        """Generate a rollback command if possible."""
        rollback_mappings = {
            # Firewall rules
            r'firewall-cmd.*--remove-port[= ](\d+/\w+)': r'firewall-cmd --permanent --add-port=\1',
            r'firewall-cmd.*--remove-service[= ](\w+)': r'firewall-cmd --permanent --add-service=\1',
            
            # IAM bindings
            r'gcloud.*remove-iam-policy-binding.*--member[= ]["\'](.*?)["\'].*--role[= ]["\'](.*?)["\']': 
                r'gcloud projects add-iam-policy-binding PROJECT_ID --member="\1" --role="\2"',
            
            # System services
            r'systemctl stop (\S+)': r'systemctl start \1',
            r'systemctl disable (\S+)': r'systemctl enable \1',
            
            # File permissions
            r'chmod (\d+) (.+)': 'chmod [ORIGINAL_PERMISSIONS] \2  # Note: Original permissions need to be determined',
        }
        
        for pattern, rollback in rollback_mappings.items():
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                return match.expand(rollback)
        
        return None
    
    def _assess_data_loss_risk(self, command: str, command_type: CommandType) -> bool:
        """Assess if the command risks data loss."""
        if command_type == CommandType.DELETION:
            return True
        
        # Check for destructive patterns
        destructive_patterns = [
            r'DROP\s+TABLE',
            r'TRUNCATE',
            r'DELETE\s+FROM',
            r'>\s*[^>]',  # Overwrite redirection
            r'format|mkfs',  # Filesystem formatting
        ]
        
        for pattern in destructive_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        
        return False
    
    def get_mitigation_suggestions(self, impact: ImpactAnalysis) -> List[str]:
        """Provide suggestions to mitigate the impact."""
        suggestions = []
        
        if impact.data_loss_risk:
            suggestions.append("Create a backup before executing this command")
            suggestions.append("Consider using versioning or soft-delete options")
        
        if impact.estimated_downtime:
            suggestions.append("Schedule during maintenance window")
            suggestions.append("Notify affected users before execution")
            suggestions.append("Have rollback plan ready")
        
        if not impact.reversible:
            suggestions.append("Document current state before making changes")
            suggestions.append("Test in non-production environment first")
        
        if len(impact.affected_services) > 2:
            suggestions.append("Consider breaking into smaller, isolated changes")
            suggestions.append("Monitor all affected services during execution")
        
        return suggestions