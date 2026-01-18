"""
Tests for core data models.
"""

import pytest
from pydantic import ValidationError

from src.core.models import (
    BrandIdentity,
    Concept,
    ConceptBrief,
    EpisodeConcept,
    OnePagerSpec,
    Phase,
    RunState,
    StrategicDossier,
    StrategicTension,
    VisualMarkers,
)


class TestStrategicDossier:
    """Tests for StrategicDossier model."""

    def test_valid_dossier(self, sample_dossier_data):
        """Test creating a valid dossier."""
        dossier = StrategicDossier.model_validate(sample_dossier_data)
        
        assert dossier.company_name == "Test Company Inc"
        assert dossier.company_slug == "test-company-inc"
        assert len(dossier.strategic_tensions) == 3
        assert len(dossier.sources) == 5

    def test_dossier_requires_company_name(self, sample_dossier_data):
        """Test that company_name is required."""
        del sample_dossier_data["company_name"]
        
        with pytest.raises(ValidationError):
            StrategicDossier.model_validate(sample_dossier_data)

    def test_tension_id_pattern(self):
        """Test strategic tension ID pattern validation."""
        # Valid ID
        tension = StrategicTension(
            id="tension_01",
            description="Valid tension description here",
            opportunity_type="gap",
            priority_score=3,
        )
        assert tension.id == "tension_01"
        
        # Invalid ID should fail
        with pytest.raises(ValidationError):
            StrategicTension(
                id="invalid_id",
                description="Invalid tension",
                opportunity_type="gap",
                priority_score=3,
            )


class TestConceptBrief:
    """Tests for ConceptBrief model."""

    def test_valid_brief(self, sample_concept_briefs_data):
        """Test creating valid briefs."""
        for brief_data in sample_concept_briefs_data:
            brief = ConceptBrief.model_validate(brief_data)
            assert brief.slot_id in ["01", "02", "03"]

    def test_slot_id_enum(self):
        """Test slot_id only accepts valid values."""
        with pytest.raises(ValidationError):
            ConceptBrief(
                slot_id="04",  # Invalid
                slot_type="safe_bet",
                assigned_tension_id="tension_01",
                strategic_focus="Test focus",
                platform_focus="youtube",
                format_guidance="Test guidance",
                risk_profile="low",
                success_hypothesis="Test hypothesis",
            )


class TestConcept:
    """Tests for Concept model."""

    def test_concept_requires_six_episodes(self):
        """Test that exactly 6 episode concepts are required."""
        base_concept = {
            "id": "concept_01",
            "title": "Test Concept",
            "hook": "This is the hook that makes CMOs care",
            "premise": "This is a longer premise that explains the concept in 2-3 sentences. It provides context and detail.",
            "long_form_extension": "Ruutu+/Katsomo cut, 3x21min broadcast extension.",
            "format": {
                "series_type": "ongoing",
                "episode_length": "10-15 minutes",
                "cadence": "Weekly",
            },
            "platform_strategy": {
                "primary": {
                    "platform": "YouTube",
                    "rationale": "Best for long-form content",
                },
            },
            "series_structure": {
                "recurring_elements": ["Opening hook"],
                "variable_elements": ["Guest"],
                "host_approach": "No host",
            },
            "brand_integration": {
                "philosophy": "Subtle integration",
            },
            "episode_concepts": [],  # Empty - should fail
            "why_this_wins": {
                "strategic_alignment": "Addresses key tension",
                "competitive_differentiation": "Unique approach",
                "audience_value_proposition": "Entertainment value",
            },
            "execution": {
                "complexity": "medium",
                "budget_tier": "mid",
                "timeline_to_first_episode": "8 weeks",
            },
            "risks": [
                {"risk": "Test risk", "mitigation": "Test mitigation"},
            ],
        }
        
        # Should fail with 0 episodes
        with pytest.raises(ValidationError):
            Concept.model_validate(base_concept)
        
        # Should succeed with 6 episodes
        base_concept["episode_concepts"] = [
            {"number": i, "title": f"Episode {i}", "description": f"Description {i}"}
            for i in range(1, 7)
        ]
        concept = Concept.model_validate(base_concept)
        assert len(concept.episode_concepts) == 6


class TestRunState:
    """Tests for RunState model."""

    def test_state_creation(self):
        """Test creating a new run state."""
        state = RunState(
            run_id="20240115_120000",
            company_slug="test-company",
        )
        
        assert state.current_phase == Phase.INPUT
        assert state.concepts == []
        assert state.dossier is None

    def test_phase_advancement(self):
        """Test phase advancement."""
        state = RunState(
            run_id="20240115_120000",
            company_slug="test-company",
        )
        
        state.advance_to(Phase.VALIDATE)
        assert state.current_phase == Phase.VALIDATE
        
        state.advance_to(Phase.RESEARCH)
        assert state.current_phase == Phase.RESEARCH

    def test_phase_history_recording(self):
        """Test phase history recording."""
        state = RunState(
            run_id="20240115_120000",
            company_slug="test-company",
        )
        
        result = state.record_phase_start(Phase.VALIDATE)
        assert result.phase == Phase.VALIDATE
        assert result.success is False
        
        state.record_phase_complete(success=True)
        assert state.phase_history[-1].success is True
