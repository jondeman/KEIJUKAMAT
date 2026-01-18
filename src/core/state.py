"""
Run state management for KonseptiKeiju.

Handles loading, saving, and managing pipeline run state with support
for resumability and error recovery.
"""

from datetime import datetime
from pathlib import Path

from .filesystem import (
    ArchivePaths,
    RunPaths,
    generate_run_id,
    read_json,
    slugify,
    write_json,
    write_text,
)
from .logger import get_logger
from .models import Phase, RunState, StrategicDossier, UserInput

logger = get_logger(__name__)


class StateManager:
    """
    Manages the state of a pipeline run.
    
    Responsibilities:
    - Creating new runs
    - Loading existing runs (for resumability)
    - Persisting state changes
    - Archive lookup and storage
    """

    def __init__(self, run_paths: RunPaths):
        self.paths = run_paths
        self._state: RunState | None = None

    @property
    def state(self) -> RunState:
        """Get current run state."""
        if self._state is None:
            raise RuntimeError("State not initialized. Call create_run() or load_run() first.")
        return self._state

    @classmethod
    async def create_new_run(
        cls,
        company_name: str,
        user_email: str,
        access_code: str,
        additional_context: str = "",
    ) -> "StateManager":
        """
        Create a new pipeline run.
        
        Args:
            company_name: Name of the target company
            user_email: User's email for delivery
            access_code: Authentication code
            additional_context: Optional additional context
            
        Returns:
            StateManager instance with initialized state
        """
        run_id = generate_run_id()
        company_slug = slugify(company_name)
        
        paths = RunPaths(run_id, company_slug)
        paths.ensure_directories()
        
        manager = cls(paths)
        
        # Create initial state
        manager._state = RunState(
            run_id=run_id,
            company_slug=company_slug,
            user_input=UserInput(
                company_name=company_name,
                user_email=user_email,
                access_code=access_code,
                additional_context=additional_context,
            ),
        )
        
        # Save initial state
        await manager.save()

        # Save additional context for traceability
        if additional_context.strip():
            await write_text(
                manager.paths.additional_context_md,
                "# Lisähuomiot (käyttäjän antama)\n\n" + additional_context.strip(),
            )
        
        logger.info(
            "Created new run",
            run_id=run_id,
            company=company_name,
            slug=company_slug,
        )
        
        return manager

    @classmethod
    async def load_run(cls, run_dir: Path) -> "StateManager":
        """
        Load an existing run from disk.
        
        Args:
            run_dir: Path to the run directory
            
        Returns:
            StateManager instance with loaded state
        """
        # Parse run directory name to extract components
        # Format: {YYYY-MM-DD}_{company_slug}_{run_id}
        dir_name = run_dir.name
        parts = dir_name.split("_")
        
        if len(parts) < 3:
            raise ValueError(f"Invalid run directory name: {dir_name}")
        
        # Last part is run_id, first part is date, middle is slug
        run_id = parts[-1]
        company_slug = "_".join(parts[1:-1])
        
        paths = RunPaths(run_id, company_slug)
        paths.base = run_dir  # Override base path
        
        manager = cls(paths)
        
        # Load state from file
        state_data = await read_json(paths.state_file)
        manager._state = RunState.model_validate(state_data)
        
        logger.info(
            "Loaded existing run",
            run_id=run_id,
            company=company_slug,
            phase=manager._state.current_phase.value,
        )
        
        return manager

    async def save(self) -> None:
        """Persist current state to disk."""
        self.state.updated_at = datetime.utcnow()
        await write_json(
            self.paths.state_file,
            self.state.model_dump(mode="json"),
        )
        logger.debug("State saved", phase=self.state.current_phase.value)

    async def advance_phase(self, new_phase: Phase) -> None:
        """
        Advance to a new phase.
        
        Args:
            new_phase: The phase to advance to
        """
        old_phase = self.state.current_phase
        self.state.advance_to(new_phase)
        await self.save()
        
        logger.info(
            "Phase transition",
            from_phase=old_phase.value,
            to_phase=new_phase.value,
        )

    async def start_phase(self, phase: Phase) -> None:
        """
        Record the start of a phase.
        
        Args:
            phase: The phase being started
        """
        self.state.record_phase_start(phase)
        await self.save()
        
        logger.info("Phase started", phase=phase.value)

    async def complete_phase(self, success: bool, error: str | None = None) -> None:
        """
        Record the completion of the current phase.
        
        Args:
            success: Whether the phase completed successfully
            error: Optional error message if failed
        """
        self.state.record_phase_complete(success, error)
        await self.save()
        
        if success:
            logger.info("Phase completed", phase=self.state.current_phase.value)
        else:
            logger.error(
                "Phase failed",
                phase=self.state.current_phase.value,
                error=error,
            )


