"""Example integration of error handling into existing Paddi components."""

from typing import Any, Dict, List

from app.collector.agent_collector import Collector
from app.error_handling.decorators import auto_retry, with_self_healing
from app.error_handling.intelligent_handler import SelfHealingSystem
from app.error_handling.specific_handlers import ErrorHandlerRegistry
from app.explainer.agent_explainer import GeminiExplainer
from app.log.logger import get_logger
from app.memory.context_manager import ContextualMemory

logger = get_logger(__name__)


class ErrorAwareCollector(Collector):
    """Enhanced collector with self-healing capabilities."""

    def __init__(self, project_id: str):
        super().__init__(project_id)
        self.memory = ContextualMemory(project_id=project_id)
        self.healing_system = SelfHealingSystem(self.memory)

    @with_self_healing(max_retries=3)
    async def collect_iam_policies(self) -> Dict[str, Any]:
        """Collect IAM policies with automatic error recovery."""
        return await super().collect_iam_policies()

    @auto_retry(max_attempts=3, delay=2.0, exceptions=(Exception,))
    async def collect_scc_findings(self) -> List[Dict[str, Any]]:
        """Collect SCC findings with automatic retry."""
        return await super().collect_scc_findings()


class ErrorAwareExplainer(GeminiExplainer):
    """Enhanced explainer with intelligent error handling."""

    def __init__(self, project_id: str, location: str = "us-central1"):
        super().__init__(project_id, location)
        self.memory = ContextualMemory(project_id=project_id)
        self.error_registry = ErrorHandlerRegistry()

    @with_self_healing(
        max_retries=3,
        error_types=[Exception],  # Handle all exceptions
        fallback=lambda self, findings: self._offline_analysis(findings)
    )
    async def analyze_findings(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analyze findings with self-healing and fallback to offline analysis."""
        return await super().analyze_findings(findings)

    async def _offline_analysis(self, findings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback offline analysis when AI service is unavailable."""
        logger.warning("Using offline analysis due to AI service unavailability")
        
        results = []
        for finding in findings:
            # Basic rule-based analysis
            severity = "HIGH" if "owner" in str(finding).lower() else "MEDIUM"
            
            results.append({
                "title": finding.get("name", "Unknown Finding"),
                "severity": severity,
                "explanation": "Offline analysis: Potential security risk detected",
                "recommendation": "Manual review required when AI service is available",
                "offline_analysis": True
            })
        
        return results


def integrate_error_handling_into_cli():
    """Example of integrating error handling into CLI commands."""
    from app.cli.paddi_cli import PaddiCLI
    
    # Monkey patch existing methods with error handling
    original_audit = PaddiCLI.audit
    
    @with_self_healing(max_retries=2)
    async def enhanced_audit(self, project_id: str = None):
        """Enhanced audit with self-healing."""
        try:
            return await original_audit(self, project_id)
        except Exception as e:
            logger.error(f"Audit failed: {e}")
            # Provide helpful error guidance
            error_registry = ErrorHandlerRegistry()
            
            # Analyze error type
            if "permission" in str(e).lower():
                guidance = await error_registry.handle_specific_error(
                    "permission", e, {"resource_type": "audit"}
                )
                logger.info(f"Permission guidance: {guidance}")
            elif "rate limit" in str(e).lower():
                guidance = await error_registry.handle_specific_error(
                    "api_limit", e, {"service": "gcp"}
                )
                logger.info(f"Rate limit guidance: {guidance}")
            
            raise
    
    # Replace with enhanced version
    PaddiCLI.audit = enhanced_audit


# Example usage in scripts
async def example_resilient_audit():
    """Example of using error-aware components."""
    project_id = "my-project"
    
    # Initialize components with error handling
    collector = ErrorAwareCollector(project_id)
    explainer = ErrorAwareExplainer(project_id)
    
    try:
        # Collect with automatic retry and recovery
        logger.info("Starting resilient collection...")
        collected_data = await collector.collect()
        
        # Analyze with fallback to offline analysis
        logger.info("Analyzing findings...")
        analysis_results = await explainer.analyze_findings(
            collected_data.get("findings", [])
        )
        
        # Check if offline analysis was used
        if any(r.get("offline_analysis") for r in analysis_results):
            logger.warning(
                "Some results were generated using offline analysis. "
                "Re-run when AI service is available for better results."
            )
        
        return analysis_results
        
    except Exception as e:
        # Even with all recovery attempts, some errors might not be recoverable
        logger.error(f"Unrecoverable error during audit: {e}")
        
        # Get healing statistics for debugging
        if hasattr(collector, 'healing_system'):
            stats = collector.healing_system.get_healing_statistics()
            logger.info(f"Healing statistics: {stats}")
        
        raise


# Configuration example for different environments
ERROR_HANDLING_CONFIG = {
    "development": {
        "max_retries": 5,
        "retry_delay": 1.0,
        "enable_learning": True,
        "verbose_logging": True
    },
    "production": {
        "max_retries": 3,
        "retry_delay": 5.0,
        "enable_learning": True,
        "verbose_logging": False
    },
    "testing": {
        "max_retries": 1,
        "retry_delay": 0.1,
        "enable_learning": False,
        "verbose_logging": True
    }
}


def get_error_handling_config(environment: str = "development") -> Dict[str, Any]:
    """Get error handling configuration for environment."""
    return ERROR_HANDLING_CONFIG.get(environment, ERROR_HANDLING_CONFIG["development"])