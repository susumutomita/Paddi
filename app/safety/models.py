"""Safety models for risk assessment and validation."""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class RiskLevel(Enum):
    """Risk levels for command assessment."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CommandType(Enum):
    """Types of commands based on their impact."""
    READ_ONLY = "read_only"
    CONFIGURATION = "configuration"
    PERMISSION = "permission"
    DELETION = "deletion"
    NETWORK = "network"
    UNKNOWN = "unknown"


class ApprovalStatus(Enum):
    """Status of human approval for commands."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    AUTO_APPROVED = "auto_approved"


@dataclass
class CommandValidation:
    """Result of command validation."""
    command: str
    is_safe: bool
    risk_level: RiskLevel
    command_type: CommandType
    risks: List[str]
    warnings: List[str]
    requires_approval: bool
    dry_run_output: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "is_safe": self.is_safe,
            "risk_level": self.risk_level.value,
            "command_type": self.command_type.value,
            "risks": self.risks,
            "warnings": self.warnings,
            "requires_approval": self.requires_approval,
            "dry_run_output": self.dry_run_output
        }


@dataclass
class ImpactAnalysis:
    """Analysis of command impact on the system."""
    command: str
    affected_resources: List[str]
    affected_services: List[str]
    estimated_downtime: Optional[str]
    reversible: bool
    rollback_command: Optional[str]
    data_loss_risk: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "affected_resources": self.affected_resources,
            "affected_services": self.affected_services,
            "estimated_downtime": self.estimated_downtime,
            "reversible": self.reversible,
            "rollback_command": self.rollback_command,
            "data_loss_risk": self.data_loss_risk
        }


@dataclass
class ApprovalRequest:
    """Request for human approval of a command."""
    id: str
    command: str
    validation: CommandValidation
    impact_analysis: ImpactAnalysis
    requested_at: datetime
    requested_by: str
    status: ApprovalStatus
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "command": self.command,
            "validation": self.validation.to_dict(),
            "impact_analysis": self.impact_analysis.to_dict(),
            "requested_at": self.requested_at.isoformat(),
            "requested_by": self.requested_by,
            "status": self.status.value,
            "approved_by": self.approved_by,
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "rejection_reason": self.rejection_reason
        }


@dataclass
class AuditLogEntry:
    """Audit log entry for command execution."""
    id: str
    timestamp: datetime
    command: str
    executed_by: str
    validation_result: CommandValidation
    impact_analysis: Optional[ImpactAnalysis]
    approval: Optional[ApprovalRequest]
    execution_result: Optional[str]
    execution_error: Optional[str]
    dry_run: bool
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "command": self.command,
            "executed_by": self.executed_by,
            "validation_result": self.validation_result.to_dict(),
            "impact_analysis": self.impact_analysis.to_dict() if self.impact_analysis else None,
            "approval": self.approval.to_dict() if self.approval else None,
            "execution_result": self.execution_result,
            "execution_error": self.execution_error,
            "dry_run": self.dry_run
        }