class ArchiveManager:
    """
    Manages the archive of completed research and concepts.
    
    The archive serves as a cache to avoid re-running expensive
    research for companies we've already analyzed.
    """

    @staticmethod
    async def check_exists(company_slug: str) -> bool:
        """Check if archived research exists for a company."""
        paths = ArchivePaths(company_slug)
        return paths.strategic_dossier_json.exists()

    @staticmethod
    async def load_dossier(company_slug: str) -> StrategicDossier | None:
        """
        Load archived strategic dossier for a company.
        
        Args:
            company_slug: Company slug to look up
            
        Returns:
            StrategicDossier if found, None otherwise
        """
        paths = ArchivePaths(company_slug)
        
        if not paths.strategic_dossier_json.exists():
            return None
        
        try:
            data = await read_json(paths.strategic_dossier_json)
            dossier = StrategicDossier.model_validate(data)
            
            logger.info(
                "Loaded dossier from archive",
                company=company_slug,
                generated_at=str(dossier.generated_at),
            )
            
            return dossier
        except Exception as e:
            logger.warning(
                "Failed to load archived dossier",
                company=company_slug,
                error=str(e),
            )
            return None

    @staticmethod
    async def save_to_archive(
        company_slug: str,
        dossier: StrategicDossier,
        raw_research: str = "",
    ) -> None:
        """
        Save research results to archive.
        
        Args:
            company_slug: Company slug
            dossier: Strategic dossier to archive
            raw_research: Raw research output to preserve
        """
        paths = ArchivePaths(company_slug)
        paths.ensure_directories()
        
        # Save structured dossier
        await write_json(
            paths.strategic_dossier_json,
            dossier.model_dump(mode="json"),
        )
        
        # Save human-readable markdown
        from .formatters import dossier_to_markdown
        markdown = dossier_to_markdown(dossier)
        paths.strategic_dossier_md.write_text(markdown, encoding="utf-8")
        
        # Save raw research if provided
        if raw_research:
            paths.research_raw_md.write_text(raw_research, encoding="utf-8")
        
        # Save sources separately for reference
        sources_data = [s.model_dump(mode="json") for s in dossier.sources]
        await write_json(paths.sources_json, sources_data)
        
        # Update archive index
        await ArchiveManager._update_index(company_slug, dossier)
        
        logger.info("Saved to archive", company=company_slug)

    @staticmethod
    async def _update_index(company_slug: str, dossier: StrategicDossier) -> None:
        """Update the archive index with new entry."""
        index_path = ArchivePaths.index_file()
        
        # Load existing index or create new
        if index_path.exists():
            index = await read_json(index_path)
        else:
            index = {"companies": {}}
        
        # Update entry
        index["companies"][company_slug] = {
            "company_name": dossier.company_name,
            "last_updated": datetime.utcnow().isoformat(),
            "tension_count": len(dossier.strategic_tensions),
            "source_count": len(dossier.sources),
        }
        
        # Save updated index
        index_path.parent.mkdir(parents=True, exist_ok=True)
        await write_json(index_path, index)

    @staticmethod
    async def list_archived_companies() -> list[str]:
        """List all archived company slugs."""
        companies_dir = ArchivePaths("").base.parent
        
        if not companies_dir.exists():
            return []
        
        return [
            d.name for d in companies_dir.iterdir()
            if d.is_dir() and (d / "research" / "strategic_dossier.json").exists()
        ]
