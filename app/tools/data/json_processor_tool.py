"""JSON data processing tool."""

import json
import logging
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


class JSONProcessorTool(BaseTool):
    """Tool for processing and transforming JSON data."""

    def _get_metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return ToolMetadata(
            name="json_processor",
            description="Processes and transforms JSON data with various operations",
            category=ToolCategory.DATA_PROCESSING,
            priority=ToolPriority.MEDIUM,
            tags=["json", "data", "transform", "filter", "merge", "validate"],
            parameters={
                "operation": {
                    "type": "string",
                    "description": "Operation to perform",
                    "required": True,
                    "choices": ["filter", "transform", "merge", "validate", "query", "format"],
                },
                "input_data": {
                    "type": "object|string",
                    "description": "Input JSON data or file path",
                    "required": True,
                },
                "criteria": {
                    "type": "object",
                    "description": "Criteria for filter/query operations",
                    "required": False,
                },
                "transform_spec": {
                    "type": "object",
                    "description": "Transformation specification",
                    "required": False,
                },
                "merge_data": {
                    "type": "object|string",
                    "description": "Data to merge with input",
                    "required": False,
                },
                "schema": {
                    "type": "object",
                    "description": "JSON schema for validation",
                    "required": False,
                },
                "output_file": {
                    "type": "string",
                    "description": "Output file path",
                    "required": False,
                },
            },
        )

    def validate_parameters(self, params: Dict[str, Any]) -> List[str]:
        """Validate input parameters."""
        errors = []

        # Check required parameters
        if "operation" not in params:
            errors.append("Missing required parameter: operation")
        if "input_data" not in params:
            errors.append("Missing required parameter: input_data")

        # Validate operation
        if "operation" in params:
            valid_ops = ["filter", "transform", "merge", "validate", "query", "format"]
            if params["operation"] not in valid_ops:
                errors.append(f"Invalid operation: {params['operation']}")

            # Check operation-specific requirements
            if params["operation"] == "filter" and "criteria" not in params:
                errors.append("Filter operation requires 'criteria' parameter")
            if params["operation"] == "transform" and "transform_spec" not in params:
                errors.append("Transform operation requires 'transform_spec' parameter")
            if params["operation"] == "merge" and "merge_data" not in params:
                errors.append("Merge operation requires 'merge_data' parameter")
            if params["operation"] == "validate" and "schema" not in params:
                errors.append("Validate operation requires 'schema' parameter")

        return errors

    def execute(self, context: ToolExecutionContext, **kwargs) -> ToolResult:
        """Execute JSON processing operation."""
        try:
            operation = kwargs["operation"]
            input_data = self._load_json_data(kwargs["input_data"])

            result_data = None

            if operation == "filter":
                result_data = self._filter_data(input_data, kwargs["criteria"])
            elif operation == "transform":
                result_data = self._transform_data(input_data, kwargs["transform_spec"])
            elif operation == "merge":
                merge_data = self._load_json_data(kwargs["merge_data"])
                result_data = self._merge_data(input_data, merge_data)
            elif operation == "validate":
                validation_result = self._validate_data(input_data, kwargs["schema"])
                return ToolResult(
                    success=validation_result["valid"],
                    data=validation_result,
                    error=validation_result.get("error"),
                )
            elif operation == "query":
                result_data = self._query_data(input_data, kwargs.get("criteria", {}))
            elif operation == "format":
                result_data = self._format_data(input_data)

            # Save to file if requested
            if "output_file" in kwargs and result_data is not None:
                output_path = Path(kwargs["output_file"])
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result_data, f, indent=2, ensure_ascii=False)

            return ToolResult(
                success=True,
                data=result_data,
                metadata={
                    "operation": operation,
                    "input_size": self._get_data_size(input_data),
                    "output_size": self._get_data_size(result_data),
                    "output_file": kwargs.get("output_file"),
                },
            )

        except Exception as e:
            logger.error(f"JSON processing failed: {e}")
            return ToolResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__},
            )

    def _load_json_data(self, data: Union[str, dict]) -> Any:
        """Load JSON data from string path or dict."""
        if isinstance(data, str):
            # Check if it's a file path
            path = Path(data)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                # Try to parse as JSON string
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    raise ValueError(f"Invalid JSON data or file not found: {data}")
        return data

    def _filter_data(self, data: Any, criteria: Dict[str, Any]) -> Any:
        """Filter JSON data based on criteria."""
        if isinstance(data, list):
            result = []
            for item in data:
                if self._matches_criteria(item, criteria):
                    result.append(item)
            return result
        elif isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if self._matches_criteria({key: value}, criteria):
                    result[key] = value
            return result
        return data

    def _matches_criteria(self, item: Any, criteria: Dict[str, Any]) -> bool:
        """Check if item matches filter criteria."""
        if not isinstance(item, dict):
            return False

        for key, expected in criteria.items():
            if key not in item:
                return False
            
            actual = item[key]
            
            # Handle different comparison types
            if isinstance(expected, dict):
                # Advanced comparisons
                if "$gt" in expected and not (actual > expected["$gt"]):
                    return False
                if "$lt" in expected and not (actual < expected["$lt"]):
                    return False
                if "$in" in expected and actual not in expected["$in"]:
                    return False
                if "$regex" in expected:
                    import re
                    if not re.match(expected["$regex"], str(actual)):
                        return False
            elif actual != expected:
                return False

        return True

    def _transform_data(self, data: Any, spec: Dict[str, Any]) -> Any:
        """Transform data according to specification."""
        if isinstance(data, list):
            return [self._transform_item(item, spec) for item in data]
        elif isinstance(data, dict):
            return self._transform_item(data, spec)
        return data

    def _transform_item(self, item: Dict[str, Any], spec: Dict[str, Any]) -> Dict[str, Any]:
        """Transform a single item."""
        result = {}

        for target_key, source_spec in spec.items():
            if isinstance(source_spec, str):
                # Simple field mapping
                if source_spec in item:
                    result[target_key] = item[source_spec]
            elif isinstance(source_spec, dict):
                # Complex transformation
                if "field" in source_spec:
                    value = item.get(source_spec["field"])
                    
                    # Apply transformations
                    if "upper" in source_spec and source_spec["upper"]:
                        value = str(value).upper()
                    if "lower" in source_spec and source_spec["lower"]:
                        value = str(value).lower()
                    if "default" in source_spec and value is None:
                        value = source_spec["default"]
                    
                    result[target_key] = value

        return result

    def _merge_data(self, data1: Any, data2: Any) -> Any:
        """Merge two JSON data structures."""
        if isinstance(data1, dict) and isinstance(data2, dict):
            result = data1.copy()
            result.update(data2)
            return result
        elif isinstance(data1, list) and isinstance(data2, list):
            return data1 + data2
        else:
            return [data1, data2]

    def _validate_data(self, data: Any, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against JSON schema."""
        try:
            # Simple validation implementation
            # In production, use jsonschema library
            errors = []
            
            if "type" in schema:
                expected_type = schema["type"]
                actual_type = type(data).__name__
                
                type_map = {
                    "object": "dict",
                    "array": "list",
                    "string": "str",
                    "number": "float",
                    "integer": "int",
                    "boolean": "bool",
                }
                
                if type_map.get(expected_type, expected_type) != actual_type:
                    errors.append(f"Expected type {expected_type}, got {actual_type}")

            if "required" in schema and isinstance(data, dict):
                for required_field in schema["required"]:
                    if required_field not in data:
                        errors.append(f"Missing required field: {required_field}")

            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "error": "; ".join(errors) if errors else None,
            }

        except Exception as e:
            return {
                "valid": False,
                "errors": [str(e)],
                "error": str(e),
            }

    def _query_data(self, data: Any, criteria: Dict[str, Any]) -> Any:
        """Query data using JSONPath-like syntax."""
        # Simple implementation
        if not criteria:
            return data

        path = criteria.get("path", "")
        if path:
            parts = path.split(".")
            result = data
            for part in parts:
                if isinstance(result, dict) and part in result:
                    result = result[part]
                elif isinstance(result, list) and part.isdigit():
                    idx = int(part)
                    if 0 <= idx < len(result):
                        result = result[idx]
                else:
                    return None
            return result

        return data

    def _format_data(self, data: Any) -> str:
        """Format JSON data as pretty-printed string."""
        return json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True)

    def _get_data_size(self, data: Any) -> int:
        """Get approximate size of data."""
        if data is None:
            return 0
        json_str = json.dumps(data)
        return len(json_str)