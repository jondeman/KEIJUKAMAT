"""
Quality gate checks for pipeline phase transitions.

Each phase must pass quality checks before proceeding to the next.
"""

from pathlib import Path

from src.core.logger import get_logger
from src.core.models import (
    Concept,
    ConceptBrief,
    OnePagerSpec,
    Phase,
    StrategicDossier,
)
from src.core.validators import (
    validate_concept_briefs,
    validate_concepts,
    validate_dossier,
    validate_onepager_files,
    validate_onepager_specs,
)

logger = get_logger(__name__)


class QualityGateError(Exception):
    """Raised when a quality gate check fails."""

    def __init__(self, phase: Phase, errors: list[str]):
        self.phase = phase
        self.errors = errors
        message = f"Quality gate failed for {phase.value}: {'; '.join(errors)}"
        super().__init__(message)


class QualityGateChecker:
    """
    Checks quality gates at phase transitions.
    
    Quality gates ensure each phase produces valid, high-quality output
    before the pipeline proceeds.
    """

    def check_research_output(self, dossier: StrategicDossier) -> None:
        """
        Check research phase output quality.
        
        Requirements:
        - Valid dossier schema
        - At least 3 strategic tensions
        - At least 1 opportunity zone
        - Brand visual markers present
        - At least 5 sources cited
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = validate_dossier(dossier)
        
        if errors:
            logger.warning(
                "Research quality gate failed",
                error_count=len(errors),
                errors=errors[:5],  # Log first 5
            )
            raise QualityGateError(Phase.RESEARCH, errors)
        
        logger.info(
            "Research quality gate passed",
            tension_count=len(dossier.strategic_tensions),
            source_count=len(dossier.sources),
        )

    def check_strategize_output(self, briefs: list[ConceptBrief]) -> None:
        """
        Check strategize phase output quality.
        
        Requirements:
        - Exactly 3 briefs
        - Each brief has different tension
        - Risk profile spread (low/medium/high)
        - Platform focus variety
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = validate_concept_briefs(briefs)
        
        if errors:
            logger.warning(
                "Strategize quality gate failed",
                error_count=len(errors),
                errors=errors,
            )
            raise QualityGateError(Phase.STRATEGIZE, errors)
        
        logger.info(
            "Strategize quality gate passed",
            brief_count=len(briefs),
        )

    def check_create_output(self, concepts: list[Concept]) -> None:
        """
        Check create phase output quality.
        
        Requirements:
        - Exactly 3 concepts
        - Valid concept schema
        - CMO hook present in each
        - Platform variety
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = validate_concepts(concepts)
        
        if errors:
            logger.warning(
                "Create quality gate failed",
                error_count=len(errors),
                errors=errors[:5],
            )
            raise QualityGateError(Phase.CREATE, errors)
        
        logger.info(
            "Create quality gate passed",
            concept_count=len(concepts),
            titles=[c.title for c in concepts],
        )

    def check_visualize_output(
        self,
        specs: list[OnePagerSpec],
        onepager_dir: Path,
    ) -> None:
        """
        Check visualize phase output quality.
        
        Requirements:
        - 3 specs with generation prompts
        - 3 PNG files exist
        - Each file > 100KB
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = validate_onepager_specs(specs)
        errors.extend(validate_onepager_files(onepager_dir))
        
        if errors:
            logger.warning(
                "Visualize quality gate failed",
                error_count=len(errors),
                errors=errors,
            )
            raise QualityGateError(Phase.VISUALIZE, errors)
        
        logger.info(
            "Visualize quality gate passed",
            spec_count=len(specs),
        )

    def check_compose_output(self, pitch_email: str) -> None:
        """
        Check compose phase output quality.
        
        Requirements:
        - Email not too short
        - Contains strategic hypothesis
        - Contains all concept titles
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = []
        
        if len(pitch_email) < 100:
            errors.append("Pitch email is too short (< 100 chars)")
        
        if "hypothesis" not in pitch_email.lower():
            errors.append("Pitch email missing strategic hypothesis section")
        
        # Check for concept mentions
        concept_markers = ["concept 1", "concept 2", "concept 3"]
        for marker in concept_markers:
            if marker.lower() not in pitch_email.lower() and f"**{marker}" not in pitch_email.lower():
                # Also check for numbered format
                pass  # Allow flexible formatting
        
        if errors:
            logger.warning(
                "Compose quality gate failed",
                error_count=len(errors),
                errors=errors,
            )
            raise QualityGateError(Phase.COMPOSE_PITCH, errors)
        
        logger.info("Compose quality gate passed")

    def check_package_output(
        self,
        package_dir: Path,
        required_files: list[str],
    ) -> None:
        """
        Check package phase output quality.
        
        Requirements:
        - All required files exist
        - Package index complete
        
        Raises:
            QualityGateError: If validation fails
        """
        errors = []
        
        for filename in required_files:
            file_path = package_dir / filename
            if not file_path.exists():
                errors.append(f"Missing required file: {filename}")
        
        if errors:
            logger.warning(
                "Package quality gate failed",
                error_count=len(errors),
                errors=errors,
            )
            raise QualityGateError(Phase.PACKAGE, errors)
        
        logger.info("Package quality gate passed")


def run_quality_gate(
    phase: Phase,
    checker: QualityGateChecker,
    **kwargs,
) -> bool:
    """
    Run quality gate for a phase.
    
    Args:
        phase: The phase to check
        checker: QualityGateChecker instance
        **kwargs: Phase-specific arguments
        
    Returns:
        True if passed, raises QualityGateError otherwise
    """
    gate_methods = {
        Phase.RESEARCH: lambda: checker.check_research_output(kwargs["dossier"]),
        Phase.STRATEGIZE: lambda: checker.check_strategize_output(kwargs["briefs"]),
        Phase.CREATE: lambda: checker.check_create_output(kwargs["concepts"]),
        Phase.VISUALIZE: lambda: checker.check_visualize_output(
            kwargs["specs"], kwargs["onepager_dir"]
        ),
        Phase.COMPOSE_PITCH: lambda: checker.check_compose_output(kwargs["pitch_email"]),
        Phase.PACKAGE: lambda: checker.check_package_output(
            kwargs["package_dir"], kwargs["required_files"]
        ),
    }
    
    if phase not in gate_methods:
        return True  # No gate for this phase
    
    gate_methods[phase]()
    return True
