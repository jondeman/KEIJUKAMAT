"""
Prompt Logger - Tracks all prompts used in API calls.

Features:
- Saves each prompt to dated log files
- Organizes by bot type (research, creative, ad)
- Automatic cleanup of logs older than 14 days
- Full traceability for prompt iteration
"""

import json
import os
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .config import settings
from .logger import get_logger

logger = get_logger(__name__)

# Default retention period
PROMPT_LOG_RETENTION_DAYS = 14


class PromptLogger:
    """
    Logs all prompts used in API calls for traceability.
    
    Directory structure:
    prompt_logs/
    ├── research/
    │   ├── 2026-01-16/
    │   │   ├── deep_research_001.md
    │   │   ├── diagnostic_001.md
    │   │   └── structure_001.md
    │   └── 2026-01-17/
    ├── creative/
    │   └── 2026-01-16/
    └── ad/
        └── 2026-01-16/
    """
    
    def __init__(self, base_dir: Path | None = None):
        """
        Initialize prompt logger.
        
        Args:
            base_dir: Base directory for logs. Defaults to PROJECT_ROOT/prompt_logs
        """
        if base_dir:
            self.base_dir = base_dir
        else:
            self.base_dir = settings.project_root / "prompt_logs"
        
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Track sequence numbers per category per day
        self._sequence_counters: dict[str, int] = {}
    
    def _get_date_dir(self, category: str) -> Path:
        """Get or create dated directory for a category."""
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        date_dir = self.base_dir / category / today
        date_dir.mkdir(parents=True, exist_ok=True)
        return date_dir
    
    def _get_sequence(self, category: str, prompt_type: str) -> int:
        """Get next sequence number for this category/type combo."""
        key = f"{category}_{prompt_type}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
        
        if key not in self._sequence_counters:
            # Count existing files to continue sequence
            date_dir = self._get_date_dir(category)
            existing = list(date_dir.glob(f"{prompt_type}_*.md"))
            self._sequence_counters[key] = len(existing) + 1
        else:
            self._sequence_counters[key] += 1
        
        return self._sequence_counters[key]
    
    def log_prompt(
        self,
        category: str,
        prompt_type: str,
        prompt: str,
        metadata: dict[str, Any] | None = None,
        response: str | None = None,
    ) -> Path:
        """
        Log a prompt to file.
        
        Args:
            category: Bot category (research, creative, ad)
            prompt_type: Type of prompt (deep_research, diagnostic, concept_gen, etc.)
            prompt: The full prompt text
            metadata: Optional metadata (model, temperature, etc.)
            response: Optional response text to log alongside
            
        Returns:
            Path to the saved log file
        """
        date_dir = self._get_date_dir(category)
        seq = self._get_sequence(category, prompt_type)
        
        filename = f"{prompt_type}_{seq:03d}.md"
        filepath = date_dir / filename
        
        # Build log content
        timestamp = datetime.now(timezone.utc).isoformat()
        
        content = f"""# Prompt Log: {prompt_type}

**Timestamp:** {timestamp}
**Category:** {category}
**Type:** {prompt_type}
"""
        
        if metadata:
            content += "\n## Metadata\n\n```json\n"
            content += json.dumps(metadata, indent=2, default=str)
            content += "\n```\n"
        
        content += f"\n## Prompt\n\n```\n{prompt}\n```\n"
        
        if response:
            # Save FULL response (no truncation)
            content += f"\n## Response\n\n```\n{response}\n```\n"
            content += f"\n*Response length: {len(response)} characters*\n"
        
        # Write file
        filepath.write_text(content, encoding="utf-8")
        
        logger.debug(
            "Prompt logged",
            category=category,
            prompt_type=prompt_type,
            file=str(filepath),
        )
        
        return filepath
    
    def cleanup_old_logs(self, retention_days: int = PROMPT_LOG_RETENTION_DAYS) -> int:
        """
        Delete log directories older than retention period.
        
        Args:
            retention_days: Number of days to keep logs (default 14)
            
        Returns:
            Number of directories deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=retention_days)
        cutoff_str = cutoff_date.strftime("%Y-%m-%d")
        
        deleted_count = 0
        
        # Check each category directory
        for category_dir in self.base_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            # Check each date directory within category
            for date_dir in category_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                # Parse directory name as date
                try:
                    dir_date = date_dir.name  # Format: YYYY-MM-DD
                    if dir_date < cutoff_str:
                        # Delete old directory
                        shutil.rmtree(date_dir)
                        deleted_count += 1
                        logger.info(
                            "Deleted old prompt logs",
                            directory=str(date_dir),
                            age_days=f">{retention_days}",
                        )
                except (ValueError, OSError) as e:
                    logger.warning(
                        "Could not process log directory",
                        directory=str(date_dir),
                        error=str(e),
                    )
        
        if deleted_count > 0:
            logger.info(
                "Prompt log cleanup complete",
                deleted_directories=deleted_count,
                retention_days=retention_days,
            )
        
        return deleted_count
    
    def get_stats(self) -> dict[str, Any]:
        """Get statistics about logged prompts."""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "categories": {},
        }
        
        for category_dir in self.base_dir.iterdir():
            if not category_dir.is_dir():
                continue
            
            category_stats = {
                "files": 0,
                "size_bytes": 0,
                "dates": [],
            }
            
            for date_dir in category_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                category_stats["dates"].append(date_dir.name)
                
                for file in date_dir.glob("*.md"):
                    category_stats["files"] += 1
                    category_stats["size_bytes"] += file.stat().st_size
            
            stats["categories"][category_dir.name] = category_stats
            stats["total_files"] += category_stats["files"]
            stats["total_size_bytes"] += category_stats["size_bytes"]
        
        return stats


# Global instance
_prompt_logger: PromptLogger | None = None


def get_prompt_logger() -> PromptLogger:
    """Get the global prompt logger instance."""
    global _prompt_logger
    if _prompt_logger is None:
        _prompt_logger = PromptLogger()
    return _prompt_logger


def log_prompt(
    category: str,
    prompt_type: str,
    prompt: str,
    metadata: dict[str, Any] | None = None,
    response: str | None = None,
) -> Path:
    """Convenience function to log a prompt using the global logger."""
    return get_prompt_logger().log_prompt(
        category=category,
        prompt_type=prompt_type,
        prompt=prompt,
        metadata=metadata,
        response=response,
    )


def cleanup_prompt_logs(retention_days: int = PROMPT_LOG_RETENTION_DAYS) -> int:
    """Convenience function to cleanup old logs."""
    return get_prompt_logger().cleanup_old_logs(retention_days)
