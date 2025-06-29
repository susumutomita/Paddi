"""Data service for handling data persistence using repository pattern."""

import logging
from typing import Any, Dict, List, Optional

from app.repository.base import Repository
from app.repository.factory import RepositoryFactory

logger = logging.getLogger(__name__)


class DataService:
    """Service for managing data persistence."""
    
    def __init__(self, repository: Optional[Repository] = None):
        """Initialize data service.
        
        Args:
            repository: Repository instance (uses default if None)
        """
        self.repository = repository or RepositoryFactory.get_default()
    
    def save_collected_data(self, data: Dict[str, Any], key: str = "collected") -> str:
        """Save collected cloud configuration data.
        
        Args:
            data: Collected data to save
            key: Key for the data (default: "collected")
            
        Returns:
            Key used for saving
        """
        self.repository.save(key, data)
        logger.info("Saved collected data with key: %s", key)
        return key
    
    def load_collected_data(self, key: str = "collected") -> Optional[Dict[str, Any]]:
        """Load collected cloud configuration data.
        
        Args:
            key: Key for the data (default: "collected")
            
        Returns:
            Collected data or None if not found
        """
        data = self.repository.load(key)
        if data:
            logger.info("Loaded collected data with key: %s", key)
        else:
            logger.warning("No collected data found with key: %s", key)
        return data
    
    def save_explained_data(self, data: List[Dict[str, Any]], key: str = "explained") -> str:
        """Save security findings from explainer.
        
        Args:
            data: Security findings to save
            key: Key for the data (default: "explained")
            
        Returns:
            Key used for saving
        """
        self.repository.save(key, data)
        logger.info("Saved explained data with key: %s", key)
        return key
    
    def load_explained_data(self, key: str = "explained") -> Optional[List[Dict[str, Any]]]:
        """Load security findings from explainer.
        
        Args:
            key: Key for the data (default: "explained")
            
        Returns:
            Security findings or None if not found
        """
        data = self.repository.load(key)
        if data:
            logger.info("Loaded explained data with key: %s", key)
        else:
            logger.warning("No explained data found with key: %s", key)
        return data
    
    def save_report(self, content: str, key: str, format: str = "text") -> str:
        """Save generated report.
        
        Args:
            content: Report content
            key: Key for the report
            format: Report format ('text' for MD/HTML)
            
        Returns:
            Key used for saving
        """
        self.repository.save(key, content, format=format)
        logger.info("Saved report with key: %s", key)
        return key
    
    def load_report(self, key: str) -> Optional[str]:
        """Load generated report.
        
        Args:
            key: Key for the report
            
        Returns:
            Report content or None if not found
        """
        content = self.repository.load(key)
        if content:
            logger.info("Loaded report with key: %s", key)
        else:
            logger.warning("No report found with key: %s", key)
        return content
    
    def list_available_data(self) -> Dict[str, List[str]]:
        """List all available data by category.
        
        Returns:
            Dictionary with categories and their keys
        """
        all_keys = self.repository.list_keys()
        
        categorized = {
            "collected": [],
            "explained": [],
            "reports": [],
            "other": []
        }
        
        for key in all_keys:
            if "collected" in key:
                categorized["collected"].append(key)
            elif "explained" in key:
                categorized["explained"].append(key)
            elif "audit" in key or "report" in key:
                categorized["reports"].append(key)
            else:
                categorized["other"].append(key)
        
        return categorized
    
    def cleanup_old_data(self, keep_latest: int = 5) -> int:
        """Clean up old data files, keeping only the latest ones.
        
        Args:
            keep_latest: Number of latest files to keep per category
            
        Returns:
            Number of files deleted
        """
        categorized = self.list_available_data()
        deleted_count = 0
        
        for category, keys in categorized.items():
            if len(keys) > keep_latest:
                # Sort keys (assuming they have timestamps)
                sorted_keys = sorted(keys)
                keys_to_delete = sorted_keys[:-keep_latest]
                
                for key in keys_to_delete:
                    self.repository.delete(key)
                    deleted_count += 1
                    logger.debug("Deleted old data: %s", key)
        
        if deleted_count > 0:
            logger.info("Cleaned up %d old data files", deleted_count)
        
        return deleted_count