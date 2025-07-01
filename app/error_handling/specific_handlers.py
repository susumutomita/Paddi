"""Specific error handlers for common patterns."""

import asyncio
import os
from typing import Any, Dict, Optional

from app.log.logger import get_logger

logger = get_logger(__name__)


class APILimitHandler:
    """Handles API rate limit and quota errors."""

    def __init__(self):
        self.retry_delays = {
            "gemini": 60,  # 1 minute for Gemini API
            "gcp": 15,     # 15 seconds for GCP APIs
            "default": 30   # Default 30 seconds
        }
        self.quota_reset_times = {}

    async def handle_rate_limit(self, service: str, error: Exception) -> Dict[str, Any]:
        """Handle rate limit error with smart retry."""
        error_msg = str(error).lower()
        
        # Extract retry-after header if available
        retry_after = self._extract_retry_after(error_msg)
        if retry_after:
            wait_time = retry_after
        else:
            wait_time = self.retry_delays.get(service, self.retry_delays["default"])
        
        logger.info(f"⏳ API制限エラー: {wait_time}秒待機します...")
        
        return {
            "action": "retry",
            "wait_time": wait_time,
            "message": f"API制限により{wait_time}秒後に再試行します",
            "alternative": self._suggest_alternative_endpoint(service)
        }

    def _extract_retry_after(self, error_msg: str) -> Optional[int]:
        """Extract retry-after value from error message."""
        import re
        match = re.search(r'retry[- ]?after[:\s]+(\d+)', error_msg, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return None

    def _suggest_alternative_endpoint(self, service: str) -> Optional[str]:
        """Suggest alternative endpoint if available."""
        alternatives = {
            "gemini": "gemini-1.5-flash の代わりに gemini-1.5-pro を使用",
            "gcp": "別のリージョンのエンドポイントを使用"
        }
        return alternatives.get(service)


class PermissionHandler:
    """Handles permission and authentication errors."""

    def __init__(self):
        self.required_roles = {
            "compute": ["roles/compute.viewer", "roles/compute.admin"],
            "storage": ["roles/storage.objectViewer", "roles/storage.admin"],
            "iam": ["roles/iam.securityReviewer", "roles/iam.admin"],
            "securitycenter": ["roles/securitycenter.findingsViewer"]
        }

    async def handle_permission_error(self, resource_type: str, 
                                    error: Exception) -> Dict[str, Any]:
        """Handle permission error with specific guidance."""
        error_msg = str(error)
        
        # Identify missing permission
        missing_permission = self._identify_missing_permission(error_msg)
        required_roles = self.required_roles.get(resource_type, [])
        
        # Generate fix command
        fix_command = self._generate_fix_command(resource_type, missing_permission)
        
        return {
            "error_type": "permission",
            "missing_permission": missing_permission,
            "required_roles": required_roles,
            "fix_commands": [fix_command] if fix_command else [],
            "manual_steps": [
                f"1. プロジェクトの管理者に連絡してください",
                f"2. 以下のロールのいずれかを付与してもらってください: {', '.join(required_roles)}",
                f"3. または、以下のコマンドを実行してください:",
                f"   {fix_command}" if fix_command else ""
            ]
        }

    def _identify_missing_permission(self, error_msg: str) -> Optional[str]:
        """Extract missing permission from error message."""
        import re
        # Common patterns for GCP permission errors
        patterns = [
            r"requires\s+(?:the\s+)?([a-zA-Z.]+)\s+permission",
            r"missing\s+permission\s+([a-zA-Z.]+)",
            r"denied\s+on\s+\'([a-zA-Z.]+)\'"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_msg, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _generate_fix_command(self, resource_type: str, 
                            permission: Optional[str]) -> Optional[str]:
        """Generate gcloud command to fix permission."""
        if not permission:
            return None
        
        # Get project ID from environment or config
        project_id = os.getenv("GCP_PROJECT_ID", "YOUR_PROJECT_ID")
        service_account = os.getenv("SERVICE_ACCOUNT_EMAIL", "YOUR_SERVICE_ACCOUNT")
        
        # Map permission to role
        role = None
        if resource_type in self.required_roles:
            role = self.required_roles[resource_type][0]  # Use viewer role by default
        
        if role:
            return (
                f"gcloud projects add-iam-policy-binding {project_id} "
                f"--member='serviceAccount:{service_account}' "
                f"--role='{role}'"
            )
        return None


class NetworkErrorHandler:
    """Handles network and connectivity errors."""

    def __init__(self):
        self.connection_checks = [
            ("Google DNS", "8.8.8.8"),
            ("Cloudflare DNS", "1.1.1.1"),
            ("GCP Endpoint", "googleapis.com")
        ]

    async def handle_network_error(self, error: Exception) -> Dict[str, Any]:
        """Handle network error with diagnostics."""
        error_msg = str(error).lower()
        
        # Perform connectivity checks
        connectivity = await self._check_connectivity()
        
        # Determine if it's a proxy issue
        proxy_issue = self._detect_proxy_issue(error_msg)
        
        suggestions = []
        if not connectivity["internet"]:
            suggestions.append("インターネット接続を確認してください")
        if proxy_issue:
            suggestions.append("プロキシ設定を確認してください")
            suggestions.append(f"export HTTPS_PROXY={os.getenv('HTTPS_PROXY', 'your-proxy:port')}")
        if "dns" in error_msg:
            suggestions.append("DNS設定を確認してください")
            suggestions.append("代替DNSサーバー (8.8.8.8) を使用してみてください")
        
        return {
            "error_type": "network",
            "connectivity": connectivity,
            "proxy_detected": proxy_issue,
            "suggestions": suggestions,
            "retry_recommended": True,
            "wait_time": 5  # 5 seconds before retry
        }

    async def _check_connectivity(self) -> Dict[str, bool]:
        """Check various connectivity endpoints."""
        import socket
        
        results = {"internet": False, "gcp": False}
        
        for name, host in self.connection_checks:
            try:
                socket.gethostbyname(host)
                results["internet"] = True
                if "GCP" in name:
                    results["gcp"] = True
            except Exception:
                logger.debug(f"Failed to resolve {name} ({host})")
        
        return results

    def _detect_proxy_issue(self, error_msg: str) -> bool:
        """Detect if error is proxy-related."""
        proxy_keywords = ["proxy", "tunnel", "certificate", "ssl", "tls"]
        return any(keyword in error_msg for keyword in proxy_keywords)


class ResourceErrorHandler:
    """Handles resource limitation errors."""

    def __init__(self):
        self.resource_limits = {
            "memory": 1024 * 1024 * 1024,  # 1GB
            "disk": 10 * 1024 * 1024 * 1024,  # 10GB
            "cpu": 80  # 80% CPU usage
        }

    async def handle_resource_error(self, error: Exception, 
                                  context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resource limitation errors."""
        error_msg = str(error).lower()
        
        # Identify resource type
        resource_type = self._identify_resource_type(error_msg)
        
        # Get current usage
        current_usage = await self._get_resource_usage(resource_type)
        
        # Generate optimization strategies
        strategies = self._generate_optimization_strategies(resource_type, context)
        
        return {
            "error_type": "resource",
            "resource": resource_type,
            "current_usage": current_usage,
            "limit": self.resource_limits.get(resource_type),
            "optimization_strategies": strategies,
            "can_retry": True,
            "split_operation": resource_type in ["memory", "disk"]
        }

    def _identify_resource_type(self, error_msg: str) -> str:
        """Identify which resource is exhausted."""
        if "memory" in error_msg or "ram" in error_msg:
            return "memory"
        elif "disk" in error_msg or "storage" in error_msg:
            return "disk"
        elif "cpu" in error_msg or "processor" in error_msg:
            return "cpu"
        return "unknown"

    async def _get_resource_usage(self, resource_type: str) -> Dict[str, Any]:
        """Get current resource usage."""
        try:
            import psutil
            
            if resource_type == "memory":
                mem = psutil.virtual_memory()
                return {
                    "used": mem.used,
                    "total": mem.total,
                    "percent": mem.percent
                }
            elif resource_type == "disk":
                disk = psutil.disk_usage('/')
                return {
                    "used": disk.used,
                    "total": disk.total,
                    "percent": disk.percent
                }
            elif resource_type == "cpu":
                return {
                    "percent": psutil.cpu_percent(interval=1)
                }
        except ImportError:
            logger.warning("psutil not available for resource monitoring")
        
        return {"error": "Unable to get resource usage"}

    def _generate_optimization_strategies(self, resource_type: str, 
                                        context: Dict[str, Any]) -> list:
        """Generate optimization strategies based on resource type."""
        strategies = []
        
        if resource_type == "memory":
            strategies.extend([
                "データを小さなチャンクに分割して処理",
                "不要なオブジェクトを削除してガベージコレクションを実行",
                "キャッシュをクリア",
                "処理をストリーミング方式に変更"
            ])
        elif resource_type == "disk":
            strategies.extend([
                "一時ファイルを削除",
                "出力を圧縮形式で保存",
                "不要なログファイルを削除",
                "外部ストレージを使用"
            ])
        elif resource_type == "cpu":
            strategies.extend([
                "並列処理の数を減らす",
                "処理を時間帯をずらして実行",
                "より効率的なアルゴリズムを使用"
            ])
        
        return strategies


class ErrorHandlerRegistry:
    """Registry for specific error handlers."""

    def __init__(self):
        self.handlers = {
            "api_limit": APILimitHandler(),
            "permission": PermissionHandler(),
            "network": NetworkErrorHandler(),
            "resource": ResourceErrorHandler()
        }

    def get_handler(self, error_type: str):
        """Get specific handler for error type."""
        return self.handlers.get(error_type)

    async def handle_specific_error(self, error_type: str, error: Exception, 
                                  context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle error using specific handler."""
        handler = self.get_handler(error_type)
        if not handler:
            return None
        
        # Route to appropriate handler method
        if error_type == "api_limit":
            return await handler.handle_rate_limit(
                context.get("service", "default"), error
            )
        elif error_type == "permission":
            return await handler.handle_permission_error(
                context.get("resource_type", "unknown"), error
            )
        elif error_type == "network":
            return await handler.handle_network_error(error)
        elif error_type == "resource":
            return await handler.handle_resource_error(error, context)
        
        return None