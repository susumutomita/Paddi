"""System information and management tools."""

import logging
import os
import platform
import psutil
import subprocess
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.tools.base import (
    BaseTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)


logger = logging.getLogger(__name__)


class SystemInfoTool(BaseTool):
    """Tool for gathering system information."""

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="system_info",
            description="Gathers system information including OS, hardware, processes, and network",
            category=ToolCategory.SYSTEM_MANAGEMENT,
            priority=ToolPriority.LOW,
            tags=["system", "info", "monitoring", "hardware", "processes"],
            parameters={
                "info_type": {
                    "type": "string",
                    "description": "Type of information to gather (all, os, cpu, memory, disk, network, processes)",
                    "required": False,
                    "default": "all",
                },
                "format": {
                    "type": "string",
                    "description": "Output format (json, text)",
                    "required": False,
                    "default": "json",
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Validate info_type
        if "info_type" in params:
            valid_types = ["all", "os", "cpu", "memory", "disk", "network", "processes"]
            if params["info_type"] not in valid_types:
                errors.append(f"Invalid info_type: {params['info_type']}. Must be one of {valid_types}")

        # Validate format
        if "format" in params:
            valid_formats = ["json", "text"]
            if params["format"] not in valid_formats:
                errors.append(f"Invalid format: {params['format']}. Must be one of {valid_formats}")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute system information gathering."""
        try:
            info_type = kwargs.get("info_type", "all")
            output_format = kwargs.get("format", "json")

            info = {}

            if info_type in ["all", "os"]:
                info["os"] = self._get_os_info()

            if info_type in ["all", "cpu"]:
                info["cpu"] = self._get_cpu_info()

            if info_type in ["all", "memory"]:
                info["memory"] = self._get_memory_info()

            if info_type in ["all", "disk"]:
                info["disk"] = self._get_disk_info()

            if info_type in ["all", "network"]:
                info["network"] = self._get_network_info()

            if info_type in ["all", "processes"]:
                info["processes"] = self._get_process_info()

            # Format output
            if output_format == "text":
                data = self._format_as_text(info)
            else:
                data = info

            return ToolResult(
                success=True,
                data=data,
                metadata={
                    "info_type": info_type,
                    "format": output_format,
                    "timestamp": datetime.utcnow().isoformat(),
                },
            )

        except Exception as e:
            logger.error(f"Failed to gather system information: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )

    def _get_os_info(self) -> Dict[str, Any]:
        """Get operating system information."""
        return {
            "system": platform.system(),
            "node": platform.node(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat(),
        }

    def _get_cpu_info(self) -> Dict[str, Any]:
        """Get CPU information."""
        cpu_freq = psutil.cpu_freq()
        return {
            "physical_cores": psutil.cpu_count(logical=False),
            "total_cores": psutil.cpu_count(logical=True),
            "max_frequency": cpu_freq.max if cpu_freq else None,
            "min_frequency": cpu_freq.min if cpu_freq else None,
            "current_frequency": cpu_freq.current if cpu_freq else None,
            "cpu_usage_per_core": psutil.cpu_percent(interval=1, percpu=True),
            "total_cpu_usage": psutil.cpu_percent(interval=1),
        }

    def _get_memory_info(self) -> Dict[str, Any]:
        """Get memory information."""
        virtual_mem = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "virtual": {
                "total": virtual_mem.total,
                "available": virtual_mem.available,
                "used": virtual_mem.used,
                "percentage": virtual_mem.percent,
            },
            "swap": {
                "total": swap.total,
                "used": swap.used,
                "free": swap.free,
                "percentage": swap.percent,
            },
        }

    def _get_disk_info(self) -> Dict[str, Any]:
        """Get disk information."""
        partitions = psutil.disk_partitions()
        disk_info = []

        for partition in partitions:
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_info.append({
                    "device": partition.device,
                    "mountpoint": partition.mountpoint,
                    "fstype": partition.fstype,
                    "total": usage.total,
                    "used": usage.used,
                    "free": usage.free,
                    "percentage": usage.percent,
                })
            except PermissionError:
                # This can happen on Windows
                continue

        return {
            "partitions": disk_info,
            "io_counters": psutil.disk_io_counters()._asdict() if psutil.disk_io_counters() else None,
        }

    def _get_network_info(self) -> Dict[str, Any]:
        """Get network information."""
        interfaces = {}
        for interface, addrs in psutil.net_if_addrs().items():
            interfaces[interface] = []
            for addr in addrs:
                interfaces[interface].append({
                    "family": str(addr.family),
                    "address": addr.address,
                    "netmask": addr.netmask,
                    "broadcast": addr.broadcast,
                })

        return {
            "interfaces": interfaces,
            "io_counters": psutil.net_io_counters()._asdict() if psutil.net_io_counters() else None,
        }

    def _get_process_info(self) -> List[Dict[str, Any]]:
        """Get information about running processes."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status']):
            try:
                processes.append({
                    "pid": proc.info['pid'],
                    "name": proc.info['name'],
                    "cpu_percent": proc.info['cpu_percent'],
                    "memory_percent": proc.info['memory_percent'],
                    "status": proc.info['status'],
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'] or 0, reverse=True)
        return processes[:20]  # Return top 20 processes

    def _format_as_text(self, info: Dict[str, Any]) -> str:
        """Format information as readable text."""
        lines = []

        for section, data in info.items():
            lines.append(f"\n=== {section.upper()} ===")
            lines.append(self._format_section(data))

        return "\n".join(lines)

    def _format_section(self, data: Any, indent: int = 0) -> str:
        """Format a section of data."""
        lines = []
        prefix = "  " * indent

        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._format_section(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    lines.append(self._format_section(item, indent))
                    lines.append("")  # Empty line between items
                else:
                    lines.append(f"{prefix}- {item}")
        else:
            lines.append(f"{prefix}{data}")

        return "\n".join(lines)