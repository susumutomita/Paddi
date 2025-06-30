"""File operation tools."""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Any, Dict, List, Union

from app.tools.base import (
    BaseTool,
    ToolCategory,
    ToolExecutionContext,
    ToolMetadata,
    ToolPriority,
    ToolResult,
)


logger = logging.getLogger(__name__)


class FileOperationTool(BaseTool):
    """Tool for file operations."""

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="file_operation",
            description="Performs file operations like read, write, copy, move, and delete",
            category=ToolCategory.FILE_OPERATION,
            priority=ToolPriority.MEDIUM,
            tags=["file", "filesystem", "io", "read", "write"],
            parameters={
                "operation": {
                    "type": "string",
                    "description": "Operation to perform (read, write, copy, move, delete, list)",
                    "required": True,
                },
                "path": {
                    "type": "string",
                    "description": "File or directory path",
                    "required": True,
                },
                "content": {
                    "type": "string",
                    "description": "Content for write operation",
                    "required": False,
                },
                "destination": {
                    "type": "string",
                    "description": "Destination path for copy/move operations",
                    "required": False,
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Recursive operation for directories",
                    "required": False,
                    "default": False,
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Check required parameters
        if "operation" not in params:
            errors.append("Missing required parameter: operation")
        if "path" not in params:
            errors.append("Missing required parameter: path")

        # Validate operation
        if "operation" in params:
            valid_operations = ["read", "write", "copy", "move", "delete", "list", "exists"]
            if params["operation"] not in valid_operations:
                errors.append(f"Invalid operation: {params['operation']}. Must be one of {valid_operations}")

            # Check operation-specific requirements
            if params["operation"] == "write" and "content" not in params:
                errors.append("Write operation requires 'content' parameter")
            if params["operation"] in ["copy", "move"] and "destination" not in params:
                errors.append(f"{params['operation'].capitalize()} operation requires 'destination' parameter")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute file operation."""
        try:
            operation = kwargs["operation"]
            path = Path(kwargs["path"])
            
            if operation == "read":
                return self._read_file(path)
            elif operation == "write":
                return self._write_file(path, kwargs["content"])
            elif operation == "copy":
                return self._copy_file(path, Path(kwargs["destination"]), kwargs.get("recursive", False))
            elif operation == "move":
                return self._move_file(path, Path(kwargs["destination"]))
            elif operation == "delete":
                return self._delete_file(path, kwargs.get("recursive", False))
            elif operation == "list":
                return self._list_directory(path)
            elif operation == "exists":
                return self._check_exists(path)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unsupported operation: {operation}"
                )

        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__}
            )

    def _read_file(self, path: Path) -> ToolResult:
        """Read file content."""
        if not path.exists():
            return ToolResult(
                success=False,
                error=f"File not found: {path}"
            )

        if path.is_dir():
            return ToolResult(
                success=False,
                error=f"Cannot read directory: {path}"
            )

        try:
            # Detect file type and read accordingly
            if path.suffix == ".json":
                with open(path, "r", encoding="utf-8") as f:
                    content = json.load(f)
            else:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()

            return ToolResult(
                success=True,
                data=content,
                metadata={
                    "file_size": path.stat().st_size,
                    "file_type": path.suffix,
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to read file: {e}"
            )

    def _write_file(self, path: Path, content: Union[str, dict]) -> ToolResult:
        """Write content to file."""
        try:
            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Write based on content type
            if isinstance(content, dict) or (isinstance(content, str) and path.suffix == ".json"):
                with open(path, "w", encoding="utf-8") as f:
                    if isinstance(content, str):
                        content = json.loads(content)
                    json.dump(content, f, indent=2, ensure_ascii=False)
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)

            return ToolResult(
                success=True,
                data={"path": str(path), "size": path.stat().st_size},
                metadata={"operation": "write", "path": str(path)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to write file: {e}"
            )

    def _copy_file(self, source: Path, destination: Path, recursive: bool) -> ToolResult:
        """Copy file or directory."""
        if not source.exists():
            return ToolResult(
                success=False,
                error=f"Source not found: {source}"
            )

        try:
            if source.is_dir():
                if recursive:
                    shutil.copytree(source, destination)
                else:
                    return ToolResult(
                        success=False,
                        error="Directory copy requires recursive=True"
                    )
            else:
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, destination)

            return ToolResult(
                success=True,
                data={
                    "source": str(source),
                    "destination": str(destination),
                    "copied": True
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to copy: {e}"
            )

    def _move_file(self, source: Path, destination: Path) -> ToolResult:
        """Move file or directory."""
        if not source.exists():
            return ToolResult(
                success=False,
                error=f"Source not found: {source}"
            )

        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))

            return ToolResult(
                success=True,
                data={
                    "source": str(source),
                    "destination": str(destination),
                    "moved": True
                }
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to move: {e}"
            )

    def _delete_file(self, path: Path, recursive: bool) -> ToolResult:
        """Delete file or directory."""
        if not path.exists():
            return ToolResult(
                success=False,
                error=f"Path not found: {path}"
            )

        try:
            if path.is_dir():
                if recursive:
                    shutil.rmtree(path)
                else:
                    path.rmdir()  # Only works for empty directories
            else:
                path.unlink()

            return ToolResult(
                success=True,
                data={"deleted": str(path)},
                metadata={"recursive": recursive}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to delete: {e}"
            )

    def _list_directory(self, path: Path) -> ToolResult:
        """List directory contents."""
        if not path.exists():
            return ToolResult(
                success=False,
                error=f"Path not found: {path}"
            )

        if not path.is_dir():
            return ToolResult(
                success=False,
                error=f"Not a directory: {path}"
            )

        try:
            items = []
            for item in path.iterdir():
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None,
                    "path": str(item),
                })

            return ToolResult(
                success=True,
                data=items,
                metadata={"count": len(items), "directory": str(path)}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Failed to list directory: {e}"
            )

    def _check_exists(self, path: Path) -> ToolResult:
        """Check if path exists."""
        exists = path.exists()
        data = {
            "exists": exists,
            "path": str(path)
        }

        if exists:
            data["type"] = "directory" if path.is_dir() else "file"
            if path.is_file():
                data["size"] = path.stat().st_size

        return ToolResult(
            success=True,
            data=data
        )