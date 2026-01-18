"""
Tests for Orchestrator components.
"""

import pytest

from src.core.models import ConceptBrief, Phase, StrategicDossier
from src.orchestrator.state_machine import StateMachine
from src.orchestrator.strategize import Strategizer, assign_tensions_to_slots


class TestStateMachine:
    """Tests for StateMachine."""

    def test_valid_transitions(self):
        """Test valid phase transitions."""
        assert StateMachine.can_transition(Phase.INPUT, Phase.VALIDATE)
        assert StateMachine.can_transition(Phase.VALIDATE, Phase.CHECK_ARCHIVE)
        assert StateMachine.can_transition(Phase.RESEARCH, Phase.STRATEGIZE)
        assert StateMachine.can_transition(Phase.CREATE, Phase.VISUALIZE)

    def test_invalid_transitions(self):
        """Test invalid phase transitions are rejected."""
        assert not StateMachine.can_transition(Phase.INPUT, Phase.CREATE)
        assert not StateMachine.can_transition(Phase.VALIDATE, Phase.DONE)
        assert not StateMachine.can_transition(Phase.DONE, Phase.INPUT)

    def test_terminal_states(self):
        """Test terminal state detection."""
        assert StateMachine.is_terminal(Phase.DONE)
        assert StateMachine.is_terminal(Phase.ERROR)
        assert not StateMachine.is_terminal(Phase.CREATE)

    def test_next_phase(self):
        """Test getting next phase."""
        assert StateMachine.get_next_phase(Phase.INPUT) == Phase.VALIDATE
        assert StateMachine.get_next_phase(Phase.VALIDATE) == Phase.CHECK_ARCHIVE
        assert StateMachine.get_next_phase(Phase.RESEARCH) == Phase.STRATEGIZE

    def test_skip_research(self):
        """Test skipping research when cached."""
        # Normal flow goes to research
        assert StateMachine.get_next_phase(Phase.CHECK_ARCHIVE, skip_research=False) == Phase.RESEARCH
        
        # With skip, goes to strategize
        assert StateMachine.get_next_phase(Phase.CHECK_ARCHIVE, skip_research=True) == Phase.STRATEGIZE

    def test_progress_percentage(self):
        """Test progress percentage values."""
        assert StateMachine.get_progress_percentage(Phase.INPUT) == 0
        assert StateMachine.get_progress_percentage(Phase.DONE) == 100
        assert StateMachine.get_progress_percentage(Phase.ERROR) == -1
        
        # Progress should increase through phases
        phases = [Phase.VALIDATE, Phase.CHECK_ARCHIVE, Phase.RESEARCH, 
                  Phase.STRATEGIZE, Phase.CREATE, Phase.VISUALIZE]
        
        prev_progress = -1
        for phase in phases:
            current = StateMachine.get_progress_percentage(phase)
            assert current > prev_progress
            prev_progress = current


class TestStrategizer:
    """Tests for Strategizer."""

    @pytest.fixture
    def dossier(self, sample_dossier_data):
        """Create a sample dossier."""
        return StrategicDossier.model_validate(sample_dossier_data)

    def test_generates_three_briefs(self, dossier):
        """Test that exactly 3 briefs are generated."""
        briefs = assign_tensions_to_slots(dossier)
        
        assert len(briefs) == 3

    def test_brief_slot_types(self, dossier):
        """Test that briefs have correct slot types."""
        briefs = assign_tensions_to_slots(dossier)
        
        slot_types = {b.slot_type.value for b in briefs}
        assert slot_types == {"safe_bet", "challenger", "moonshot"}

    def test_brief_slot_ids(self, dossier):
        """Test that briefs have correct slot IDs."""
        briefs = assign_tensions_to_slots(dossier)
        
        slot_ids = {b.slot_id for b in briefs}
        assert slot_ids == {"01", "02", "03"}

    def test_different_tensions_assigned(self, dossier):
        """Test that each brief gets a different tension."""
        briefs = assign_tensions_to_slots(dossier)
        
        tension_ids = {b.assigned_tension_id for b in briefs}
        assert len(tension_ids) == 3  # All different

    def test_risk_profile_spread(self, dossier):
        """Test that risk profiles are diverse."""
        briefs = assign_tensions_to_slots(dossier)
        
        risk_profiles = {b.risk_profile.value for b in briefs}
        
        # Should have at least 2 different risk levels
        assert len(risk_profiles) >= 2

    def test_platform_focus_assignment(self, dossier):
        """Test that platform focus matches slot type."""
        briefs = assign_tensions_to_slots(dossier)
        
        brief_map = {b.slot_type.value: b for b in briefs}
        
        # Safe bet should be YouTube
        assert brief_map["safe_bet"].platform_focus.value == "youtube"
        
        # Challenger should be TikTok
        assert brief_map["challenger"].platform_focus.value == "tiktok"
        
        # Moonshot should be cross-platform
        assert brief_map["moonshot"].platform_focus.value == "cross_platform"

    def test_success_hypothesis_populated(self, dossier):
        """Test that success hypothesis is populated."""
        briefs = assign_tensions_to_slots(dossier)
        
        for brief in briefs:
            assert len(brief.success_hypothesis) > 20
            assert brief.success_hypothesis.endswith(".")

    def test_handles_minimum_tensions(self):
        """Test handling of exactly 3 tensions."""
        dossier_data = {
            "company_name": "Test",
            "company_slug": "test",
            "brand_identity": {
                "positioning": "Test company positioning",
                "visual_markers": {"primary_color": "#000"},
            },
            "strategic_priorities": [],
            "marketing_posture": {},
            "competitive_analysis": {},
            "strategic_tensions": [
                {"id": "tension_01", "description": "First tension desc", 
                 "opportunity_type": "gap", "priority_score": 5},
                {"id": "tension_02", "description": "Second tension desc", 
                 "opportunity_type": "threat", "priority_score": 4},
                {"id": "tension_03", "description": "Third tension desc", 
                 "opportunity_type": "aspiration", "priority_score": 3},
            ],
            "opportunity_zones": [
                {"id": "opp_01", "description": "Opp", "rationale": "Rat", "risk_level": "low"},
            ],
            "sources": [
                {"title": f"Source {i}", "url": f"http://s{i}.com", "type": "news", 
                 "date_accessed": "2024-01-01"}
                for i in range(5)
            ],
        }
        
        dossier = StrategicDossier.model_validate(dossier_data)
        briefs = assign_tensions_to_slots(dossier)
        
        assert len(briefs) == 3
