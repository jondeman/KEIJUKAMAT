"""
Tests for Research Bot.
"""

import pytest

from src.bots.research import ResearchBot
from src.core.models import StrategicDossier


class TestResearchBot:
    """Tests for ResearchBot."""

    @pytest.fixture
    def bot(self):
        """Create a research bot instance."""
        return ResearchBot()

    @pytest.mark.asyncio
    async def test_mock_research_returns_valid_dossier(self, bot, sample_company_name):
        """Test that mock research returns a valid dossier."""
        dossier, raw_research, artifacts = await bot.research(sample_company_name)
        
        # Should return a valid StrategicDossier
        assert isinstance(dossier, StrategicDossier)
        assert dossier.company_name == sample_company_name
        
        # Should have required elements
        assert len(dossier.strategic_tensions) >= 3
        assert len(dossier.opportunity_zones) >= 1
        assert len(dossier.sources) >= 5
        
        # Raw research should be non-empty
        assert len(raw_research) > 100
        
        # Artifacts should be None for mock research
        assert artifacts is None

    @pytest.mark.asyncio
    async def test_mock_research_creates_valid_slug(self, bot):
        """Test that company slug is properly generated."""
        dossier, _, _ = await bot.research("Acme Corporation Inc.")
        
        # Slug should be lowercase, hyphenated
        assert dossier.company_slug == "acme-corporation-inc"
        assert " " not in dossier.company_slug
        assert dossier.company_slug.islower()

    @pytest.mark.asyncio
    async def test_mock_research_brand_identity(self, bot, sample_company_name):
        """Test that brand identity is populated."""
        dossier, _, _ = await bot.research(sample_company_name)
        
        # Brand identity should have required fields
        assert dossier.brand_identity.positioning
        assert dossier.brand_identity.visual_markers.primary_color
        assert len(dossier.brand_identity.voice_characteristics) > 0

    @pytest.mark.asyncio
    async def test_mock_research_strategic_tensions(self, bot, sample_company_name):
        """Test strategic tensions are properly formed."""
        dossier, _, _ = await bot.research(sample_company_name)
        
        for tension in dossier.strategic_tensions:
            # ID should match pattern
            assert tension.id.startswith("tension_")
            
            # Description should be substantive
            assert len(tension.description) > 20
            
            # Priority should be in range
            assert 1 <= tension.priority_score <= 5
            
            # Should have evidence
            assert len(tension.evidence) > 0

    @pytest.mark.asyncio
    async def test_mock_research_competitive_analysis(self, bot, sample_company_name):
        """Test competitive analysis is populated."""
        dossier, _, _ = await bot.research(sample_company_name)
        
        analysis = dossier.competitive_analysis
        
        # Should have competitors
        assert len(analysis.key_competitors) > 0
        
        # Each competitor should have required fields
        for competitor in analysis.key_competitors:
            assert competitor.name
            assert competitor.content_strategy
            assert competitor.threat_level in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_mock_research_is_deterministic_for_same_input(self, bot):
        """Test that mock research produces consistent structure."""
        dossier1, _, _ = await bot.research("Same Company")
        dossier2, _, _ = await bot.research("Same Company")
        
        # Structure should be the same
        assert len(dossier1.strategic_tensions) == len(dossier2.strategic_tensions)
        assert len(dossier1.sources) == len(dossier2.sources)
