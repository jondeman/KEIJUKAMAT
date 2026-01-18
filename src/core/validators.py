"""
Schema validation utilities for KonseptiKeiju.

Validates data structures against JSON schemas and Pydantic models
to ensure data integrity at phase boundaries.
"""

from pathlib import Path
from typing import Any

import jsonschema

from .config import settings
from .models import Concept, ConceptBrief, OnePagerSpec, StrategicDossier


class ValidationError(Exception):
    """Raised when validation fails."""

    def __init__(self, message: str, errors: list[str] | None = None):
        super().__init__(message)
        self.errors = errors or []


def load_schema(schema_name: str) -> dict[str, Any]:
    """
    Load a JSON schema from the schemas directory.
    
    Args:
        schema_name: Name of the schema file (without extension)
        
    Returns:
        Parsed JSON schema
    """
    schema_path = settings.project_root / "schemas" / f"{schema_name}.schema.json"
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    import json
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_against_schema(data: dict[str, Any], schema_name: str) -> list[str]:
    """
    Validate data against a JSON schema.
    
    Args:
        data: Data to validate
        schema_name: Name of the schema to validate against
        
    Returns:
        List of validation error messages (empty if valid)
    """
    try:
        schema = load_schema(schema_name)
    except FileNotFoundError:
        return [f"Schema '{schema_name}' not found"]
    
    errors = []
    validator = jsonschema.Draft7Validator(schema)
    
    for error in validator.iter_errors(data):
        path = ".".join(str(p) for p in error.absolute_path)
        if path:
            errors.append(f"{path}: {error.message}")
        else:
            errors.append(error.message)
    
    return errors


def validate_dossier(dossier: StrategicDossier | dict[str, Any]) -> list[str]:
    """
    Validate a strategic dossier.
    
    Args:
        dossier: Dossier to validate (model or dict)
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    # Convert to dict if needed
    if isinstance(dossier, StrategicDossier):
        data = dossier.model_dump(mode="json")
        dossier_obj = dossier
    else:
        data = dossier
        try:
            dossier_obj = StrategicDossier.model_validate(data)
        except Exception as e:
            return [f"Failed to parse dossier: {e}"]
    
    # Validate against schema
    schema_errors = validate_against_schema(data, "strategic_dossier")
    errors.extend(schema_errors)
    
    # Business logic validation
    if len(dossier_obj.strategic_tensions) < 3:
        errors.append(
            f"At least 3 strategic tensions required, found {len(dossier_obj.strategic_tensions)}"
        )
    
    if len(dossier_obj.opportunity_zones) < 1:
        errors.append(
            f"At least 1 opportunity zone required, found {len(dossier_obj.opportunity_zones)}"
        )
    
    if len(dossier_obj.sources) < 5:
        errors.append(f"At least 5 sources required, found {len(dossier_obj.sources)}")
    
    if not dossier_obj.brand_identity.visual_markers.primary_color:
        errors.append("Primary brand color is required")
    
    return errors


def validate_concept_briefs(briefs: list[ConceptBrief] | list[dict[str, Any]]) -> list[str]:
    """
    Validate concept briefs.
    
    Args:
        briefs: List of briefs to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if len(briefs) != 3:
        errors.append(f"Exactly 3 concept briefs required, found {len(briefs)}")
        return errors
    
    # Convert to models if needed
    brief_objs = []
    for i, brief in enumerate(briefs):
        if isinstance(brief, ConceptBrief):
            brief_objs.append(brief)
        else:
            try:
                brief_objs.append(ConceptBrief.model_validate(brief))
            except Exception as e:
                errors.append(f"Brief {i + 1}: Failed to parse - {e}")
    
    if errors:
        return errors
    
    # Check slot IDs are unique and correct
    slot_ids = {b.slot_id for b in brief_objs}
    if slot_ids != {"01", "02", "03"}:
        errors.append(f"Slot IDs must be '01', '02', '03', found {slot_ids}")
    
    # Check risk profile spread
    risk_levels = {b.risk_profile.value for b in brief_objs}
    if len(risk_levels) < 2:
        errors.append("Risk profiles should have variety (at least 2 different levels)")
    
    # Check tension assignments are different
    tensions = {b.assigned_tension_id for b in brief_objs}
    if len(tensions) < 3:
        errors.append("Each brief should address a different strategic tension")
    
    return errors


