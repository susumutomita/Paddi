"""Context management system for maintaining conversation state and learning from interactions."""

import json
import re
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.log.logger import get_logger

logger = get_logger(__name__)


class MemoryStorage(ABC):
    """Abstract base class for memory storage backends."""

    @abstractmethod
    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data with the given key."""

    @abstractmethod
    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data for the given key."""

    @abstractmethod
    def delete(self, key: str) -> None:
        """Delete data for the given key."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if data exists for the given key."""


class FileMemoryStorage(MemoryStorage):
    """File-based memory storage implementation."""

    def __init__(self, base_path: str = "data/memory"):
        """Initialize file storage with base path."""
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_file_path(self, key: str) -> Path:
        """Get file path for a given key."""
        return self.base_path / f"{key}.json"

    def save(self, key: str, data: Dict[str, Any]) -> None:
        """Save data to file."""
        file_path = self._get_file_path(key)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            logger.info("Saved memory data to %s", file_path)
        except Exception as e:
            logger.error("Failed to save memory data: %s", e)
            raise

    def load(self, key: str) -> Optional[Dict[str, Any]]:
        """Load data from file."""
        file_path = self._get_file_path(key)
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load memory data: %s", e)
            return None

    def delete(self, key: str) -> None:
        """Delete file for the given key."""
        file_path = self._get_file_path(key)
        if file_path.exists():
            file_path.unlink()
            logger.info("Deleted memory file: %s", file_path)

    def exists(self, key: str) -> bool:
        """Check if file exists for the given key."""
        return self._get_file_path(key).exists()


class PrivacyFilter:
    """Handles privacy-related operations for memory management."""

    # Patterns for sensitive information
    SENSITIVE_PATTERNS = [
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
        r"\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b",  # Phone
        r"\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b",  # SSN
        r"\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13})\b",  # Credit card
        r"(?i)\b(?:password|passwd|pwd|token|api[_-]?key|secret)\s*[:=]\s*\S+",  # Credentials
    ]

    def __init__(self, custom_patterns: Optional[List[str]] = None):
        """Initialize privacy filter with optional custom patterns."""
        self.patterns = [re.compile(p) for p in self.SENSITIVE_PATTERNS]
        if custom_patterns:
            self.patterns.extend([re.compile(p) for p in custom_patterns])

    def mask_sensitive_data(self, text: str) -> str:
        """Mask sensitive information in text."""
        masked_text = text
        for pattern in self.patterns:
            masked_text = pattern.sub("[MASKED]", masked_text)
        return masked_text

    def contains_sensitive_data(self, text: str) -> bool:
        """Check if text contains sensitive information."""
        return any(pattern.search(text) for pattern in self.patterns)


class CommandPattern:
    """Represents a learned command pattern."""

    def __init__(self, pattern: str, frequency: int = 1, last_used: Optional[datetime] = None):
        """Initialize command pattern."""
        self.pattern = pattern
        self.frequency = frequency
        self.last_used = last_used or datetime.now()
        self.success_rate = 1.0
        self.contexts: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "pattern": self.pattern,
            "frequency": self.frequency,
            "last_used": self.last_used.isoformat(),
            "success_rate": self.success_rate,
            "contexts": self.contexts,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CommandPattern":
        """Create from dictionary."""
        pattern = cls(
            pattern=data["pattern"],
            frequency=data.get("frequency", 1),
            last_used=datetime.fromisoformat(data["last_used"]) if "last_used" in data else None,
        )
        pattern.success_rate = data.get("success_rate", 1.0)
        pattern.contexts = data.get("contexts", [])
        return pattern


