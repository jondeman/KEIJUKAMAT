"""
Pitch email composer for KonseptiKeiju.

Generates the email that accompanies delivery materials,
explaining why these concepts matter to the recipient.
"""

from jinja2 import Template

from src.core.logger import get_logger
from src.core.models import Concept, StrategicDossier

logger = get_logger(__name__)


# Email template
PITCH_EMAIL_TEMPLATE = """Subject: Three video concepts for {{ company_name }} — addressing {{ key_challenge }}

---

Hi {{ contact_name }},

I've been studying {{ company_name }}'s recent marketing activities and strategic direction, and I noticed {{ observation }}.

Based on this analysis, I've developed three branded entertainment concepts that I believe could help {{ company_name }} achieve {{ strategic_goal }}:

**Concept 1: "{{ concept_1_title }}"**
{{ concept_1_hook }}

**Concept 2: "{{ concept_2_title }}"**
{{ concept_2_hook }}

**Concept 3: "{{ concept_3_title }}"**
{{ concept_3_hook }}

I've attached visual one-pagers for each concept, along with detailed format specifications.

---

## Strategic Hypothesis

{{ strategic_hypothesis }}

---

I'd welcome 15 minutes to walk through these ideas and get your initial reactions.

Best,
{{ user_name }}

---

📎 Attachments:
- Concept 1 One-Pager ({{ concept_1_title }}.png)
- Concept 2 One-Pager ({{ concept_2_title }}.png)
- Concept 3 One-Pager ({{ concept_3_title }}.png)
- Detailed Concept Documents (PDF)

[Link to full materials folder: {{ materials_link }}]
"""


class PitchComposer:
    """
    Composes pitch emails from research and concepts.
    
    The pitch email is the first thing the CMO reads, so it must:
    1. Demonstrate research/homework
    2. Clearly articulate the strategic connection
    3. Tease concepts without giving everything away
    """

    def __init__(
        self,
        dossier: StrategicDossier,
        concepts: list[Concept],
        user_name: str = "[Your Name]",
        contact_name: str = "[Contact Name]",
        materials_link: str = "[Link]",
    ):
        self.dossier = dossier
        self.concepts = sorted(concepts, key=lambda c: c.id)
        self.user_name = user_name
        self.contact_name = contact_name
        self.materials_link = materials_link

    def compose(self) -> str:
        """
        Generate the pitch email.
        
        Returns:
            Formatted email content as markdown
        """
        template = Template(PITCH_EMAIL_TEMPLATE)

        context = {
            "company_name": self.dossier.company_name,
            "key_challenge": self._extract_key_challenge(),
            "contact_name": self.contact_name,
            "observation": self._extract_observation(),
            "strategic_goal": self._extract_strategic_goal(),
            "concept_1_title": self.concepts[0].title,
            "concept_1_hook": self.concepts[0].hook,
            "concept_2_title": self.concepts[1].title,
            "concept_2_hook": self.concepts[1].hook,
            "concept_3_title": self.concepts[2].title,
            "concept_3_hook": self.concepts[2].hook,
            "strategic_hypothesis": self._generate_hypothesis(),
            "user_name": self.user_name,
            "materials_link": self.materials_link,
        }

        email = template.render(**context)

        logger.info(
            "Composed pitch email",
            company=self.dossier.company_name,
            char_count=len(email),
        )

        return email

    def _extract_key_challenge(self) -> str:
        """Extract the primary challenge from research."""
        if self.dossier.strategic_tensions:
            top_tension = max(
                self.dossier.strategic_tensions,
                key=lambda t: t.priority_score,
            )
            # Summarize in a few words
            desc = top_tension.description
            if len(desc) > 50:
                desc = desc[:47] + "..."
            return desc
        return "brand differentiation"

    def _extract_observation(self) -> str:
        """Extract a specific observation showing homework was done."""
        observations = []

        # Look for gaps in marketing posture
        if self.dossier.marketing_posture.apparent_gaps:
            gap = self.dossier.marketing_posture.apparent_gaps[0]
            observations.append(f"an opportunity in {gap.lower()}")

        # Look at strategic priorities
        if self.dossier.strategic_priorities:
            top = self.dossier.strategic_priorities[0]
            observations.append(
                f"a strong focus on {top.priority.lower()} "
                f"with {top.execution_assessment.value} execution so far"
            )

        # Look at competitive analysis
        if self.dossier.competitive_analysis.brand_losing_areas:
            area = self.dossier.competitive_analysis.brand_losing_areas[0]
            observations.append(f"competitive pressure in {area.lower()}")

        if observations:
            return observations[0]
        return "significant opportunities for branded content"

    def _extract_strategic_goal(self) -> str:
        """Extract the strategic goal concepts are targeting."""
        if self.dossier.strategic_priorities:
            top = self.dossier.strategic_priorities[0]
            return f"stronger positioning in {top.priority.lower()}"
        return "enhanced brand engagement through video content"

    def _generate_hypothesis(self) -> str:
        """Generate the strategic hypothesis paragraph."""
        company = self.dossier.company_name

        # Build hypothesis from tensions and opportunities
        parts = []

        # Opening
        parts.append(
            f"Based on my research into {company}'s current positioning and market dynamics, "
            "I believe there's a significant opportunity in branded entertainment that "
            "addresses three distinct strategic needs:"
        )

        # Address each concept's strategic angle
        for i, concept in enumerate(self.concepts, 1):
            why = concept.why_this_wins.strategic_alignment
            parts.append(f"\n\n**{i}. {concept.title}** addresses {why.lower()}")

        # Closing
        parts.append(
            f"\n\nTogether, these concepts represent a portfolio approach—from "
            f"low-risk proven formats to bold differentiators—giving {company} "
            "options across the risk spectrum while maintaining strategic coherence."
        )

        return "".join(parts)


def compose_pitch_email(
    dossier: StrategicDossier,
    concepts: list[Concept],
    user_name: str = "[Your Name]",
    contact_name: str = "[Contact Name]",
    materials_link: str = "[Link]",
) -> str:
    """
    Convenience function to compose a pitch email.
    
    Args:
        dossier: Strategic dossier
        concepts: List of concepts
        user_name: Name to sign the email
        contact_name: Recipient name
        materials_link: Link to materials folder
        
    Returns:
        Formatted email content
    """
    composer = PitchComposer(
        dossier=dossier,
        concepts=concepts,
        user_name=user_name,
        contact_name=contact_name,
        materials_link=materials_link,
    )
    return composer.compose()
