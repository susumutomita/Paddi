"""Command validation to prevent dangerous operations."""

import re
from typing import List

from app.safety.models import CommandType, CommandValidation, RiskLevel


class SafetyValidator:
    """Validates commands for safety risks."""

    # Dangerous command patterns
    DANGEROUS_PATTERNS = {
        # Network operations
        r"firewall-cmd.*--remove-(port|service)": (
            RiskLevel.CRITICAL,
            CommandType.NETWORK,
            "Removing firewall rules can block critical services",
        ),
        r"iptables.*-D|--delete": (
            RiskLevel.HIGH,
            CommandType.NETWORK,
            "Deleting iptables rules can disrupt network connectivity",
        ),
        # Permission operations
        r"gcloud.*remove-iam-policy-binding": (
            RiskLevel.HIGH,
            CommandType.PERMISSION,
            "Removing IAM bindings can break service authentication",
        ),
        r"chmod.*-R.*000": (
            RiskLevel.CRITICAL,
            CommandType.PERMISSION,
            "Setting permissions to 000 makes resources inaccessible",
        ),
        # Deletion operations
        r"gsutil\s+rm\s+-r": (
            RiskLevel.CRITICAL,
            CommandType.DELETION,
            "Recursive deletion of cloud storage can cause data loss",
        ),
        r"rm\s+-rf\s+/": (
            RiskLevel.CRITICAL,
            CommandType.DELETION,
            "Recursive force deletion from root is extremely dangerous",
        ),
        r"gcloud.*delete.*--quiet": (
            RiskLevel.HIGH,
            CommandType.DELETION,
            "Quiet deletion bypasses confirmation prompts",
        ),
        # Configuration changes
        r"systemctl\s+(stop|disable)": (
            RiskLevel.MEDIUM,
            CommandType.CONFIGURATION,
            "Stopping or disabling services can affect availability",
        ),
    }

    # Safe command patterns
    SAFE_PATTERNS = {
        r"gcloud.*list": CommandType.READ_ONLY,
        r"gsutil\s+ls": CommandType.READ_ONLY,
        r"kubectl\s+get": CommandType.READ_ONLY,
        r"systemctl\s+status": CommandType.READ_ONLY,
        r"cat\s+": CommandType.READ_ONLY,
        r"echo\s+": CommandType.READ_ONLY,
    }

    # Medium risk patterns (not in DANGEROUS_PATTERNS but not safe)
    MEDIUM_RISK_PATTERNS = {
        r"systemctl\s+restart": (
            RiskLevel.MEDIUM,
            CommandType.CONFIGURATION,
            "Restarting services can cause temporary unavailability",
        ),
    }

    # Required approval patterns
    APPROVAL_REQUIRED_PATTERNS = [
        r".*production.*",
        r".*prod-.*",
        r".*critical.*",
        r".*delete.*",
        r".*remove.*",
        r".*DROP\s+TABLE.*",
        r".*TRUNCATE.*",
    ]

    def __init__(self):
        """Initialize the validator."""
        # Merge DANGEROUS_PATTERNS and MEDIUM_RISK_PATTERNS
        all_risk_patterns = {**self.DANGEROUS_PATTERNS, **self.MEDIUM_RISK_PATTERNS}
        self.dangerous_regex = {
            re.compile(pattern, re.IGNORECASE): info for pattern, info in all_risk_patterns.items()
        }
        self.safe_regex = {
            re.compile(pattern, re.IGNORECASE): cmd_type
            for pattern, cmd_type in self.SAFE_PATTERNS.items()
        }
        self.approval_regex = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.APPROVAL_REQUIRED_PATTERNS
        ]

    def validate_command(self, command: str) -> CommandValidation:
        """Validate a command for safety risks."""
        risks = []
        warnings = []
        risk_level = RiskLevel.LOW
        command_type = CommandType.UNKNOWN
        requires_approval = False

        # Check against dangerous patterns
        for pattern, (level, cmd_type, risk_msg) in self.dangerous_regex.items():
            if pattern.search(command):
                risks.append(risk_msg)
                risk_level = max(level, risk_level)
                command_type = cmd_type

        # Check if it's a safe command
        for pattern, cmd_type in self.safe_regex.items():
            if pattern.search(command):
                command_type = cmd_type
                if not risks:  # Only mark as low risk if no dangers found
                    risk_level = RiskLevel.LOW
                break

        # Check if approval is required
        for pattern in self.approval_regex:
            if pattern.search(command):
                requires_approval = True
                warnings.append("This command affects production or critical resources")
                break

        # Additional checks
        self._check_resource_names(command, warnings)
        self._check_wildcards(command, warnings)

        # Determine if command is safe
        is_safe = risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM] and not risks

        # High risk commands always require approval
        if risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            requires_approval = True

        return CommandValidation(
            command=command,
            is_safe=is_safe,
            risk_level=risk_level,
            command_type=command_type,
            risks=risks,
            warnings=warnings,
            requires_approval=requires_approval,
        )

    def _check_resource_names(self, command: str, warnings: List[str]) -> None:
        """Check for suspicious resource names."""
        suspicious_patterns = [
            (r"test[^a-zA-Z]", "Command appears to target test resources"),
            (r"temp[^a-zA-Z]", "Command appears to target temporary resources"),
            (r"backup[^a-zA-Z]", "Command appears to target backup resources"),
        ]

        for pattern, warning in suspicious_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                warnings.append(warning)

    def _check_wildcards(self, command: str, warnings: List[str]) -> None:
        """Check for dangerous wildcard usage."""
        if "*" in command:
            warnings.append("Command contains wildcards which may affect multiple resources")
        if "?" in command:
            warnings.append("Command contains single-character wildcards")

    def get_safe_alternatives(self, command: str) -> List[str]:
        """Suggest safer alternatives for dangerous commands."""
        alternatives = []

        # Firewall alternatives
        if re.search(r"firewall-cmd.*--remove", command):
            alternatives.append(
                "Consider using '--add-rich-rule' with reject action instead of removing rules"
            )
            alternatives.append("Use '--list-all' first to verify current rules")

        # IAM alternatives
        if "remove-iam-policy-binding" in command:
            alternatives.append("Use 'get-iam-policy' first to review current bindings")
            alternatives.append("Consider using more restrictive roles instead of removing access")

        # Deletion alternatives
        if re.search(r"(rm|delete).*-[rf]", command):
            alternatives.append("Use '--dry-run' flag if available")
            alternatives.append("Consider moving to a backup location instead of deleting")
            alternatives.append("List files first before deletion")

        return alternatives
