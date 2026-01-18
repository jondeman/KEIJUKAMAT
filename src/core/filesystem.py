"""
Filesystem utilities for KonseptiKeiju.

Handles all path management, directory creation, and file I/O operations
to ensure consistent structure across runs and archive.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles

from .config import settings


def slugify(text: str) -> str:
    """
    Convert text to a URL-safe slug.
    
    Examples:
        "Acme Corp" -> "acme-corp"
        "McDonald's" -> "mcdonalds"
        "AT&T Communications" -> "att-communications"
    """
    # Lowercase
    slug = text.lower()
    # Remove special characters except spaces and hyphens
    slug = re.sub(r"[^a-z0-9\s-]", "", slug)
    # Replace spaces with hyphens
    slug = re.sub(r"\s+", "-", slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r"-+", "-", slug)
    # Strip leading/trailing hyphens
    slug = slug.strip("-")
    return slug


def company_folder_name(company_name: str) -> str:
    """
    Create a filesystem-safe company folder name using underscores.

    Examples:
        "Musti & Mirri" -> "musti__mirri"
        "Instrumentarium" -> "instrumentarium"
    """
    cleaned = company_name.strip().replace(" ", "_")
    cleaned = re.sub(r"[^A-Za-z0-9_-]", "", cleaned)
    if not cleaned:
        cleaned = slugify(company_name).replace("-", "_")
    return cleaned.lower()


def generate_run_id() -> str:
    """Generate a unique run ID based on timestamp."""
    return datetime.utcnow().strftime("%Y%m%d_%H%M%S")


class RunPaths:
    """
    Path manager for a specific pipeline run.
    
    Provides consistent access to all file paths within a run's directory.
    """

    def __init__(self, run_id: str, company_slug: str):
        self.run_id = run_id
        self.company_slug = company_slug
        self.date_str = datetime.utcnow().strftime("%Y-%m-%d")
        
        # Base run directory: runs/{YYYY-MM-DD}_{company_slug}_{run_id}/
        self.base = settings.get_runs_path() / f"{self.date_str}_{company_slug}_{run_id}"

    @property
    def run_dir(self) -> Path:
        """Alias for base directory - the root of this run's artifacts."""
        return self.base

    def ensure_directories(self) -> None:
        """Create all required directories for this run."""
        directories = [
            self.base,
            self.base / "artifacts",
            self.base / "artifacts" / "research",
            self.base / "artifacts" / "concepts",
            self.base / "artifacts" / "onepagers",
            self.base / "artifacts" / "onepagers" / "variants",
            self.base / "artifacts" / "delivery",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    # State files
    @property
    def state_file(self) -> Path:
        return self.base / "run_state.json"

    @property
    def logs_file(self) -> Path:
        return self.base / "logs.jsonl"

    @property
    def additional_context_md(self) -> Path:
        return self.base / "additional_context.md"

    # Research artifacts
    @property
    def research_dir(self) -> Path:
        return self.base / "artifacts" / "research"

    @property
    def strategic_dossier_json(self) -> Path:
        return self.research_dir / "strategic_dossier.json"

    @property
    def strategic_dossier_md(self) -> Path:
        return self.research_dir / "strategic_dossier.md"

    @property
    def research_raw_md(self) -> Path:
        return self.research_dir / "research_raw.md"

    @property
    def sources_json(self) -> Path:
        return self.research_dir / "sources.json"

    # Concept artifacts
    @property
    def concepts_dir(self) -> Path:
        return self.base / "artifacts" / "concepts"

    @property
    def concepts_json(self) -> Path:
        return self.concepts_dir / "concepts.json"

    @property
    def concept_briefs_json(self) -> Path:
        return self.concepts_dir / "concept_briefs.json"

    def concept_md(self, concept_num: int) -> Path:
        return self.concepts_dir / f"concept_{concept_num:02d}.md"

    @property
    def concept_summary_md(self) -> Path:
        return self.concepts_dir / "concept_summary.md"

    # One-pager artifacts
    @property
    def onepagers_dir(self) -> Path:
        return self.base / "artifacts" / "onepagers"

    def onepager_png(self, concept_num: int) -> Path:
        return self.onepagers_dir / f"concept_{concept_num:02d}.png"

    @property
    def onepager_prompts_md(self) -> Path:
        return self.onepagers_dir / "prompts.md"

    @property
    def onepager_variants_dir(self) -> Path:
        return self.onepagers_dir / "variants"

    # Delivery artifacts
    @property
    def delivery_dir(self) -> Path:
        return self.base / "artifacts" / "delivery"

    @property
    def pitch_email_md(self) -> Path:
        return self.delivery_dir / "pitch_email.md"

    @property
    def package_index_md(self) -> Path:
        return self.delivery_dir / "package_index.md"


class ArchivePaths:
    """
    Path manager for archived company research and concepts.
    
    Archive structure:
    archive/
    ├── index.json
    └── companies/
        └── {company_slug}/
            ├── metadata.json
            ├── research/
            ├── concepts/
            └── delivery/
    """

    def __init__(self, company_slug: str):
        self.company_slug = company_slug
        self.base = settings.get_archive_path() / "companies" / company_slug

    @staticmethod
    def index_file() -> Path:
        """Get path to archive index."""
        return settings.get_archive_path() / "index.json"

    def ensure_directories(self) -> None:
        """Create all required directories for this company."""
        directories = [
            self.base,
            self.base / "research",
            self.base / "concepts",
            self.base / "delivery",
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def metadata_json(self) -> Path:
        return self.base / "metadata.json"

    # Research
    @property
    def research_dir(self) -> Path:
        return self.base / "research"

    @property
    def strategic_dossier_json(self) -> Path:
        return self.research_dir / "strategic_dossier.json"

    @property
    def strategic_dossier_md(self) -> Path:
        return self.research_dir / "strategic_dossier.md"

    @property
    def research_raw_md(self) -> Path:
        return self.research_dir / "research_raw.md"

    @property
    def sources_json(self) -> Path:
        return self.research_dir / "sources.json"

    # Concepts
    @property
    def concepts_dir(self) -> Path:
        return self.base / "concepts"

    @property
    def concepts_json(self) -> Path:
        return self.concepts_dir / "concepts.json"

    def concept_md(self, concept_num: int) -> Path:
        return self.concepts_dir / f"concept_{concept_num:02d}.md"

    # One-pager artifacts are intentionally excluded from archive storage.

    # Delivery
    @property
    def delivery_dir(self) -> Path:
        return self.base / "delivery"

    @property
    def pitch_email_md(self) -> Path:
        return self.delivery_dir / "pitch_email.md"

    @property
    def package_index_md(self) -> Path:
        return self.delivery_dir / "package_index.md"


class PromptPaths:
    """Path manager for prompt files."""

    @staticmethod
    def base() -> Path:
        return settings.get_prompts_path()

    # Research prompts
    @staticmethod
    def research_system() -> Path:
        return PromptPaths.base() / "research" / "system.md"

    @staticmethod
    def research_deep_query() -> Path:
        # Use optimized v2 prompt (see PROMPT_GUIDE.md for rationale)
        return PromptPaths.base() / "research" / "deep_research_query_v2.md"

    @staticmethod
    def research_diagnostic() -> Path:
        return PromptPaths.base() / "research" / "diagnostic_framework.md"

    # Creative prompts
    @staticmethod
    def creative_system() -> Path:
        return PromptPaths.base() / "creative" / "system.md"

    @staticmethod
    def creative_concept_generation() -> Path:
        return PromptPaths.base() / "creative" / "concept_generation.md"

    @staticmethod
    def creative_concept_format() -> Path:
        return PromptPaths.base() / "creative" / "concept_format.md"

    @staticmethod
    def creative_treatment_generation() -> Path:
        return PromptPaths.base() / "creative" / "treatment_generation.md"

    @staticmethod
    def creative_self_critique() -> Path:
        return PromptPaths.base() / "creative" / "self_critique.md"

    @staticmethod
    def creative_refinement() -> Path:
        return PromptPaths.base() / "creative" / "refinement.md"

    # AD prompts
    @staticmethod
    def ad_system() -> Path:
        return PromptPaths.base() / "ad" / "system.md"

    @staticmethod
    def ad_onepager_philosophy() -> Path:
        return PromptPaths.base() / "ad" / "onepager_philosophy.md"

    @staticmethod
    def ad_prompt_builder() -> Path:
        return PromptPaths.base() / "ad" / "prompt_builder.md"

    @staticmethod
    def ad_brand_adaptation() -> Path:
        return PromptPaths.base() / "ad" / "brand_adaptation.md"

    @staticmethod
    def ad_onepager_image_template() -> Path:
        return PromptPaths.base() / "ad" / "onepager_image_template.md"

    # Producer prompts
    @staticmethod
    def producer_strategize() -> Path:
        return PromptPaths.base() / "producer" / "strategize.md"

    @staticmethod
    def producer_pitch_email() -> Path:
        return PromptPaths.base() / "producer" / "pitch_email.md"

    @staticmethod
    def producer_quality_gates() -> Path:
        return PromptPaths.base() / "producer" / "quality_gates.md"


# =============================================================================
# FILE I/O UTILITIES
# =============================================================================


async def read_json(path: Path) -> dict[str, Any]:
    """Read and parse a JSON file."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        content = await f.read()
    return json.loads(content)


async def write_json(path: Path, data: dict[str, Any] | list[Any], indent: int = 2) -> None:
    """Write data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, indent=indent, default=str))


async def read_text(path: Path) -> str:
    """Read a text file."""
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        return await f.read()


async def write_text(path: Path, content: str) -> None:
    """Write content to a text file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "w", encoding="utf-8") as f:
        await f.write(content)


async def append_jsonl(path: Path, data: dict[str, Any]) -> None:
    """Append a JSON line to a JSONL file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    async with aiofiles.open(path, "a", encoding="utf-8") as f:
        await f.write(json.dumps(data, default=str) + "\n")


def read_json_sync(path: Path) -> dict[str, Any]:
    """Synchronous JSON read (for startup/config)."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json_sync(path: Path, data: dict[str, Any] | list[Any], indent: int = 2) -> None:
    """Synchronous JSON write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent, default=str)


def read_text_sync(path: Path) -> str:
    """Synchronous text read."""
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def write_text_sync(path: Path, content: str) -> None:
    """Synchronous text write."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
