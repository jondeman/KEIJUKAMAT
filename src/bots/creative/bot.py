"""
Creative Bot - The Concept Architect.

Transforms strategic briefs into compelling, executable video concepts
using Claude Opus 4.5.
"""

from src.core.config import settings
from src.core.filesystem import PromptPaths, read_text_sync
from src.core.logger import get_logger
from src.core.models import (
    BrandIntegration,
    BudgetTier,
    Concept,
    ConceptBrief,
    EpisodeConcept,
    ExecutionSpec,
    FormatSpec,
    PlatformSpec,
    PlatformStrategy,
    ProductionComplexity,
    Risk,
    SeriesStructure,
    SeriesType,
    StrategicDossier,
    WhyThisWins,
)
from src.core.prompt_logger import log_prompt

logger = get_logger(__name__)


class CreativeBot:
    """
    Creative Bot for generating video concepts.
    
    Takes strategic briefs and produces fully-developed
    video series concepts.
    """

    def __init__(self):
        self.use_mock = settings.use_mock_apis or not settings.has_anthropic_key()
        
        if self.use_mock:
            logger.info("Creative Bot initialized in MOCK mode")
        else:
            logger.info("Creative Bot initialized with Claude API")

    async def generate_concepts(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
        additional_context: str = "",
    ) -> list[Concept]:
        """
        Generate video concepts from briefs.
        
        Args:
            dossier: Strategic dossier with brand context
            briefs: Three concept briefs from Strategizer
            
        Returns:
            List of three Concept objects
        """
        if self.use_mock:
            return await self._mock_generate(dossier, briefs)
        else:
            return await self._real_generate(dossier, briefs, additional_context)

    async def generate_treatments(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
        additional_context: str = "",
    ) -> list[dict[str, str]]:
        """
        Generate treatment texts (Finnish) for three concepts.

        Returns:
            List of dicts with keys: slot_id, title, content
        """
        if self.use_mock:
            return await self._mock_treatments(dossier, briefs)
        return await self._real_treatments(dossier, briefs, additional_context)

    async def generate_treatments_from_raw(
        self,
        company_name: str,
        raw_research_md: str,
        additional_context: str = "",
    ) -> list[dict[str, str]]:
        """
        Generate 3 treatments directly from raw research markdown (no dossier required).

        IMPORTANT: This must not trigger any new research calls. It only uses the provided raw input.
        """
        from src.integrations.claude import ClaudeClient

        system_prompt = read_text_sync(PromptPaths.creative_system())
        treatment_prompt = read_text_sync(PromptPaths.creative_treatment_generation())

        # Slot design: safe / challenger / moonshot
        slots = [
            {
                "slot_id": "01",
                "slot_type": "SAFE_BET",
                "risk_profile": "low",
                "platform_focus": "youtube",
                "direction": "Varmasti toimiva, laajaa yleisöä keräävä formaatti. Hyödyntää brändin asiantuntijuutta ja yhteisöllisyyttä.",
            },
            {
                "slot_id": "02",
                "slot_type": "CHALLENGER",
                "risk_profile": "medium",
                "platform_focus": "tiktok/instagram",
                "direction": "Rohkea, keskustelua synnyttävä ja jaettava idea. Tuo brändin 'media itse' -ajattelun esiin.",
            },
            {
                "slot_id": "03",
                "slot_type": "MOONSHOT",
                "risk_profile": "high",
                "platform_focus": "cross-platform + live/event",
                "direction": "Innovatiivinen 'uusi media' -kokonaisuus (esim. live, stunt, PR, UGC), joka voi tehdä brändistä puheenaiheen.",
            },
        ]

        client = ClaudeClient()
        treatments: list[dict[str, str]] = []

        for s in slots:
            variant = self._slot_prompt_variant(
                slot_id=s["slot_id"],
                slot_type=s["slot_type"],
                risk_profile=s["risk_profile"],
                platform_focus=s["platform_focus"],
            )
            extra = self._format_additional_context(additional_context)
            prompt = f"""{treatment_prompt}

## Yritys
{company_name}

## Raaka tutkimus (input)
{raw_research_md}

{extra}

## Tämä slotti (pakolliset reunaehdot)
- Konseptislotti: {s["slot_id"]} / {s["slot_type"]}
- Riskiprofiili: {s["risk_profile"]}
- Pääkanava-fokus: {s["platform_focus"]}
- Luova suunta: {s["direction"]}

## Lisäpainotus (tämä erottaa slotit)
{variant}
"""
            response = await client.creative_generate(prompt=prompt, system=system_prompt)
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}" if system_prompt else prompt
            log_prompt(
                category="creative",
                prompt_type="treatment_generation",
                prompt=full_prompt,
                metadata={
                    "model": settings.claude_model,
                    "company": company_name,
                    "slot_id": s["slot_id"],
                },
                response=response,
            )
            content = response.strip()
            title = self._extract_title(content, fallback=f"Konsepti {s['slot_id']}")
            treatments.append({"slot_id": s["slot_id"], "title": title, "content": content})

        return treatments

    async def _mock_generate(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
    ) -> list[Concept]:
        """Generate mock concepts for testing."""
        logger.info("Generating mock concepts", company=dossier.company_name)
        
        company = dossier.company_name
        concepts = []
        
        # Concept 1: Safe Bet (YouTube long-form)
        concepts.append(Concept(
            id="concept_01",
            title="The Innovation Files",
            hook=f"A documentary series that takes viewers inside {company}'s R&D labs, revealing the human stories behind breakthrough innovations.",
            premise=f"Each episode follows a different team at {company} as they tackle real challenges and push the boundaries of what's possible. From concept to creation, viewers get unprecedented access to the creative process that drives the company's success.",
            format=FormatSpec(
                series_type=SeriesType.ONGOING,
                episode_length="12-15 minutes",
                cadence="Bi-weekly",
                season_length="8 episodes per season",
            ),
            platform_strategy=PlatformStrategy(
                primary=PlatformSpec(
                    platform="YouTube",
                    rationale="Long-form documentary content performs best on YouTube. The platform's algorithm favors watch time, and our in-depth storytelling will maximize engagement metrics.",
                ),
                secondary=[
                    PlatformSpec(
                        platform="LinkedIn",
                        adaptation="3-minute highlight clips focusing on professional insights and leadership perspectives.",
                    ),
                    PlatformSpec(
                        platform="Instagram",
                        adaptation="Behind-the-scenes Reels and carousel posts featuring key moments.",
                    ),
                ],
                amplification="Employee advocacy program to share episodes. Targeted YouTube ads to tech and innovation audiences.",
            ),
            series_structure=SeriesStructure(
                recurring_elements=[
                    "Opening hook showing the end result",
                    "Problem introduction with stakes",
                    "Meet the team segment",
                    "Journey through challenges",
                    "Resolution and reflection",
                ],
                variable_elements=[
                    "Different teams and projects each episode",
                    "Varying locations (labs, offices, field sites)",
                    "Guest expert appearances",
                    "Seasonal themes (sustainability, AI, etc.)",
                ],
                host_approach="No traditional host. Stories are told through the voices of team members themselves, creating authenticity and emotional connection.",
            ),
            brand_integration=BrandIntegration(
                philosophy="The brand is the canvas, not the paint. Products and technology appear naturally as part of the innovation story, never as explicit promotion.",
                integration_method="Organic presence through facility shots, team conversations, and product demonstrations in context.",
                screen_time_balance="70% human stories, 20% process/technology, 10% brand/product visibility",
                cta_approach="Soft CTA at end: 'Learn more about innovation at [company website]' with link in description.",
            ),
            episode_concepts=[
                EpisodeConcept(number=1, title="The 3AM Breakthrough", description="Following an engineering team racing against a deadline to solve a critical sustainability challenge."),
                EpisodeConcept(number=2, title="The Unexpected Solution", description="How a chance conversation in the cafeteria led to a product innovation that changed everything."),
                EpisodeConcept(number=3, title="Failing Forward", description="The story of a project that failed spectacularly—and what the team learned from it."),
                EpisodeConcept(number=4, title="The New Generation", description="Following a group of interns as they pitch their first ideas to senior leadership."),
                EpisodeConcept(number=5, title="Cross-Continental", description="How teams across three continents collaborated on a single project during a global crisis."),
                EpisodeConcept(number=6, title="Customer Zero", description="Tracking a new product from concept to its first real customer, capturing every emotion along the way."),
            ],
            why_this_wins=WhyThisWins(
                strategic_alignment=f"Directly addresses {company}'s need to humanize its innovation narrative and make R&D investment visible to audiences.",
                competitive_differentiation="Competitors focus on product features; this series focuses on the human journey, creating emotional connection that product marketing can't achieve.",
                audience_value_proposition="Viewers get inspiration, behind-the-scenes access, and authentic human stories—content they'd watch even without brand connection.",
            ),
            execution=ExecutionSpec(
                complexity=ProductionComplexity.MEDIUM,
                budget_tier=BudgetTier.MID,
                timeline_to_first_episode="8-10 weeks from greenlight",
            ),
            risks=[
                Risk(
                    risk="Internal stakeholders may be camera-shy or unavailable",
                    mitigation="Pre-production interviews to identify compelling storytellers; build pool of willing participants",
                ),
                Risk(
                    risk="Proprietary information concerns may limit access",
                    mitigation="Clear approval process with legal/comms; focus on human stories rather than trade secrets",
                ),
            ],
        ))
        
        # Concept 2: Challenger (TikTok-first)
        concepts.append(Concept(
            id="concept_02",
            title="60 Second Futures",
            hook=f"A bold TikTok series where {company} predicts and debates what life will look like in 2035—inviting Gen Z to imagine and shape tomorrow.",
            premise=f"Each episode poses a provocative question about the future, featuring quick-cut debates between experts, creators, and everyday people. The series positions {company} at the center of conversations about tomorrow while entertaining today's audiences.",
            format=FormatSpec(
                series_type=SeriesType.ONGOING,
                episode_length="45-90 seconds",
                cadence="3x per week",
                season_length=None,
            ),
            platform_strategy=PlatformStrategy(
                primary=PlatformSpec(
                    platform="TikTok",
                    rationale="The format is designed for TikTok's algorithm: high hook rate, engagement through comments/duets, and share-worthy content that sparks debate.",
                ),
                secondary=[
                    PlatformSpec(
                        platform="Instagram Reels",
                        adaptation="Same content, optimized for Reels' slightly different algorithm preferences.",
                    ),
                    PlatformSpec(
                        platform="YouTube Shorts",
                        adaptation="Compiled 'best of' collections and extended debate cuts.",
                    ),
                ],
                amplification="Creator partnerships for duets and responses. Comment engagement strategy. Trending sound/hashtag optimization.",
            ),
            series_structure=SeriesStructure(
                recurring_elements=[
                    "Opening provocative question (text on screen)",
                    "Quick-cut debate format",
                    "Unexpected twist or perspective",
                    "Call to action for comments",
                ],
                variable_elements=[
                    "Topics range from tech to culture to environment",
                    "Rotating cast of voices",
                    "Format variations (man on street, expert vs. kid, etc.)",
                ],
                host_approach="Rotating young, diverse hosts who feel native to the platform. Anti-corporate aesthetic.",
            ),
            brand_integration=BrandIntegration(
                philosophy="The brand is the convener of conversation, not the subject. Position as curious and forward-thinking, not sales-focused.",
                integration_method="Subtle watermark and end card only. Brand presence is in being the 'host' of important conversations.",
                screen_time_balance="95% content, 5% brand presence (end card and watermark only)",
                cta_approach="No direct CTA. Profile link to brand's future-focused landing page.",
            ),
            episode_concepts=[
                EpisodeConcept(number=1, title="Will We Still Drive?", description="Gen Z vs. Boomers debate the future of transportation in 2035."),
                EpisodeConcept(number=2, title="The Last Office", description="What does 'going to work' mean when everywhere is an office?"),
                EpisodeConcept(number=3, title="AI Best Friend", description="Kids predict what their AI companions will be like. Surprisingly emotional."),
                EpisodeConcept(number=4, title="Future of Food", description="Street food vendors imagine how their craft evolves in 10 years."),
                EpisodeConcept(number=5, title="Digital Afterlife", description="Would you create an AI version of yourself for loved ones? Heated debate."),
                EpisodeConcept(number=6, title="Climate Wins", description="Optimistic scientists share the breakthroughs they're most excited about."),
            ],
            why_this_wins=WhyThisWins(
                strategic_alignment="Directly tackles the youth engagement gap by meeting Gen Z where they are, with content they actually want to watch and share.",
                competitive_differentiation="Competitors are still doing product demos on TikTok. This series makes the brand part of culture, not interrupting it.",
                audience_value_proposition="Thought-provoking, snackable content that sparks conversation and makes viewers look smart when they share it.",
            ),
            execution=ExecutionSpec(
                complexity=ProductionComplexity.LOW,
                budget_tier=BudgetTier.BUDGET,
                timeline_to_first_episode="3-4 weeks from greenlight",
            ),
            risks=[
                Risk(
                    risk="Platform algorithm changes could reduce reach",
                    mitigation="Multi-platform strategy ensures no single platform dependency",
                ),
                Risk(
                    risk="Controversial topics could generate negative commentary",
                    mitigation="Clear content guidelines and active community management",
                ),
            ],
        ))
        
        # Concept 3: Moonshot (Cross-platform event)
        concepts.append(Concept(
            id="concept_03",
            title="The Changemakers Challenge",
            hook=f"A global competition where {company} funds the most ambitious ideas from young innovators—broadcast live and voted on by the audience.",
            premise=f"{company} launches an annual global challenge calling for submissions from under-30 innovators tackling real-world problems. The journey from thousands of applicants to five finalists is documented across platforms, culminating in a live-streamed finale where the audience helps decide the winner.",
            format=FormatSpec(
                series_type=SeriesType.SEASONAL,
                episode_length="Variable: 2-min social updates to 90-min finale",
                cadence="8-week campaign arc",
                season_length="1 season annually",
            ),
            platform_strategy=PlatformStrategy(
                primary=PlatformSpec(
                    platform="Cross-platform",
                    rationale="The event nature requires presence everywhere. Each platform serves a specific role in the campaign ecosystem.",
                ),
                secondary=[
                    PlatformSpec(
                        platform="TikTok/Instagram",
                        adaptation="Contestant stories, behind-the-scenes, voting promotion",
                    ),
                    PlatformSpec(
                        platform="YouTube",
                        adaptation="Long-form finalist profiles, mentor sessions, finale livestream",
                    ),
                    PlatformSpec(
                        platform="LinkedIn",
                        adaptation="Professional angle: industry impact, mentor perspectives, B2B sponsorship content",
                    ),
                ],
                amplification="PR campaign, influencer jury, partner organizations, earned media through finalist stories.",
            ),
            series_structure=SeriesStructure(
                recurring_elements=[
                    "Weekly progress updates",
                    "Contestant 'confessional' moments",
                    "Mentor feedback sessions",
                    "Community voting integration",
                    "Behind-the-scenes access",
                ],
                variable_elements=[
                    "Unique challenges based on year's theme",
                    "Different finalist personalities and projects",
                    "Surprise guest mentors",
                    "Location varies based on finalists' locations",
                ],
                host_approach="High-profile host with credibility in innovation space. Supported by influencer 'correspondents' covering different aspects.",
            ),
            brand_integration=BrandIntegration(
                philosophy="The brand is the enabler of dreams. Heavy presence is justified because the brand is genuinely making something happen.",
                integration_method="Named presenting sponsor with visible branding throughout. Products may be relevant tools for contestants.",
                screen_time_balance="30% brand visibility (as platform/enabler), 70% contestant/innovation focus",
                cta_approach="Direct CTAs for submissions, voting, and following the journey. Clear brand association throughout.",
            ),
            episode_concepts=[
                EpisodeConcept(number=1, title="The Call", description="Launch video announcing the challenge and prize. Past year's winner shares their journey."),
                EpisodeConcept(number=2, title="10,000 Dreams", description="Montage of submissions from around the world. Emotional diversity of ideas."),
                EpisodeConcept(number=3, title="The Cut", description="Following judges as they narrow to 50, then 20, then 5 finalists."),
                EpisodeConcept(number=4, title="Meet the Five", description="Deep-dive profiles into each finalist: their story, their idea, their stakes."),
                EpisodeConcept(number=5, title="Mentor Week", description="Finalists work with industry mentors to refine their pitches."),
                EpisodeConcept(number=6, title="The Finale", description="Live event where finalists present. Audience voting. Winner announcement."),
            ],
            why_this_wins=WhyThisWins(
                strategic_alignment="Positions the brand as a genuine force for innovation and youth empowerment—actions speak louder than ads.",
                competitive_differentiation="Creates a proprietary IP that competitors can't replicate. Builds annual anticipation and cultural relevance.",
                audience_value_proposition="Audiences get an inspiring journey, voting power, and the satisfaction of supporting real innovation. Highly shareable.",
            ),
            execution=ExecutionSpec(
                complexity=ProductionComplexity.HIGH,
                budget_tier=BudgetTier.PREMIUM,
                timeline_to_first_episode="4-6 months for full campaign",
            ),
            risks=[
                Risk(
                    risk="Low submission volume could undermine narrative",
                    mitigation="Partner with universities, accelerators, and youth organizations to ensure pipeline",
                ),
                Risk(
                    risk="Live finale technical issues",
                    mitigation="Professional production partner; backup broadcast plan; pre-recorded contingency content",
                ),
                Risk(
                    risk="Winner's project fails post-event",
                    mitigation="Provide ongoing support beyond prize money; set realistic expectations in messaging",
                ),
            ],
        ))

        logger.info(
            "Mock concepts generated",
            company=dossier.company_name,
            count=len(concepts),
        )

        return concepts

    async def _real_generate(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
        additional_context: str,
    ) -> list[Concept]:
        """Generate real concepts using Claude API."""
        from src.integrations.claude import ClaudeClient

        logger.info("Generating real concepts", company=dossier.company_name)

        # Load prompts
        system_prompt = read_text_sync(PromptPaths.creative_system())
        generation_prompt = read_text_sync(PromptPaths.creative_concept_generation())
        format_prompt = read_text_sync(PromptPaths.creative_concept_format())

        client = ClaudeClient()

        brief_blocks = []
        for brief in briefs:
            context = self._build_concept_context(dossier, brief, additional_context)
            brief_blocks.append(
                f"""### Slot {brief.slot_id}
**Research Summary (tiivistetty):**
{context}

**Concept Brief**
- Slot Type: {brief.slot_type.value}
- Platform Focus: {brief.platform_focus.value}
- Risk Profile: {brief.risk_profile.value}
- Format Guidance: {brief.format_guidance}
- Success Hypothesis: {brief.success_hypothesis}
"""
            )

        prompt = f"""{generation_prompt}

## Concept Briefs (3 slots)
{'\n\n'.join(brief_blocks)}

{format_prompt}

Return a JSON array with 3 concepts in slot order.
Concept IDs must be: "concept_01", "concept_02", "concept_03".
"""

        response = await client.creative_generate(
            prompt=prompt,
            system=system_prompt,
        )

        # Parse concepts from response
        import json
        import re

        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", response)
        if json_match:
            json_str = json_match.group(1)
        else:
            json_str = response

        raw_data = json.loads(json_str)
        if isinstance(raw_data, dict) and "concepts" in raw_data:
            concept_items = raw_data["concepts"]
        else:
            concept_items = raw_data

        expected_ids = ["concept_01", "concept_02", "concept_03"]
        normalized_items = []
        for item, expected_id in zip(concept_items, expected_ids, strict=False):
            if isinstance(item, dict):
                item = {**item}
                item["id"] = expected_id
            normalized_items.append(item)

        concepts = [Concept.model_validate(item) for item in normalized_items]

        for concept in concepts:
            logger.info(
                "Concept generated",
                concept_id=concept.id,
                title=concept.title,
            )

        return concepts

    def _build_concept_context(
        self,
        dossier: StrategicDossier,
        brief: ConceptBrief,
        additional_context: str = "",
    ) -> str:
        """Build a concise Finnish context block for concept generation."""
        priorities = "\n".join(
            f"- {p.rank}. {p.priority} ({p.execution_assessment.value})"
            for p in sorted(dossier.strategic_priorities, key=lambda p: p.rank)
        )
        gaps = "\n".join(f"- {g}" for g in dossier.marketing_posture.apparent_gaps)
        competitors = "\n".join(
            f"- {c.name}: {c.content_strategy} (uhka {c.threat_level.value})"
            for c in dossier.competitive_analysis.key_competitors
        )
        tensions = "\n".join(
            f"- {t.id}: {t.description} (prioriteetti {t.priority_score}/5)"
            for t in dossier.strategic_tensions
        )
        opportunities = "\n".join(
            f"- {o.id}: {o.description} (riski {o.risk_level.value})"
            for o in dossier.opportunity_zones
        )

        extra = self._format_additional_context(additional_context)
        return f"""**Brändi:** {dossier.brand_identity.positioning}

**Strategiset prioriteetit:**
{priorities or "- (ei tietoa)"}

**Havaitut aukot markkinoinnissa:**
{gaps or "- (ei tietoa)"}

**Kilpailutilanne:**
{competitors or "- (ei tietoa)"}

**Strategiset jännitteet:**
{tensions or "- (ei tietoa)"}

**Mahdollisuusalueet:**
{opportunities or "- (ei tietoa)"}

{extra}
"""

    async def _mock_treatments(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
    ) -> list[dict[str, str]]:
        """Generate mock treatments in Finnish for testing."""
        logger.info("Generating mock treatments", company=dossier.company_name)
        treatments = []
        for brief in briefs:
            title = f"Konsepti {brief.slot_id}: Rohkea mutta brändille sopiva idea"
            content = (
                f"# {title}\n\n"
                f"**Yritys:** {dossier.company_name}\n"
                f"**Konseptislotti:** {brief.slot_type.value}\n"
                f"**Strateginen fokus:** {brief.strategic_focus}\n\n"
                "## Ydinidea\n"
                "Suunnitellaan sarja, joka tekee brändistä keskustelunaiheen ja tavoittaa uusia yleisöjä "
                "yhdistämällä viihdyttävän tarinankerronnan ja aidon hyötyarvon.\n\n"
                "## Formaatti & jakelukanavat\n"
                "- Pääalusta: YouTube + TikTok/IG Reels -leikkeitä\n"
                "- Julkaisutahti: viikoittain\n"
                "- Sisältötyypit: longform, shortform, vaikuttajayhteistyö\n\n"
                "## Miksi tämä toimii\n"
                "- Vastaus brändin strategiseen jännitteeseen\n"
                "- Viraalipotentiaali (jakaminen + keskustelu)\n"
                "- Brändi näkyy luontevasti, ei mainoksena\n"
            )
            treatments.append({"slot_id": brief.slot_id, "title": title, "content": content})
        return treatments

    async def _real_treatments(
        self,
        dossier: StrategicDossier,
        briefs: list[ConceptBrief],
        additional_context: str,
    ) -> list[dict[str, str]]:
        """Generate real treatments using Claude API."""
        from src.integrations.claude import ClaudeClient

        logger.info("Generating real treatments", company=dossier.company_name)

        system_prompt = read_text_sync(PromptPaths.creative_system())
        treatment_prompt = read_text_sync(PromptPaths.creative_treatment_generation())

        client = ClaudeClient()
        treatments: list[dict[str, str]] = []

        for brief in briefs:
            context = self._build_context(dossier, brief, additional_context)
            variant = self._slot_prompt_variant(
                slot_id=brief.slot_id,
                slot_type=brief.slot_type.value,
                risk_profile=brief.risk_profile.value,
                platform_focus=brief.platform_focus.value,
            )
            prompt = f"""{treatment_prompt}

## Brändi & Strateginen konteksti
{context}

## Lisäpainotus (tämä erottaa slotit)
{variant}
"""
            response = await client.creative_generate(
                prompt=prompt,
                system=system_prompt,
            )
            full_prompt = f"{system_prompt}\n\n---\n\n{prompt}" if system_prompt else prompt
            log_prompt(
                category="creative",
                prompt_type="treatment_generation",
                prompt=full_prompt,
                metadata={
                    "model": settings.claude_model,
                    "company": dossier.company_name,
                    "slot_id": brief.slot_id,
                },
                response=response,
            )
            content = response.strip()
            title = self._extract_title(content, fallback=f"Konsepti {brief.slot_id}")
            treatments.append({"slot_id": brief.slot_id, "title": title, "content": content})

            logger.info(
                "Treatment generated",
                slot_id=brief.slot_id,
                title=title,
            )

        return treatments

    def _build_context(
        self,
        dossier: StrategicDossier,
        brief: ConceptBrief,
        additional_context: str = "",
    ) -> str:
        """Build a concise Finnish context block for treatment generation."""
        priorities = "\n".join(
            f"- {p.rank}. {p.priority} ({p.execution_assessment.value})"
            for p in sorted(dossier.strategic_priorities, key=lambda p: p.rank)
        )
        tensions = "\n".join(
            f"- {t.id}: {t.description} (prioriteetti {t.priority_score}/5)"
            for t in dossier.strategic_tensions
        )
        marketing = "\n".join(f"- {t}" for t in dossier.marketing_posture.current_content_types)
        competitors = "\n".join(
            f"- {c.name}: {c.content_strategy} (uhka {c.threat_level.value})"
            for c in dossier.competitive_analysis.key_competitors
        )

        extra = self._format_additional_context(additional_context)
        return f"""**Yritys:** {dossier.company_name}
**Brändi:** {dossier.brand_identity.positioning}

**Strategiset prioriteetit:**
{priorities or "- (ei tietoa)"}

**Nykyinen markkinointi/sisältö:**
{marketing or "- (ei tietoa)"}

**Kilpailijat:**
{competitors or "- (ei tietoa)"}

**Strategiset jännitteet:**
{tensions or "- (ei tietoa)"}

**Konseptibrief:**
- Slotti: {brief.slot_id} ({brief.slot_type.value})
- Strateginen fokus: {brief.strategic_focus}
- Platform-fokus: {brief.platform_focus.value}
- Riskiprofiili: {brief.risk_profile.value}
- Format guidance: {brief.format_guidance}
- Success hypothesis: {brief.success_hypothesis}

{extra}
"""

    @staticmethod
    def _format_additional_context(additional_context: str) -> str:
        if not additional_context or not additional_context.strip():
            return ""
        text = additional_context.strip()
        return (
            "**Lisähuomiot (kevyt painotus):**\n"
            f"- {text}\n"
            "Käytä tätä ohjaavana lisävivahteena, älä syrjäytä tutkimusta tai briefiä."
        )

    @staticmethod
    def _slot_prompt_variant(
        slot_id: str,
        slot_type: str,
        risk_profile: str,
        platform_focus: str,
    ) -> str:
        """Add small but clear prompt differences per slot to improve creative diversity."""
        slot_id = (slot_id or "").strip()
        slot_type = (slot_type or "").strip()
        risk_profile = (risk_profile or "").strip()
        platform_focus = (platform_focus or "").strip()

        if slot_id == "01" or "SAFE" in slot_type.upper() or risk_profile.lower() == "low":
            return (
                "- Tee konseptista helposti skaalautuva ja toistettava formaatti\n"
                "- Priorisoi laaja tavoittavuus, perheystävällisyys ja brändin asiantuntijuus\n"
                "- Vältä liian monimutkaisia tuotantoratkaisuja; kirkas, selkeä toteutus\n"
                f"- Sovita erityisesti kanavaan: {platform_focus}\n"
            )
        if slot_id == "02" or "CHALLENGER" in slot_type.upper() or risk_profile.lower() == "medium":
            return (
                "- Rakenna vahva keskustelun/jaettavuuden koukku (UGC, haaste, participation)\n"
                "- Tuo esiin 'media itse' -ajattelu ja rohkea, mutta bränditurvallinen twist\n"
                "- Hyödynnä kulttuurinen hetki tai käyttäytymisinsightti\n"
                f"- Sovita erityisesti kanavaan: {platform_focus}\n"
            )
        return (
            "- Keksi uusi media- tai PR‑kulma (stunt, live, osallistava tapahtuma)\n"
            "- Tavoitteena korkea puheenaiheisuus ja earned media\n"
            "- Salli suurempi riskitaso ja yllätyksellisyys, mutta pidä brändi selkeästi läsnä\n"
            f"- Sovita erityisesti kanavaan: {platform_focus}\n"
        )

    @staticmethod
    def _extract_title(text: str, fallback: str) -> str:
        """Extract first H1 title from markdown response."""
        for line in text.splitlines():
            if line.strip().startswith("# "):
                return line.strip().lstrip("# ").strip()
        return fallback
