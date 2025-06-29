"""File-based repository implementation."""

import json
import logging
from pathlib import Path
from typing import Any, List, Optional

from .base import Repository

logger = logging.getLogger(__name__)


class FileRepository(Repository):
    """File-based repository for persistent storage."""
    
    def __init__(self, base_path: str = "data"):
        """Initialize file repository.
        
        Args:
            base_path: Base directory for storing files
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True, parents=True)
    
    def _get_file_path(self, key: str, format: str = "json") -> Path:
        """Get file path for a key."""
        extension = "json" if format == "json" else "txt"
        return self.base_path / f"{key}.{extension}"
    
    def _detect_format(self, key: str) -> str:
        """Detect file format based on existing files."""
        json_path = self._get_file_path(key, "json")
        txt_path = self._get_file_path(key, "text")
        
        if json_path.exists():
            return "json"
        elif txt_path.exists():
            return "text"
        return "json"  # Default
    
    def save(self, key: str, data: Any, format: str = "json", **kwargs) -> None:
        """Save data to file.
        
        Args:
            key: Key for the data
            data: Data to save
            format: File format ('json' or 'text')
        """
        if format not in ["json", "text"]:
            raise ValueError(f"Unsupported format: {format}")
        
        file_path = self._get_file_path(key, format)
        
        try:
            if format == "json":
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
            else:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(str(data))
            
            logger.debug("Saved %s to %s", key, file_path)
        except Exception as e:
            logger.error("Failed to save %s: %s", key, e)
            raise
    
    def load(self, key: str, format: Optional[str] = None, **kwargs) -> Optional[Any]:
        """Load data from file.
        
        Args:
            key: Key for the data
            format: File format (auto-detected if None)
        """
        if format is None:
            format = self._detect_format(key)
        
        file_path = self._get_file_path(key, format)
        
        if not file_path.exists():
            logger.debug("File not found: %s", file_path)
            return None
        
        try:
            if format == "json":
                with open(file_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            else:
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
        except Exception as e:
            logger.error("Failed to load %s: %s", key, e)
            raise
    
    def exists(self, key: str) -> bool:
        """Check if file exists for key."""
        json_exists = self._get_file_path(key, "json").exists()
        txt_exists = self._get_file_path(key, "text").exists()
        return json_exists or txt_exists
    
    def delete(self, key: str) -> None:
        """Delete file by key."""
        # Try to delete both formats
        for format in ["json", "text"]:
            file_path = self._get_file_path(key, format)
            if file_path.exists():
                file_path.unlink()
                logger.debug("Deleted %s", file_path)
    
    def list_keys(self) -> List[str]:
        """List all keys (file names without extensions)."""
        keys = set()
        
        # Get all JSON files
        for json_file in self.base_path.glob("*.json"):
            keys.add(json_file.stem)
        
        # Get all text files
        for txt_file in self.base_path.glob("*.txt"):
            keys.add(txt_file.stem)
        
        return sorted(list(keys))