def validate_concepts(concepts: list[Concept] | list[dict[str, Any]]) -> list[str]:
    """
    Validate concepts from Creative Bot.
    
    Args:
        concepts: List of concepts to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if len(concepts) != 3:
        errors.append(f"Exactly 3 concepts required, found {len(concepts)}")
        return errors
    
    # Convert to models if needed
    concept_objs = []
    for i, concept in enumerate(concepts):
        if isinstance(concept, Concept):
            concept_objs.append(concept)
        else:
            try:
                concept_objs.append(Concept.model_validate(concept))
            except Exception as e:
                errors.append(f"Concept {i + 1}: Failed to parse - {e}")
    
    if errors:
        return errors
    
    # Check IDs are unique and correct
    concept_ids = {c.id for c in concept_objs}
    if concept_ids != {"concept_01", "concept_02", "concept_03"}:
        errors.append(f"Concept IDs must be 'concept_01/02/03', found {concept_ids}")
    
    # Check each concept has required elements
    for concept in concept_objs:
        if len(concept.hook) < 10:
            errors.append(f"{concept.id}: Hook is too short (must capture CMO attention)")
        
        if not concept.long_form_extension or len(concept.long_form_extension.strip()) < 10:
            errors.append(f"{concept.id}: Missing long-form extension (Ruutu+/Katsomo/Total-TV)")

        if len(concept.episode_concepts) != 6:
            errors.append(f"{concept.id}: Must have exactly 6 episode concepts")
        
        if not concept.why_this_wins.strategic_alignment:
            errors.append(f"{concept.id}: Missing strategic alignment explanation")
    
    # Check platforms are diverse
    primary_platforms = {c.platform_strategy.primary.platform for c in concept_objs}
    if len(primary_platforms) < 2:
        errors.append("Concepts should target different primary platforms")
    
    return errors


def validate_onepager_specs(specs: list[OnePagerSpec] | list[dict[str, Any]]) -> list[str]:
    """
    Validate one-pager specifications.
    
    Args:
        specs: List of specs to validate
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if len(specs) != 3:
        errors.append(f"Exactly 3 one-pager specs required, found {len(specs)}")
        return errors
    
    # Convert to models if needed
    spec_objs = []
    for i, spec in enumerate(specs):
        if isinstance(spec, OnePagerSpec):
            spec_objs.append(spec)
        else:
            try:
                spec_objs.append(OnePagerSpec.model_validate(spec))
            except Exception as e:
                errors.append(f"Spec {i + 1}: Failed to parse - {e}")
    
    if errors:
        return errors
    
    # Check each spec
    for spec in spec_objs:
        if not spec.generation_prompt:
            errors.append(f"{spec.concept_id}: Missing generation prompt")
        
        if len(spec.content.headline) > 50:
            errors.append(f"{spec.concept_id}: Headline too long (max 50 chars)")
        
        if len(spec.content.bullets) > 4:
            errors.append(f"{spec.concept_id}: Too many bullets (max 4)")
    
    return errors


def validate_onepager_files(onepager_dir: Path) -> list[str]:
    """
    Validate generated one-pager image files.
    
    Args:
        onepager_dir: Directory containing generated images
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    required_files = [
        onepager_dir / "concept_01.png",
        onepager_dir / "concept_02.png",
        onepager_dir / "concept_03.png",
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            errors.append(f"Missing one-pager: {file_path.name}")
        else:
            # Check file size (should be > 100KB for a real image)
            size_kb = file_path.stat().st_size / 1024
            if size_kb < 100:
                errors.append(
                    f"{file_path.name}: File too small ({size_kb:.1f}KB), "
                    "may be corrupted or blank"
                )
    
    return errors


class QualityGate:
    """
    Quality gate checker for phase transitions.
    
    Each phase transition requires passing specific quality checks.
    """

    @staticmethod
    def research_to_strategize(dossier: StrategicDossier) -> tuple[bool, list[str]]:
        """Check if research output passes quality gate."""
        errors = validate_dossier(dossier)
        return len(errors) == 0, errors

    @staticmethod
    def strategize_to_create(briefs: list[ConceptBrief]) -> tuple[bool, list[str]]:
        """Check if strategize output passes quality gate."""
        errors = validate_concept_briefs(briefs)
        return len(errors) == 0, errors

    @staticmethod
    def create_to_visualize(concepts: list[Concept]) -> tuple[bool, list[str]]:
        """Check if create output passes quality gate."""
        errors = validate_concepts(concepts)
        return len(errors) == 0, errors

    @staticmethod
    def visualize_to_compose(specs: list[OnePagerSpec], onepager_dir: Path) -> tuple[bool, list[str]]:
        """Check if visualize output passes quality gate."""
        errors = validate_onepager_specs(specs)
        errors.extend(validate_onepager_files(onepager_dir))
        return len(errors) == 0, errors

    @staticmethod
    def compose_to_package(pitch_email: str) -> tuple[bool, list[str]]:
        """Check if compose output passes quality gate."""
        errors = []
        
        if len(pitch_email) < 100:
            errors.append("Pitch email is too short")
        
        if "strategic hypothesis" not in pitch_email.lower():
            errors.append("Pitch email missing strategic hypothesis")
        
        return len(errors) == 0, errors