class ContextualMemory:
    """Main context management class for handling memory and learning."""

    def __init__(
        self,
        storage: Optional[MemoryStorage] = None,
        privacy_filter: Optional[PrivacyFilter] = None,
        max_short_term_size: int = 100,
        project_id: Optional[str] = None,
    ):
        """Initialize contextual memory system."""
        self.storage = storage or FileMemoryStorage()
        self.privacy_filter = privacy_filter or PrivacyFilter()
        self.max_short_term_size = max_short_term_size
        self.project_id = project_id or "default"

        # Memory structures
        self.short_term = deque(maxlen=max_short_term_size)
        self.long_term: Dict[str, Any] = {}
        self.preferences: Dict[str, Any] = {}
        self.project_context: Dict[str, Any] = {}

        # Learning structures
        self.command_patterns: Dict[str, CommandPattern] = {}
        self.error_patterns: Dict[str, List[str]] = defaultdict(list)
        self.successful_solutions: Dict[str, str] = {}

        # Load existing memory
        self._load_memory()

    def _load_memory(self) -> None:
        """Load memory from storage."""
        memory_key = f"context_{self.project_id}"
        data = self.storage.load(memory_key)

        if data:
            self.long_term = data.get("long_term", {})
            self.preferences = data.get("preferences", {})
            self.project_context = data.get("project_context", {})

            # Restore command patterns
            patterns_data = data.get("command_patterns", {})
            self.command_patterns = {
                k: CommandPattern.from_dict(v) for k, v in patterns_data.items()
            }

            self.error_patterns = defaultdict(list, data.get("error_patterns", {}))
            self.successful_solutions = data.get("successful_solutions", {})

            logger.info("Loaded memory for project: %s", self.project_id)

    def save_memory(self) -> None:
        """Save current memory state to storage."""
        memory_key = f"context_{self.project_id}"

        # Convert command patterns to dict
        patterns_dict = {k: v.to_dict() for k, v in self.command_patterns.items()}

        data = {
            "long_term": self.long_term,
            "preferences": self.preferences,
            "project_context": self.project_context,
            "command_patterns": patterns_dict,
            "error_patterns": dict(self.error_patterns),
            "successful_solutions": self.successful_solutions,
            "last_saved": datetime.now().isoformat(),
        }

        self.storage.save(memory_key, data)
        logger.info("Saved memory for project: %s", self.project_id)

    def add_to_short_term(self, content: str, context_type: str = "general") -> None:
        """Add content to short-term memory."""
        # Apply privacy filter
        filtered_content = self.privacy_filter.mask_sensitive_data(content)

        entry = {
            "content": filtered_content,
            "type": context_type,
            "timestamp": datetime.now().isoformat(),
        }

        self.short_term.append(entry)
        logger.debug("Added to short-term memory: %s", context_type)

    def promote_to_long_term(self, key: str, value: Any) -> None:
        """Promote important information to long-term memory."""
        self.long_term[key] = {
            "value": value,
            "created": datetime.now().isoformat(),
            "access_count": 0,
        }
        self.save_memory()

    def get_from_memory(self, key: str) -> Optional[Any]:
        """Retrieve information from memory (checks both short and long term)."""
        # Check long-term first
        if key in self.long_term:
            self.long_term[key]["access_count"] += 1
            self.long_term[key]["last_accessed"] = datetime.now().isoformat()
            return self.long_term[key]["value"]

        # Check recent short-term entries
        for entry in reversed(self.short_term):
            if key.lower() in entry["content"].lower():
                return entry["content"]

        return None

    def learn_command_pattern(self, command: str, success: bool = True) -> None:
        """Learn from command execution patterns."""
        # Extract base pattern (remove specific values)
        pattern = self._extract_pattern(command)

        if pattern in self.command_patterns:
            self.command_patterns[pattern].frequency += 1
            self.command_patterns[pattern].last_used = datetime.now()

            # Update success rate
            current_rate = self.command_patterns[pattern].success_rate
            new_rate = (
                current_rate * (self.command_patterns[pattern].frequency - 1)
                + (1 if success else 0)
            ) / self.command_patterns[pattern].frequency
            self.command_patterns[pattern].success_rate = new_rate
        else:
            self.command_patterns[pattern] = CommandPattern(pattern)

        logger.debug("Learned command pattern: %s", pattern)

    def _extract_pattern(self, command: str) -> str:
        """Extract generic pattern from specific command."""
        # Replace specific project/file names with placeholders
        pattern = re.sub(r"\"[^\"]+\"", '"<VALUE>"', command)
        pattern = re.sub(r"\'[^\']+\'", "'<VALUE>'", pattern)
        pattern = re.sub(r"\b[0-9]+\b", "<NUMBER>", pattern)
        return pattern

    def suggest_command(self, partial_command: str) -> Optional[str]:
        """Suggest command based on learned patterns."""
        matches = []

        for pattern, cmd_pattern in self.command_patterns.items():
            if partial_command.lower() in pattern.lower():
                matches.append((cmd_pattern.frequency * cmd_pattern.success_rate, pattern))

        if matches:
            # Return most frequently successful pattern
            matches.sort(reverse=True)
            return matches[0][1]

        return None

    def record_error(self, error_type: str, solution: Optional[str] = None) -> None:
        """Record error patterns and their solutions."""
        self.error_patterns[error_type].append(datetime.now().isoformat())

        if solution:
            self.successful_solutions[error_type] = solution
            logger.info("Recorded solution for error: %s", error_type)

    def get_error_solution(self, error_type: str) -> Optional[str]:
        """Get previously successful solution for an error."""
        return self.successful_solutions.get(error_type)

    def set_preference(self, key: str, value: Any) -> None:
        """Set user preference."""
        self.preferences[key] = value
        self.save_memory()

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Get user preference."""
        return self.preferences.get(key, default)

    def set_project_context(self, key: str, value: Any) -> None:
        """Set project-specific context."""
        self.project_context[key] = value
        self.save_memory()

    def get_project_context(self, key: str, default: Any = None) -> Any:
        """Get project-specific context."""
        return self.project_context.get(key, default)

    def get_recent_context(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent context from short-term memory."""
        return list(reversed(list(self.short_term)))[:limit]

    def find_similar_commands(self, query: str, limit: int = 5) -> List[str]:
        """Find similar previously used commands."""
        query_pattern = self._extract_pattern(query)
        similar = []

        for pattern, cmd_pattern in self.command_patterns.items():
            # Simple similarity check (can be enhanced with better algorithms)
            if any(word in pattern.lower() for word in query_pattern.lower().split()):
                similar.append((cmd_pattern.frequency, pattern))

        similar.sort(reverse=True)
        return [pattern for _, pattern in similar[:limit]]

    def clear_memory(self, scope: str = "all") -> None:
        """Clear memory based on scope."""
        if scope == "all":
            self.short_term.clear()
            self.long_term.clear()
            self.preferences.clear()
            self.project_context.clear()
            self.command_patterns.clear()
            self.error_patterns.clear()
            self.successful_solutions.clear()
            logger.info("Cleared all memory")
        elif scope == "short_term":
            self.short_term.clear()
            logger.info("Cleared short-term memory")
        elif scope == "long_term":
            self.long_term.clear()
            logger.info("Cleared long-term memory")
        elif scope == "preferences":
            self.preferences.clear()
            logger.info("Cleared preferences")
        elif scope == "project":
            self.project_context.clear()
            logger.info("Cleared project context")
        elif scope == "learning":
            self.command_patterns.clear()
            self.error_patterns.clear()
            self.successful_solutions.clear()
            logger.info("Cleared learning data")
        else:
            logger.warning("Unknown scope: %s", scope)

        self.save_memory()

    def export_memory(self) -> Dict[str, Any]:
        """Export memory for backup or transfer."""
        return {
            "short_term": list(self.short_term),
            "long_term": self.long_term,
            "preferences": self.preferences,
            "project_context": self.project_context,
            "command_patterns": {k: v.to_dict() for k, v in self.command_patterns.items()},
            "error_patterns": dict(self.error_patterns),
            "successful_solutions": self.successful_solutions,
            "exported_at": datetime.now().isoformat(),
        }

    def import_memory(self, data: Dict[str, Any]) -> None:
        """Import memory from backup."""
        if "short_term" in data:
            self.short_term = deque(data["short_term"], maxlen=self.max_short_term_size)

        if "long_term" in data:
            self.long_term = data["long_term"]

        if "preferences" in data:
            self.preferences = data["preferences"]

        if "project_context" in data:
            self.project_context = data["project_context"]

        if "command_patterns" in data:
            self.command_patterns = {
                k: CommandPattern.from_dict(v) for k, v in data["command_patterns"].items()
            }

        if "error_patterns" in data:
            self.error_patterns = defaultdict(list, data["error_patterns"])

        if "successful_solutions" in data:
            self.successful_solutions = data["successful_solutions"]

        self.save_memory()
        logger.info("Imported memory successfully")
