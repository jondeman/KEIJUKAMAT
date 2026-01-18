"""
Producer orchestrator for KonseptiKeiju.

The Producer is the main controller that:
- Validates input
- Manages state transitions
- Coordinates bot execution
- Ensures quality gates pass
- Compiles final delivery
"""

import asyncio
import subprocess
from urllib.parse import quote
from datetime import datetime
from pathlib import Path
from typing import Callable

from src.core.config import settings
from src.core.filesystem import (
    ArchivePaths,
    RunPaths,
    company_folder_name,
    write_json,
    write_text,
)
from src.core.formatters import (
    concept_to_markdown,
    concepts_summary_markdown,
    dossier_to_markdown,
)
from src.core.logger import RunLogger, get_logger
from src.core.models import (
    Concept,
    ConceptBrief,
    OnePagerSpec,
    Phase,
    RunState,
    StrategicDossier,
)
from src.core.state import ArchiveManager, StateManager

from .pitch_composer import compose_pitch_email
from .quality_gates import QualityGateChecker, QualityGateError
from .state_machine import StateMachine
from .strategize import assign_tensions_to_slots

logger = get_logger(__name__)


class ProducerError(Exception):
    """Raised when producer encounters an unrecoverable error."""

    pass


class Producer:
    """
    Main orchestrator for the KonseptiKeiju pipeline.
    
    Usage:
        producer = await Producer.create(
            company_name="Acme Corp",
            user_email="user@example.com",
            access_code="secret",
        )
        await producer.run()
    """

    def __init__(
        self,
        state_manager: StateManager,
        run_paths: RunPaths,
        run_logger: RunLogger,
    ):
        self.state_manager = state_manager
        self.paths = run_paths
        self.run_logger = run_logger
        self.quality_checker = QualityGateChecker()

        # Bot instances (set during run)
        self._research_bot = None
        self._creative_bot = None
        self._ad_bot = None

    @property
    def state(self) -> RunState:
        """Get current run state."""
        return self.state_manager.state

    @classmethod
    async def create(
        cls,
        company_name: str,
        user_email: str,
        access_code: str,
        additional_context: str = "",
    ) -> "Producer":
        """
        Create a new Producer instance with initialized state.
        
        Args:
            company_name: Target company name
            user_email: User's email for delivery
            access_code: Authentication code
            additional_context: Optional context
            
        Returns:
            Initialized Producer
        """
        # Validate access code
        if settings.access_code and access_code != settings.access_code:
            raise ProducerError("Invalid access code")

        # Create state
        state_manager = await StateManager.create_new_run(
            company_name=company_name,
            user_email=user_email,
            access_code=access_code,
            additional_context=additional_context,
        )

        # Set up paths and logger
        run_paths = state_manager.paths
        run_logger = RunLogger(run_paths.logs_file)

        producer = cls(state_manager, run_paths, run_logger)

        run_logger.info(
            "Producer initialized",
            run_id=state_manager.state.run_id,
            company=company_name,
        )

        return producer

    async def run(self) -> None:
        """
        Execute the full pipeline.
        
        Runs through all phases from VALIDATE to DONE,
        handling errors and retries as needed.
        """
        self.run_logger.info("Starting pipeline run", run_id=self.state.run_id)

        try:
            # Initialize bots (lazy import to avoid circular deps)
            await self._initialize_bots()

            # Run phases in sequence
            await self._run_phase(Phase.VALIDATE, self._phase_validate)
            await self._run_phase(Phase.CHECK_ARCHIVE, self._phase_check_archive)

            # Research (may be skipped if cached)
            if self.state.dossier is None:
                await self._run_phase(Phase.RESEARCH, self._phase_research)

            await self._run_phase(Phase.STRATEGIZE, self._phase_strategize)
            await self._run_phase(Phase.CREATE, self._phase_create)
            await self._run_phase(Phase.VISUALIZE, self._phase_visualize)
            await self._run_phase(Phase.COMPOSE_PITCH, self._phase_compose_pitch)
            await self._run_phase(Phase.PACKAGE, self._phase_package)
            await self._run_phase(Phase.DELIVER, self._phase_deliver)

            # Mark complete
            await self.state_manager.advance_phase(Phase.DONE)
            self.run_logger.info("Pipeline completed successfully")

        except Exception as e:
            await self.state_manager.advance_phase(Phase.ERROR)
            self.run_logger.error("Pipeline failed", error=str(e))
            raise

    async def _initialize_bots(self) -> None:
        """Initialize bot instances."""
        from src.bots.ad import ADBot
        from src.bots.creative import CreativeBot
        from src.bots.research import ResearchBot

        self._research_bot = ResearchBot()
        self._creative_bot = CreativeBot()
        self._ad_bot = ADBot()

        self.run_logger.debug("Bots initialized")

    async def _run_phase(
        self,
        phase: Phase,
        handler: Callable,
        max_retries: int = 3,
    ) -> None:
        """
        Run a pipeline phase with retry logic.
        
        Args:
            phase: Phase to execute
            handler: Async handler function
            max_retries: Maximum retry attempts
        """
        await self.state_manager.advance_phase(phase)
        await self.state_manager.start_phase(phase)

        start_time = datetime.utcnow()
        self.run_logger.phase_start(phase.value)

        for attempt in range(max_retries):
            try:
                await handler()
                await self.state_manager.complete_phase(success=True)

                duration_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                self.run_logger.phase_complete(phase.value, True, duration_ms)
                return

            except QualityGateError as e:
                self.run_logger.warning(
                    f"Quality gate failed (attempt {attempt + 1}/{max_retries})",
                    phase=phase.value,
                    errors=e.errors,
                )
                if attempt == max_retries - 1:
                    await self.state_manager.complete_phase(
                        success=False,
                        error=f"Quality gate failed: {'; '.join(e.errors)}",
                    )
                    raise

            except Exception as e:
                self.run_logger.error(
                    f"Phase error (attempt {attempt + 1}/{max_retries})",
                    phase=phase.value,
                    error=str(e),
                )
                if attempt == max_retries - 1:
                    await self.state_manager.complete_phase(
                        success=False,
                        error=str(e),
                    )
                    raise

                # Brief pause before retry
                await asyncio.sleep(2 ** attempt)

    # =========================================================================
    # PHASE HANDLERS
    # =========================================================================

    async def _phase_validate(self) -> None:
        """Validate input phase."""
        user_input = self.state.user_input

        if not user_input:
            raise ProducerError("No user input provided")

        if not user_input.company_name:
            raise ProducerError("Company name is required")

        if not user_input.user_email:
            raise ProducerError("User email is required")

        self.run_logger.info("Input validated", company=user_input.company_name)

    async def _phase_check_archive(self) -> None:
        """Check archive for existing research."""
        company_slug = self.state.company_slug

        if await ArchiveManager.check_exists(company_slug):
            dossier = await ArchiveManager.load_dossier(company_slug)

            if dossier:
                self.state.dossier = dossier
                self.state.archive_ref = company_slug
                await self.state_manager.save()

                self.run_logger.info(
                    "Loaded research from archive",
                    company=company_slug,
                    tensions=len(dossier.strategic_tensions),
                )
                return

        self.run_logger.info("No cached research found", company=company_slug)

    async def _phase_research(self) -> None:
        """
        Execute research phase.
        
        Pipeline:
        1. Run Deep Research via ResearchBot
        2. ResearchBot internally uses Synthesizer to parse + analyze
        3. Synthesizer saves all artifacts (raw, sections, analysis, dossier)
        4. Quality gate validates output
        5. Archive for future reuse
        """
        assert self._research_bot is not None

        company_name = self.state.user_input.company_name
        additional_context = self.state.user_input.additional_context

        # Run research with full artifact tracking
        # The ResearchBot now uses ResearchSynthesizer internally
        dossier, raw_research, artifacts = await self._research_bot.research(
            company_name=company_name,
            additional_context=additional_context,
            run_dir=self.paths.run_dir,  # Pass run dir for artifact storage
        )

        # Quality gate
        self.quality_checker.check_research_output(dossier)

        # Save to state
        self.state.dossier = dossier
        await self.state_manager.save()

        # Artifacts are now saved by ResearchSynthesizer, but we still save
        # top-level copies for easy access
        await write_json(
            self.paths.strategic_dossier_json,
            dossier.model_dump(mode="json"),
        )
        await write_text(
            self.paths.strategic_dossier_md,
            dossier_to_markdown(dossier),
        )
        if raw_research:
            await write_text(self.paths.research_raw_md, raw_research)

        # Save to archive
        await ArchiveManager.save_to_archive(
            self.state.company_slug,
            dossier,
            raw_research,
        )

        self.run_logger.artifact_created("strategic_dossier", str(self.paths.strategic_dossier_json))
        
        # Log artifact details if available
        if artifacts:
            self.run_logger.info(
                "Research artifacts saved",
                sections_extracted=len(artifacts.extracted_sections),
                prompts_used=list(artifacts.prompts_used.keys()),
            )
        await self._publish_delivery_snapshot("research")

    async def _phase_strategize(self) -> None:
        """Execute strategize phase."""
        assert self.state.dossier is not None

        # Generate concept briefs
        briefs = assign_tensions_to_slots(self.state.dossier)

        # Quality gate
        self.quality_checker.check_strategize_output(briefs)

        # Save to state
        self.state.concept_briefs = briefs
        await self.state_manager.save()

        # Save artifacts
        await write_json(
            self.paths.concept_briefs_json,
            [b.model_dump(mode="json") for b in briefs],
        )

        self.run_logger.artifact_created("concept_briefs", str(self.paths.concept_briefs_json))
        await self._publish_delivery_snapshot("strategize")

    async def _phase_create(self) -> None:
        """Execute create phase."""
        assert self._creative_bot is not None
        assert self.state.dossier is not None
        assert len(self.state.concept_briefs) == 3

        # Generate concepts
        concepts = await self._creative_bot.generate_concepts(
            dossier=self.state.dossier,
            briefs=self.state.concept_briefs,
            additional_context=self.state.user_input.additional_context,
        )

        # Quality gate
        self.quality_checker.check_create_output(concepts)

        # Save to state
        self.state.concepts = concepts
        await self.state_manager.save()

        # Save artifacts
        await write_json(
            self.paths.concepts_json,
            [c.model_dump(mode="json") for c in concepts],
        )

        for concept in concepts:
            num = int(concept.id.split("_")[1])
            await write_text(
                self.paths.concept_md(num),
                concept_to_markdown(concept),
            )

        await write_text(
            self.paths.concept_summary_md,
            concepts_summary_markdown(concepts),
        )

        self.run_logger.artifact_created("concepts", str(self.paths.concepts_json))

        # Generate and save treatments (Finnish) under runs/{company}/TREATMENTS
        treatments = await self._creative_bot.generate_treatments(
            dossier=self.state.dossier,
            briefs=self.state.concept_briefs,
            additional_context=self.state.user_input.additional_context,
        )
        company_folder = company_folder_name(self.state.dossier.company_name)
        treatments_dir = settings.get_runs_path() / company_folder / "TREATMENTS"
        treatments_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        treatment_paths: list[str] = []
        for item in treatments:
            slot_id = item.get("slot_id", "00")
            filename = f"{company_folder}_TREATMENT_{slot_id}_{timestamp}.md"
            path = treatments_dir / filename
            await write_text(path, item.get("content", ""))
            treatment_paths.append(str(path))

        self.run_logger.artifact_created("treatments", str(treatments_dir))
        self.state.treatment_files = treatment_paths
        await self.state_manager.save()
        await self._publish_delivery_snapshot("create")

    async def _phase_visualize(self) -> None:
        """Execute visualize phase."""
        assert self._ad_bot is not None
        assert self.state.dossier is not None
        assert len(self.state.concepts) == 3

        # Prefer treatment-based one-pagers for richer, Puuilo-style layouts
        treatment_paths = self.state.treatment_files or self._resolve_treatment_paths()
        treatments: list[dict[str, str]] = []
        for p in treatment_paths:
            path = Path(p)
            if not path.exists():
                continue
            content = path.read_text(encoding="utf-8")
            title = "Konsepti"
            for line in content.splitlines():
                if line.strip().startswith("# "):
                    title = line.strip().lstrip("# ").strip()
                    break
            slot_id = "00"
            parts = path.stem.split("_")
            if "TREATMENT" in parts:
                try:
                    idx = parts.index("TREATMENT")
                    candidate = parts[idx + 1]
                    if candidate.isdigit():
                        slot_id = candidate.zfill(2)
                except Exception:
                    pass
            treatments.append({"slot_id": slot_id, "title": title, "content": content})

        if treatments:
            specs = await self._ad_bot.generate_onepagers_from_treatments(
                company_name=self.state.dossier.company_name,
                treatments=treatments,
                output_dir=self.paths.onepagers_dir,
                additional_context=self.state.user_input.additional_context,
            )
        else:
            specs = await self._ad_bot.generate_onepagers(
                dossier=self.state.dossier,
                concepts=self.state.concepts,
                output_dir=self.paths.onepagers_dir,
                additional_context=self.state.user_input.additional_context,
            )

        # Quality gate
        self.quality_checker.check_visualize_output(specs, self.paths.onepagers_dir)

        # Save to state
        self.state.onepager_specs = specs
        await self.state_manager.save()

        # Save prompts as separate files (one per concept)
        prompts_dir = self.paths.onepagers_dir / "PROMPTS"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        for spec in specs:
            prompt_md = (
                f"# One-Pager Prompt — {spec.concept_id}\n\n"
                f"## {spec.content.headline}\n\n"
                f"```\n{spec.generation_prompt}\n```\n"
            )
            prompt_path = prompts_dir / f"onepager_prompt_{spec.concept_id}_{timestamp}.md"
            await write_text(prompt_path, prompt_md)

        self.run_logger.artifact_created("onepagers", str(self.paths.onepagers_dir))
        await self._publish_delivery_snapshot("visualize")

    async def _phase_compose_pitch(self) -> None:
        """Execute compose pitch phase."""
        assert self.state.dossier is not None
        assert len(self.state.concepts) == 3

        # Compose email
        pitch_email = compose_pitch_email(
            dossier=self.state.dossier,
            concepts=self.state.concepts,
            user_name="[Your Name]",
            contact_name="[Contact Name]",
            materials_link=self._materials_link(),
        )

        # Quality gate
        self.quality_checker.check_compose_output(pitch_email)

        # Save to state
        self.state.pitch_email = pitch_email
        await self.state_manager.save()

        # Save artifact
        await write_text(self.paths.pitch_email_md, pitch_email)

        self.run_logger.artifact_created("pitch_email", str(self.paths.pitch_email_md))
        await self._publish_delivery_snapshot("compose_pitch")

    async def _phase_package(self) -> None:
        """Execute package phase."""
        # Create package index
        index_content = self._create_package_index()
        await write_text(self.paths.package_index_md, index_content)

        # Copy to archive
        archive_paths = ArchivePaths(self.state.company_slug)
        archive_paths.ensure_directories()

        # Copy concepts
        for concept in self.state.concepts:
            num = int(concept.id.split("_")[1])
            src = self.paths.concept_md(num)
            dst = archive_paths.concept_md(num)
            if src.exists():
                dst.write_text(src.read_text())

        # NOTE: Do not archive one-pager images to avoid large storage usage.

        self.run_logger.artifact_created("package_index", str(self.paths.package_index_md))
        await self._publish_delivery_snapshot("package")

    async def _phase_deliver(self) -> None:
        """Execute deliver phase."""
        from src.integrations.email.client import EmailClient

        delivery_dir = await self._build_delivery_site()
        await self._publish_delivery_to_github(delivery_dir, message_suffix="deliver")
        self._cleanup_run_onepagers()
        materials_link = self._materials_link()
        if materials_link == "[Materials Link]":
            self.run_logger.warning("Delivery base URL not configured; links will be placeholder")

        # Compose a delivery email with links
        subject = f"KonseptiKeiju: {self.state.user_input.company_name} – Materiaalit"
        body = self._compose_delivery_email(materials_link)

        client = EmailClient()
        sent = await client.send_delivery(
            to_email=self.state.user_input.user_email,
            subject=subject,
            body=body,
            attachments=None,
        )

        self.run_logger.info(
            "Delivery ready",
            run_id=self.state.run_id,
            email=self.state.user_input.user_email,
            delivery_dir=str(delivery_dir),
            email_sent=sent,
        )

    async def _publish_delivery_snapshot(self, phase: str) -> None:
        """Incrementally publish delivery artifacts to GitHub Pages."""
        if not settings.github_token or not settings.github_repo:
            return
        try:
            delivery_dir = await self._build_delivery_site()
            await self._publish_delivery_to_github(delivery_dir, message_suffix=phase)
        except Exception as exc:
            self.run_logger.warning("Incremental GitHub publish failed", phase=phase, error=str(exc))

    async def _publish_delivery_to_github(self, delivery_dir: Path, message_suffix: str | None = None) -> None:
        """Push delivery files to GitHub Pages repo if configured."""
        token = settings.github_token
        repo = settings.github_repo
        if not token or not repo:
            self.run_logger.info("GitHub publish skipped (token/repo not configured)")
            return

        repo_root = settings.project_root
        deliveries_dir = settings.get_delivery_pages_dir()
        if not deliveries_dir.exists():
            self.run_logger.warning("GitHub publish skipped (delivery dir missing)")
            return

        def _redact_secret(value: str, secret: str | None) -> str:
            if not value or not secret:
                return value
            redacted = value.replace(secret, "***")
            try:
                encoded = quote(secret, safe="")
                redacted = redacted.replace(encoded, "***")
            except Exception:
                pass
            return redacted

        try:
            encoded_token = quote(token, safe="")
            remote_url = f"https://x-access-token:{encoded_token}@github.com/{repo}.git"

            if settings.git_user_name:
                subprocess.run(
                    ["git", "-C", str(repo_root), "config", "user.name", settings.git_user_name],
                    check=True,
                )
            if settings.git_user_email:
                subprocess.run(
                    ["git", "-C", str(repo_root), "config", "user.email", settings.git_user_email],
                    check=True,
                )

            # Ensure "origin" exists (Render deploys may not have remotes)
            has_origin = subprocess.run(
                ["git", "-C", str(repo_root), "remote", "get-url", "origin"],
                check=False,
                capture_output=True,
                text=True,
            )
            if has_origin.returncode != 0:
                subprocess.run(
                    ["git", "-C", str(repo_root), "remote", "add", "origin", remote_url],
                    check=True,
                )
            else:
                subprocess.run(
                    ["git", "-C", str(repo_root), "remote", "set-url", "origin", remote_url],
                    check=True,
                )

            status = subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "status",
                    "--porcelain",
                    "--untracked-files=all",
                    str(deliveries_dir),
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            changes = [line for line in status.stdout.splitlines() if line.strip()]
            if not changes:
                self.run_logger.info("GitHub publish skipped (no delivery changes)", file_count=0)
                return
            self.run_logger.info(
                "GitHub publish detected delivery changes",
                file_count=len(changes),
            )

            subprocess.run(
                ["git", "-C", str(repo_root), "add", str(deliveries_dir)],
                check=True,
            )
            suffix = f" ({message_suffix})" if message_suffix else ""
            message = f"Update deliveries: {self.state.company_slug}/{self.state.run_id}{suffix}"
            subprocess.run(
                ["git", "-C", str(repo_root), "commit", "-m", message],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo_root), "fetch", "origin", settings.github_branch],
                check=True,
            )
            subprocess.run(
                ["git", "-C", str(repo_root), "rebase", "--autostash", f"origin/{settings.github_branch}"],
                check=True,
            )
            subprocess.run(
                [
                    "git",
                    "-C",
                    str(repo_root),
                    "push",
                    "origin",
                    f"HEAD:{settings.github_branch}",
                ],
                check=True,
            )
            self.run_logger.info("GitHub publish complete", branch=settings.github_branch)
        except Exception as exc:
            self.run_logger.error(
                "GitHub publish failed",
                error=_redact_secret(str(exc), token),
            )

    def _cleanup_run_onepagers(self) -> None:
        """Remove large one-pager images from run folder after delivery."""
        try:
            for i in range(1, 4):
                path = self.paths.onepager_png(i)
                if path.exists():
                    path.unlink()
            variants_dir = self.paths.onepager_variants_dir
            if variants_dir.exists():
                for file in variants_dir.glob("*.png"):
                    file.unlink()
        except Exception as exc:
            self.run_logger.warning("Failed to cleanup run one-pagers", error=str(exc))

    def _create_package_index(self) -> str:
        """Create the package index markdown."""
        company = self.state.dossier.company_name if self.state.dossier else "Unknown"

        lines = [
            f"# Concept Package: {company}",
            "",
            f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*",
            f"*Run ID: {self.state.run_id}*",
            "",
            "---",
            "",
            "## Contents",
            "",
            "### Research",
            f"- [Strategic Dossier](research/strategic_dossier.md)",
            "",
            "### Concepts",
        ]

        for concept in self.state.concepts:
            num = int(concept.id.split("_")[1])
            lines.append(f"- [Concept {num}: {concept.title}](concepts/concept_{num:02d}.md)")

        lines.extend([
            "",
            "### Visual One-Pagers",
            "- [Concept 1 One-Pager](onepagers/concept_01.png)",
            "- [Concept 2 One-Pager](onepagers/concept_02.png)",
            "- [Concept 3 One-Pager](onepagers/concept_03.png)",
            "",
            "### Delivery",
            "- [Pitch Email Draft](delivery/pitch_email.md)",
        ])
        if self.paths.additional_context_md.exists():
            lines.append("- [Lisähuomiot](delivery/additional_context.md)")
        lines.append("")

        return "\n".join(lines)

    def _materials_link(self) -> str:
        base = (settings.delivery_base_url or "").rstrip("/")
        if not base:
            return "[Materials Link]"
        return f"{base}/{self.state.company_slug}/{self.state.run_id}/index.html"

    async def _build_delivery_site(self) -> Path:
        """Build a GitHub Pages-ready delivery folder with links."""
        import zipfile

        company_slug = self.state.company_slug
        run_id = self.state.run_id
        base_dir = settings.get_delivery_pages_dir()
        target_dir = base_dir / company_slug / run_id

        research_dir = target_dir / "research"
        concepts_dir = target_dir / "concepts"
        treatments_dir = target_dir / "treatments"
        onepagers_dir = target_dir / "onepagers"
        delivery_dir = target_dir / "delivery"

        for d in (research_dir, concepts_dir, treatments_dir, onepagers_dir, delivery_dir):
            d.mkdir(parents=True, exist_ok=True)

        # Copy research artifacts
        if self.paths.strategic_dossier_md.exists():
            (research_dir / "strategic_dossier.md").write_text(
                self.paths.strategic_dossier_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        if self.paths.research_raw_md.exists():
            (research_dir / "research_raw.md").write_text(
                self.paths.research_raw_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        # Copy treatments
        for treatment_path in self._resolve_treatment_paths():
            src = Path(treatment_path)
            if src.exists():
                (treatments_dir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")

        # Copy concept markdowns (if available)
        for i in range(1, 4):
            src = self.paths.concept_md(i)
            if src.exists():
                (concepts_dir / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        if self.paths.concept_summary_md.exists():
            (concepts_dir / self.paths.concept_summary_md.name).write_text(
                self.paths.concept_summary_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        # Copy one-pagers
        for i in range(1, 4):
            src = self.paths.onepager_png(i)
            if src.exists():
                (onepagers_dir / src.name).write_bytes(src.read_bytes())

        # Copy pitch email and package index
        if self.paths.pitch_email_md.exists():
            (delivery_dir / "pitch_email.md").write_text(
                self.paths.pitch_email_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        if self.paths.package_index_md.exists():
            (delivery_dir / "package_index.md").write_text(
                self.paths.package_index_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
        if self.paths.additional_context_md.exists():
            (delivery_dir / "additional_context.md").write_text(
                self.paths.additional_context_md.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

        # Build a single download archive for the entire delivery
        zip_path = target_dir / "outputs.zip"
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
            for folder in (research_dir, concepts_dir, treatments_dir, onepagers_dir, delivery_dir):
                for file in folder.rglob("*"):
                    if file.is_file():
                        zipf.write(file, file.relative_to(target_dir))

        index_md = self._create_delivery_index()
        (target_dir / "index.md").write_text(index_md, encoding="utf-8")
        (target_dir / "index.html").write_text(self._markdown_to_simple_html(index_md), encoding="utf-8")

        return target_dir

    def _resolve_treatment_paths(self) -> list[str]:
        if self.state.treatment_files:
            return self.state.treatment_files

        # Fallback: try latest treatments from runs/{company}/TREATMENTS
        company_folder = company_folder_name(self.state.user_input.company_name)
        treatments_dir = settings.get_runs_path() / company_folder / "TREATMENTS"
        if not treatments_dir.exists():
            return []

        treatment_files = sorted(treatments_dir.glob(f"{company_folder}_TREATMENT_*.md"), reverse=True)
        timestamps = set()
        for f in treatment_files:
            parts = f.stem.split("_")
            if len(parts) >= 4:
                timestamp = "_".join(parts[-2:])
                timestamps.add(timestamp)
        latest_timestamp = sorted(timestamps, reverse=True)[0] if timestamps else None
        if not latest_timestamp:
            return []

        matches = []
        for slot_id in ["01", "02", "03"]:
            pattern = f"{company_folder}_TREATMENT_{slot_id}_{latest_timestamp}.md"
            for match in treatments_dir.glob(pattern):
                matches.append(str(match))
        return matches

    def _create_delivery_index(self) -> str:
        company = self.state.user_input.company_name
        run_id = self.state.run_id
        lines = [
            f"# KonseptiKeiju Delivery — {company}",
            "",
            f"*Run ID: {run_id}*",
            "",
            "## Lataa kaikki",
            "- [Lataa kaikki (zip)](outputs.zip)",
            "",
            "## Research",
            "- [Strategic Dossier](research/strategic_dossier.md)",
            "- [Raw Research](research/research_raw.md)",
            "",
            "## Concepts",
            "- [Concept Summary](concepts/concept_summary.md)",
            "- [Concept 01](concepts/concept_01.md)",
            "- [Concept 02](concepts/concept_02.md)",
            "- [Concept 03](concepts/concept_03.md)",
            "",
            "## Treatments",
        ]

        for path in self._resolve_treatment_paths():
            name = Path(path).name
            lines.append(f"- [{name}](treatments/{name})")

        lines.extend([
            "",
            "## One-Pagers",
            "- [One-Pager 01](onepagers/concept_01.png)",
            "- [One-Pager 02](onepagers/concept_02.png)",
            "- [One-Pager 03](onepagers/concept_03.png)",
            "",
            "## Delivery",
            "- [Pitch Email](delivery/pitch_email.md)",
            "- [Package Index](delivery/package_index.md)",
        ])
        if self.paths.additional_context_md.exists():
            lines.append("- [Lisähuomiot](delivery/additional_context.md)")
        lines.append("")
        return "\n".join(lines)

    def _markdown_to_simple_html(self, md: str) -> str:
        """Minimal markdown-to-HTML for simple link pages."""
        lines = []
        for raw in md.splitlines():
            if raw.startswith("# "):
                lines.append(f"<h1>{raw[2:]}</h1>")
            elif raw.startswith("## "):
                lines.append(f"<h2>{raw[3:]}</h2>")
            elif raw.startswith("- ["):
                # format: - [Text](url)
                text = raw.split("[", 1)[1].split("]", 1)[0]
                url = raw.split("(", 1)[1].split(")", 1)[0]
                lines.append(f'<li><a href="{url}">{text}</a></li>')
            elif raw.strip() == "":
                lines.append("")
            else:
                lines.append(f"<p>{raw}</p>")

        # Wrap list items in a UL
        html_lines = []
        in_list = False
        for line in lines:
            if line.startswith("<li>") and not in_list:
                html_lines.append("<ul>")
                in_list = True
            if not line.startswith("<li>") and in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(line)
        if in_list:
            html_lines.append("</ul>")

        body = "\n".join(html_lines)
        return f"<!DOCTYPE html><html><head><meta charset=\"utf-8\"><title>KonseptiKeiju Delivery</title></head><body>{body}</body></html>"

    def _compose_delivery_email(self, materials_link: str) -> str:
        company = self.state.user_input.company_name
        dossier = self.state.dossier
        concepts = self.state.concepts or []

        # Research highlights (keep tight and useful for selling)
        tension_lines = []
        if dossier and dossier.strategic_tensions:
            for t in sorted(dossier.strategic_tensions, key=lambda x: x.priority_score, reverse=True)[:3]:
                tension_lines.append(f"- {t.description}")
        opportunity_lines = []
        if dossier and dossier.opportunity_zones:
            for o in dossier.opportunity_zones[:3]:
                opportunity_lines.append(f"- {o.description}")

        research_block = ""
        if tension_lines or opportunity_lines:
            parts = []
            if tension_lines:
                parts.append("Tärkeimmät jännitteet:\n" + "\n".join(tension_lines))
            if opportunity_lines:
                parts.append("Isoimmat mahdollisuudet:\n" + "\n".join(opportunity_lines))
            research_block = "\n\n" + "\n\n".join(parts)

        # Concept highlights with short “why these”
        concept_lines = []
        for concept in concepts:
            why = (concept.why_this_wins.strategic_alignment or "").strip()
            if len(why) > 180:
                why = why[:177].rstrip() + "..."
            if not why:
                why = "Ratkaisee keskeisen strategisen jännitteen ja on selkeästi toteutettava."
            concept_lines.append(f"- {concept.title}: {why}")
        concepts_block = ""
        if concept_lines:
            concepts_block = "\n\nLuodut konseptit ja miksi juuri nämä:\n" + "\n".join(concept_lines)

        base_url = (settings.delivery_base_url or "").rstrip("/")
        base_line = f"Toimitusrepo: {base_url}\n\n" if base_url else ""
        return (
            f"Hei!\n\n"
            f"Tässä KonseptiKeiju -materiaalit yritykselle {company}.\n\n"
            f"{base_line}"
            f"Materiaalit (tämä ajo): {materials_link}\n\n"
            f"Tiivis nosto tutkimuksesta ja konseptien valinnasta:{research_block}{concepts_block}\n\n"
            f"Sisältö:\n"
            f"- Tutkimus (strateginen dossier + raw)\n"
            f"- 3 treatmenttia\n"
            f"- 3 onepageria (A4)\n\n"
            f"Terveisin,\nKonseptiKeiju"
        )
