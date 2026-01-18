"""
Strategic tension to concept slot assignment.

The Strategizer takes a Strategic Dossier and assigns tensions
to the three concept slots with appropriate risk profiles.
"""

from src.core.logger import get_logger
from src.core.models import (
    ConceptBrief,
    PlatformFocus,
    RiskLevel,
    SlotType,
    StrategicDossier,
    StrategicTension,
)

logger = get_logger(__name__)


class Strategizer:
    """
    Assigns strategic tensions to concept slots.
    
    The three slots follow a deliberate spread:
    - Slot 01 (Safe Bet): Address top strategic priority, low risk
    - Slot 02 (Challenger): Attack competitive pressure or gap, medium risk
    - Slot 03 (Moonshot): Unlock latent opportunity, high risk
    """

    def __init__(self, dossier: StrategicDossier):
        self.dossier = dossier
        self.tensions = sorted(
            dossier.strategic_tensions,
            key=lambda t: t.priority_score,
            reverse=True,
        )
        self.opportunities = dossier.opportunity_zones

    def generate_briefs(self) -> list[ConceptBrief]:
        """
        Generate three concept briefs from the strategic dossier.
        
        Returns:
            List of three ConceptBrief objects
        """
        if len(self.tensions) < 3:
            raise ValueError(
                f"Need at least 3 strategic tensions, found {len(self.tensions)}"
            )

        briefs = [
            self._create_safe_bet_brief(),
            self._create_challenger_brief(),
            self._create_moonshot_brief(),
        ]

        logger.info(
            "Generated concept briefs",
            company=self.dossier.company_name,
            tensions_assigned=[b.assigned_tension_id for b in briefs],
        )

        return briefs

    def _create_safe_bet_brief(self) -> ConceptBrief:
        """
        Create the Safe Bet brief (Slot 01).
        
        Addresses the #1 strategic priority with a proven, low-risk format.
        Primary platform: YouTube long-form.
        """
        # Select highest priority tension
        tension = self.tensions[0]

        return ConceptBrief(
            slot_id="01",
            slot_type=SlotType.SAFE_BET,
            assigned_tension_id=tension.id,
            strategic_focus=self._summarize_tension(tension),
            platform_focus=PlatformFocus.YOUTUBE,
            format_guidance=self._get_safe_bet_format_guidance(tension),
            risk_profile=RiskLevel.LOW,
            success_hypothesis=self._generate_hypothesis(tension, "safe"),
        )

    def _create_challenger_brief(self) -> ConceptBrief:
        """
        Create the Challenger brief (Slot 02).
        
        Attacks a competitive pressure point or addresses a gap.
        Primary platform: TikTok/Reels-first.
        """
        # Find a tension related to competition or gaps
        tension = self._find_challenger_tension()

        return ConceptBrief(
            slot_id="02",
            slot_type=SlotType.CHALLENGER,
            assigned_tension_id=tension.id,
            strategic_focus=self._summarize_tension(tension),
            platform_focus=PlatformFocus.TIKTOK,
            format_guidance=self._get_challenger_format_guidance(tension),
            risk_profile=RiskLevel.MEDIUM,
            success_hypothesis=self._generate_hypothesis(tension, "challenger"),
        )

    def _create_moonshot_brief(self) -> ConceptBrief:
        """
        Create the Moonshot brief (Slot 03).
        
        Unlocks a latent opportunity with high differentiation potential.
        Primary platform: Cross-platform event.
        """
        # Find most intriguing opportunity or underserved audience tension
        tension = self._find_moonshot_tension()

        return ConceptBrief(
            slot_id="03",
            slot_type=SlotType.MOONSHOT,
            assigned_tension_id=tension.id,
            strategic_focus=self._summarize_tension(tension),
            platform_focus=PlatformFocus.CROSS_PLATFORM,
            format_guidance=self._get_moonshot_format_guidance(tension),
            risk_profile=RiskLevel.HIGH,
            success_hypothesis=self._generate_hypothesis(tension, "moonshot"),
        )

    def _find_challenger_tension(self) -> StrategicTension:
        """Find the best tension for the Challenger slot."""
        # Prefer tensions related to competition or gaps
        for tension in self.tensions[1:]:  # Skip the first (used for safe bet)
            if tension.opportunity_type.value in ("threat", "gap"):
                return tension

        # Fallback to second highest priority
        return self.tensions[1]

    def _find_moonshot_tension(self) -> StrategicTension:
        """Find the best tension for the Moonshot slot."""
        # Get tensions already used
        used_ids = {self.tensions[0].id, self._find_challenger_tension().id}

        # Prefer underserved audience or aspiration tensions
        for tension in self.tensions:
            if tension.id in used_ids:
                continue
            if tension.opportunity_type.value in ("underserved_audience", "aspiration"):
                return tension

        # Fallback to any unused tension
        for tension in self.tensions:
            if tension.id not in used_ids:
                return tension

        # Last resort: third tension
        return self.tensions[2]

    def _summarize_tension(self, tension: StrategicTension) -> str:
        """Create a one-sentence summary of a tension."""
        return tension.description[:200]  # Truncate if too long

    def _generate_hypothesis(self, tension: StrategicTension, slot_type: str) -> str:
        """
        Generate a success hypothesis explaining why the CMO would care.
        """
        brand = self.dossier.company_name
        opp_type = tension.opportunity_type.value.replace("_", " ")

        if slot_type == "safe":
            return (
                f"This concept directly addresses {brand}'s top strategic priority "
                f"({opp_type}) with a proven format that minimizes execution risk "
                "while delivering measurable brand value."
            )
        elif slot_type == "challenger":
            return (
                f"This concept enables {brand} to aggressively address their {opp_type} "
                "with bold positioning that differentiates them in the market and "
                "captures attention on high-engagement platforms."
            )
        else:  # moonshot
            return (
                f"This concept unlocks an untapped opportunity for {brand} by addressing "
                f"their {opp_type} in a way that creates cultural relevance and "
                "positions the brand as an innovator in their space."
            )

    def _get_safe_bet_format_guidance(self, tension: StrategicTension) -> str:
        """Get format guidance for safe bet concepts."""
        return (
            "Focus on proven YouTube formats: documentary-style, interview series, "
            "or educational content. Episodes should be 8-15 minutes. "
            "Prioritize professional production quality and clear brand alignment. "
            "The series should have obvious rewatch and share value."
        )

    def _get_challenger_format_guidance(self, tension: StrategicTension) -> str:
        """Get format guidance for challenger concepts."""
        return (
            "Design for TikTok/Reels first: vertical format, 30-90 seconds, "
            "hook in first 3 seconds. Embrace platform-native aesthetics and trends. "
            "Consider creator collaborations. Content should feel bold and contemporary, "
            "not like traditional brand advertising."
        )

    def _get_moonshot_format_guidance(self, tension: StrategicTension) -> str:
        """Get format guidance for moonshot concepts."""
        return (
            "Think beyond single-platform content: interactive experiences, "
            "live events with digital extensions, user participation mechanics, "
            "or innovative cross-platform storytelling. This should feel like "
            "something the industry hasn't seen before. High production ambition "
            "is acceptable given the differentiation potential."
        )


def assign_tensions_to_slots(dossier: StrategicDossier) -> list[ConceptBrief]:
    """
    Convenience function to assign tensions to concept slots.
    
    Args:
        dossier: Strategic dossier with tensions
        
    Returns:
        List of three concept briefs
    """
    strategizer = Strategizer(dossier)
    return strategizer.generate_briefs()
