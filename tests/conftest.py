"""
Pytest configuration and fixtures for Concept Forge tests.
"""

import asyncio
import os
from pathlib import Path

import pytest

# Ensure we're using mock APIs in tests
os.environ["USE_MOCK_APIS"] = "true"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def sample_company_name() -> str:
    """Sample company name for testing."""
    return "Test Company Inc"


@pytest.fixture
def sample_user_email() -> str:
    """Sample email for testing."""
    return "test@example.com"


@pytest.fixture
def sample_access_code() -> str:
    """Sample access code for testing."""
    return "test_code"


@pytest.fixture
def sample_dossier_data() -> dict:
    """Sample strategic dossier data."""
    return {
        "company_name": "Test Company Inc",
        "company_slug": "test-company-inc",
        "brand_identity": {
            "positioning": "Test Company is a leader in test products.",
            "visual_markers": {
                "primary_color": "#1a73e8",
                "secondary_colors": ["#34a853"],
                "style_keywords": ["modern", "clean"],
                "tone_keywords": ["professional"],
            },
            "voice_characteristics": ["Confident", "Clear"],
        },
        "strategic_priorities": [
            {
                "rank": 1,
                "priority": "Market expansion",
                "evidence": ["Press release about new markets"],
                "execution_assessment": "moderate",
            },
        ],
        "marketing_posture": {
            "current_content_types": ["Product videos"],
            "channel_presence": {
                "youtube": {"active": True, "assessment": "Good engagement"},
            },
            "apparent_gaps": ["No TikTok presence"],
            "audience_engagement": "Above average",
        },
        "competitive_analysis": {
            "key_competitors": [
                {
                    "name": "Competitor A",
                    "content_strategy": "Heavy video content",
                    "threat_level": "high",
                },
            ],
            "brand_winning_areas": ["Product quality"],
            "brand_losing_areas": ["Social presence"],
        },
        "strategic_tensions": [
            {
                "id": "tension_01",
                "description": "Youth audience gap despite youth-focused products",
                "evidence": ["Low engagement from under-30s"],
                "opportunity_type": "gap",
                "priority_score": 5,
            },
            {
                "id": "tension_02",
                "description": "Competitor content dominance",
                "evidence": ["Competitor has 3x YouTube subscribers"],
                "opportunity_type": "threat",
                "priority_score": 4,
            },
            {
                "id": "tension_03",
                "description": "Sustainability story untold",
                "evidence": ["Strong credentials, weak content"],
                "opportunity_type": "aspiration",
                "priority_score": 3,
            },
        ],
        "opportunity_zones": [
            {
                "id": "opp_01",
                "description": "TikTok-first content series",
                "rationale": "No current presence, open field",
                "risk_level": "medium",
            },
        ],
        "sources": [
            {
                "title": "Company Website",
                "url": "https://testcompany.com",
                "type": "company_site",
                "date_accessed": "2024-01-15",
                "relevance": "Primary source",
            },
            {
                "title": "YouTube Channel",
                "url": "https://youtube.com/@testcompany",
                "type": "video",
                "date_accessed": "2024-01-15",
                "relevance": "Content analysis",
            },
            {
                "title": "News Article 1",
                "url": "https://news.example.com/1",
                "type": "news",
                "date_accessed": "2024-01-15",
                "relevance": "Strategy insight",
            },
            {
                "title": "News Article 2",
                "url": "https://news.example.com/2",
                "type": "news",
                "date_accessed": "2024-01-15",
                "relevance": "Market analysis",
            },
            {
                "title": "Industry Report",
                "url": "https://reports.example.com/1",
                "type": "report",
                "date_accessed": "2024-01-15",
                "relevance": "Industry context",
            },
        ],
    }


@pytest.fixture
def sample_concept_briefs_data() -> list:
    """Sample concept briefs data."""
    return [
        {
            "slot_id": "01",
            "slot_type": "safe_bet",
            "assigned_tension_id": "tension_01",
            "strategic_focus": "Address youth audience gap",
            "platform_focus": "youtube",
            "format_guidance": "Long-form documentary content",
            "risk_profile": "low",
            "success_hypothesis": "Captures youth through authentic storytelling",
        },
        {
            "slot_id": "02",
            "slot_type": "challenger",
            "assigned_tension_id": "tension_02",
            "strategic_focus": "Counter competitor dominance",
            "platform_focus": "tiktok",
            "format_guidance": "Short-form viral content",
            "risk_profile": "medium",
            "success_hypothesis": "Disrupts competitor advantage",
        },
        {
            "slot_id": "03",
            "slot_type": "moonshot",
            "assigned_tension_id": "tension_03",
            "strategic_focus": "Tell untold sustainability story",
            "platform_focus": "cross_platform",
            "format_guidance": "Interactive cross-platform experience",
            "risk_profile": "high",
            "success_hypothesis": "Creates cultural moment around values",
        },
    ]
