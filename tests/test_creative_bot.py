"""
Tests for Creative Bot.
"""

import pytest

from src.bots.creative import CreativeBot
from src.core.models import Concept, ConceptBrief, StrategicDossier


class TestCreativeBot:
    """Tests for CreativeBot."""

    @pytest.fixture
    def bot(self):
        """Create a creative bot instance."""
        return CreativeBot()

    @pytest.fixture
    def dossier(self, sample_dossier_data):
        """Create a sample dossier."""
        return StrategicDossier.model_validate(sample_dossier_data)

    @pytest.fixture
    def briefs(self, sample_concept_briefs_data):
        """Create sample concept briefs."""
        return [ConceptBrief.model_validate(b) for b in sample_concept_briefs_data]

    @pytest.mark.asyncio
    async def test_generates_three_concepts(self, bot, dossier, briefs):
        """Test that exactly 3 concepts are generated."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        assert len(concepts) == 3

    @pytest.mark.asyncio
    async def test_concept_ids_are_correct(self, bot, dossier, briefs):
        """Test that concept IDs match expected pattern."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        concept_ids = {c.id for c in concepts}
        assert concept_ids == {"concept_01", "concept_02", "concept_03"}

    @pytest.mark.asyncio
    async def test_concepts_have_six_episodes(self, bot, dossier, briefs):
        """Test that each concept has exactly 6 episode concepts."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        for concept in concepts:
            assert len(concept.episode_concepts) == 6

    @pytest.mark.asyncio
    async def test_concepts_have_valid_structure(self, bot, dossier, briefs):
        """Test that concepts have all required fields."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        for concept in concepts:
            # Basic fields
            assert concept.title
            assert len(concept.hook) >= 10
            assert len(concept.premise) >= 50
            
            # Format
            assert concept.format.series_type
            assert concept.format.episode_length
            assert concept.format.cadence
            
            # Platform strategy
            assert concept.platform_strategy.primary.platform
            assert concept.platform_strategy.primary.rationale
            
            # Why this wins
            assert concept.why_this_wins.strategic_alignment
            assert concept.why_this_wins.competitive_differentiation
            assert concept.why_this_wins.audience_value_proposition
            
            # Execution
            assert concept.execution.complexity
            assert concept.execution.budget_tier
            
            # Risks
            assert len(concept.risks) >= 1

    @pytest.mark.asyncio
    async def test_platform_diversity(self, bot, dossier, briefs):
        """Test that concepts target different platforms."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        platforms = {c.platform_strategy.primary.platform for c in concepts}
        
        # Should have at least 2 different platforms
        assert len(platforms) >= 2

    @pytest.mark.asyncio
    async def test_concept_hooks_are_substantive(self, bot, dossier, briefs):
        """Test that concept hooks pass basic quality check."""
        concepts = await bot.generate_concepts(dossier, briefs, additional_context="")
        
        for concept in concepts:
            # Hook should be a complete sentence
            assert concept.hook.endswith((".", "!", "?"))
            
            # Hook should mention the company or be clearly about them
            # (In real implementation, might check for company name)
            assert len(concept.hook.split()) >= 5
