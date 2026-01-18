"""
Research Bot - The Strategic Detective.

Transforms raw company information into actionable creative intelligence
using Gemini Deep Research.

Pipeline:
1. Build research query from company info + context
2. Execute Gemini Deep Research (long-running agentic process)
3. Synthesize raw output into structured Strategic Dossier
4. Save all artifacts with full traceability
"""

from datetime import datetime
from pathlib import Path

from src.core.config import settings
from src.core.filesystem import (
    PromptPaths,
    read_text_sync,
    slugify,
    write_text_sync,
    company_folder_name,
)
from src.core.logger import get_logger
from src.core.models import (
    BrandIdentity,
    ChannelPresence,
    CompetitiveAnalysis,
    Competitor,
    ExecutionAssessment,
    MarketingPosture,
    OpportunityType,
    OpportunityZone,
    RiskLevel,
    Source,
    SourceType,
    StrategicDossier,
    StrategicPriority,
    StrategicTension,
    ThreatLevel,
    VisualMarkers,
)
from src.bots.research.synthesizer import (
    ResearchArtifacts,
    ResearchSynthesizer,
)

logger = get_logger(__name__)


class ResearchBot:
    """
    Research Bot for strategic brand analysis.
    
    Uses Gemini Deep Research to conduct comprehensive research
    and synthesizes findings into a Strategic Dossier.
    """

    def __init__(self):
        self.use_mock = settings.use_mock_apis or not settings.has_gemini_key()
        
        if self.use_mock:
            logger.info("Research Bot initialized in MOCK mode")
        else:
            logger.info("Research Bot initialized with Gemini API")

    async def research(
        self,
        company_name: str,
        additional_context: str = "",
        run_dir: Path | None = None,
    ) -> tuple[StrategicDossier, str, ResearchArtifacts | None]:
        """
        Conduct research on a company.
        
        Full pipeline:
        1. Build research query from company info + context
        2. Execute Gemini Deep Research (may take several minutes)
        3. Parse and extract sections from raw output
        4. Apply diagnostic framework to identify tensions
        5. Structure into validated Strategic Dossier
        6. Save all artifacts with full traceability
        
        Args:
            company_name: Name of the company to research
            additional_context: Optional additional context/guidance
            run_dir: Optional directory to save artifacts (for real research)
            
        Returns:
            Tuple of (StrategicDossier, raw_research_output, ResearchArtifacts or None)
        """
        if self.use_mock:
            dossier, raw = await self._mock_research(company_name)

            # Save mock research output + prompt in company folder
            system_prompt = read_text_sync(PromptPaths.research_system())
            query_template = read_text_sync(PromptPaths.research_deep_query())
            query = query_template.format(
                company_name=company_name,
                additional_context=additional_context or "Ei lisäkontekstia.",
            )

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            company_folder = company_folder_name(company_name)
            company_dir = settings.get_runs_path() / company_folder
            company_dir.mkdir(parents=True, exist_ok=True)

            prompt_path = company_dir / f"{company_folder}_Research_PROMPT_{timestamp}.md"
            prompt_content = (
                "# Deep Research - Käytetty Prompt (MOCK)\n\n"
                "## SYSTEM\n\n"
                f"{system_prompt}\n\n"
                "---\n\n"
                "## QUERY\n\n"
                f"{query}\n"
            )
            write_text_sync(prompt_path, prompt_content)

            raw_path = company_dir / f"{company_folder}_Research_{timestamp}.md"
            write_text_sync(raw_path, raw)
            logger.info("Mock research saved", directory=str(company_dir))

            return dossier, raw, None
        else:
            return await self._real_research(company_name, additional_context, run_dir)

    async def _mock_research(self, company_name: str) -> tuple[StrategicDossier, str]:
        """Generate mock research data for testing."""
        logger.info("Generating mock research", company=company_name)
        
        company_slug = slugify(company_name)
        
        # Create comprehensive mock dossier
        dossier = StrategicDossier(
            company_name=company_name,
            company_slug=company_slug,
            generated_at=datetime.utcnow(),
            brand_identity=BrandIdentity(
                positioning=f"{company_name} is a leading innovator in their industry, focused on delivering exceptional value to customers through innovative products and services.",
                visual_markers=VisualMarkers(
                    primary_color="#1a73e8",
                    secondary_colors=["#34a853", "#fbbc04"],
                    style_keywords=["modern", "clean", "professional", "innovative"],
                    tone_keywords=["confident", "approachable", "forward-thinking"],
                ),
                voice_characteristics=[
                    "Confident but not arrogant",
                    "Technical yet accessible",
                    "Customer-centric",
                    "Innovation-focused",
                ],
            ),
            strategic_priorities=[
                StrategicPriority(
                    rank=1,
                    priority="Digital transformation and market expansion",
                    evidence=[
                        "Recent press releases emphasize digital-first strategy",
                        "CEO interviews highlight expansion into new markets",
                        "Increased investment in technology infrastructure",
                    ],
                    execution_assessment=ExecutionAssessment.MODERATE,
                ),
                StrategicPriority(
                    rank=2,
                    priority="Brand awareness among younger demographics",
                    evidence=[
                        "New social media campaigns targeting Gen Z",
                        "Partnership with youth-focused influencers",
                        "Updated brand voice in recent marketing",
                    ],
                    execution_assessment=ExecutionAssessment.WEAK,
                ),
                StrategicPriority(
                    rank=3,
                    priority="Sustainability and corporate responsibility",
                    evidence=[
                        "Published sustainability report",
                        "Announced carbon neutrality goals",
                        "Launched eco-friendly product line",
                    ],
                    execution_assessment=ExecutionAssessment.STRONG,
                ),
            ],
            marketing_posture=MarketingPosture(
                current_content_types=[
                    "Product announcements",
                    "Corporate communications",
                    "Occasional behind-the-scenes content",
                    "Customer testimonials",
                ],
                channel_presence={
                    "youtube": ChannelPresence(
                        active=True,
                        assessment="Regular uploads but low engagement. Content feels corporate and lacks personality.",
                    ),
                    "tiktok": ChannelPresence(
                        active=False,
                        assessment="No presence. Significant opportunity gap for reaching younger audiences.",
                    ),
                    "instagram": ChannelPresence(
                        active=True,
                        assessment="Active posting but inconsistent style. Mix of product shots and lifestyle content.",
                    ),
                    "linkedin": ChannelPresence(
                        active=True,
                        assessment="Strong B2B presence. Thought leadership content performs well.",
                    ),
                },
                apparent_gaps=[
                    "No long-form video content strategy",
                    "Missing from short-form video platforms",
                    "Limited influencer partnerships",
                    "No branded entertainment or series content",
                ],
                audience_engagement="Engagement rates below industry average on consumer-facing channels. B2B engagement is strong.",
            ),
            competitive_analysis=CompetitiveAnalysis(
                key_competitors=[
                    Competitor(
                        name="Competitor Alpha",
                        content_strategy="Strong YouTube presence with educational content. Regular podcast. Active on TikTok with viral campaigns.",
                        threat_level=ThreatLevel.HIGH,
                    ),
                    Competitor(
                        name="Competitor Beta",
                        content_strategy="Heavy investment in influencer marketing. Documentary series on streaming platforms. Strong community engagement.",
                        threat_level=ThreatLevel.MEDIUM,
                    ),
                    Competitor(
                        name="Competitor Gamma",
                        content_strategy="Traditional advertising focus. Limited digital content presence. Strong TV ad spending.",
                        threat_level=ThreatLevel.LOW,
                    ),
                ],
                brand_winning_areas=[
                    "Product quality perception",
                    "B2B relationships and trust",
                    "Sustainability credentials",
                ],
                brand_losing_areas=[
                    "Social media engagement",
                    "Youth market appeal",
                    "Content-led marketing",
                    "Cultural relevance",
                ],
            ),
            strategic_tensions=[
                StrategicTension(
                    id="tension_01",
                    description="The company aspires to reach younger audiences but lacks presence on platforms where they spend time",
                    evidence=[
                        "Zero TikTok presence while competitors gain traction",
                        "YouTube content skews corporate rather than entertaining",
                        "Internal memos mention 'youth gap' as concern",
                    ],
                    opportunity_type=OpportunityType.GAP,
                    priority_score=5,
                ),
                StrategicTension(
                    id="tension_02",
                    description="Strong sustainability messaging not translating to content that audiences want to share",
                    evidence=[
                        "Sustainability reports get media coverage but low social engagement",
                        "Competitors with weaker credentials get more attention for eco-content",
                        "Missed opportunity to lead conversation",
                    ],
                    opportunity_type=OpportunityType.ASPIRATION,
                    priority_score=4,
                ),
                StrategicTension(
                    id="tension_03",
                    description="Competitor Alpha's content strategy is capturing market attention while brand relies on traditional approaches",
                    evidence=[
                        "Competitor's YouTube subscriber growth outpaces by 3x",
                        "Share of voice declining in social conversations",
                        "Brand mentions in lifestyle content decreasing",
                    ],
                    opportunity_type=OpportunityType.THREAT,
                    priority_score=4,
                ),
                StrategicTension(
                    id="tension_04",
                    description="B2B success not translating to consumer brand perception",
                    evidence=[
                        "Strong in enterprise but weak consumer awareness",
                        "Products used by businesses but unknown to end users",
                        "Opportunity to tell human stories behind B2B wins",
                    ],
                    opportunity_type=OpportunityType.UNDERSERVED_AUDIENCE,
                    priority_score=3,
                ),
                StrategicTension(
                    id="tension_05",
                    description="Innovation leadership not being communicated in engaging, accessible ways",
                    evidence=[
                        "R&D investment is high but not visible to public",
                        "Patent portfolio impressive but not storytold",
                        "Employees have interesting stories that aren't shared",
                    ],
                    opportunity_type=OpportunityType.GAP,
                    priority_score=3,
                ),
            ],
            opportunity_zones=[
                OpportunityZone(
                    id="opp_01",
                    description="Launch a TikTok-first series that makes the brand culturally relevant to Gen Z",
                    rationale="Zero current presence means room for bold experimentation. Competitors haven't cracked the code either.",
                    risk_level=RiskLevel.MEDIUM,
                ),
                OpportunityZone(
                    id="opp_02",
                    description="Create documentary-style content showcasing real sustainability impact",
                    rationale="Strong credentials but poor storytelling. Authentic content could differentiate from greenwashing competitors.",
                    risk_level=RiskLevel.LOW,
                ),
                OpportunityZone(
                    id="opp_03",
                    description="Develop an innovation showcase series featuring behind-the-scenes R&D",
                    rationale="Untold stories with high interest potential. Could reposition brand as innovation leader.",
                    risk_level=RiskLevel.HIGH,
                ),
            ],
            sources=[
                Source(
                    title=f"{company_name} Official Website",
                    url=f"https://www.{company_slug}.com",
                    type=SourceType.COMPANY_SITE,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="Primary source for brand positioning and messaging",
                ),
                Source(
                    title=f"{company_name} YouTube Channel",
                    url=f"https://youtube.com/@{company_slug}",
                    type=SourceType.VIDEO,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="Content strategy analysis",
                ),
                Source(
                    title=f"{company_name} Announces Digital Transformation Initiative",
                    url=f"https://news.example.com/{company_slug}-digital",
                    type=SourceType.NEWS,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="Strategic priority evidence",
                ),
                Source(
                    title=f"CEO Interview: The Future of {company_name}",
                    url=f"https://business.example.com/{company_slug}-ceo-interview",
                    type=SourceType.INTERVIEW,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="Leadership vision and priorities",
                ),
                Source(
                    title=f"{company_name} 2024 Sustainability Report",
                    url=f"https://www.{company_slug}.com/sustainability",
                    type=SourceType.REPORT,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="Sustainability credentials and messaging",
                ),
                Source(
                    title=f"{company_name} LinkedIn Page",
                    url=f"https://linkedin.com/company/{company_slug}",
                    type=SourceType.SOCIAL,
                    date_accessed=datetime.utcnow().strftime("%Y-%m-%d"),
                    relevance="B2B content strategy analysis",
                ),
            ],
        )

        raw_research = f"""# Raw Research Output for {company_name}

## Research Summary
This is mock research data generated for testing purposes.
In production, this would contain the full output from Gemini Deep Research.

## Key Findings
- Company shows strong B2B presence but weak consumer engagement
- Significant gap in short-form video content
- Sustainability credentials are strong but undersold
- Competitor content strategies are outpacing the brand
- Youth market represents significant untapped opportunity

## Sources Consulted
- Company website and press releases
- Social media channels (YouTube, Instagram, LinkedIn)
- News articles and press coverage
- Industry reports
- Competitor analysis

*Generated: {datetime.utcnow().isoformat()}*
"""

        logger.info(
            "Mock research complete",
            company=company_name,
            tensions=len(dossier.strategic_tensions),
            sources=len(dossier.sources),
        )

        return dossier, raw_research

    async def _real_research(
        self,
        company_name: str,
        additional_context: str,
        run_dir: Path | None = None,
    ) -> tuple[StrategicDossier, str, ResearchArtifacts]:
        """
        Conduct real research using Gemini Deep Research API.
        
        Pipeline:
        1. Load and format research query prompt
        2. Execute Gemini Deep Research (long-running agentic task)
        3. Use ResearchSynthesizer to analyze and structure output
        4. Save all artifacts for traceability
        
        Args:
            company_name: Company to research
            additional_context: Optional context/guidance
            run_dir: Directory to save artifacts
            
        Returns:
            Tuple of (StrategicDossier, raw_research, ResearchArtifacts)
        """
        from src.integrations.gemini import GeminiClient

        research_started = datetime.utcnow()
        logger.info("Starting real research", company=company_name)

        # Load prompts
        system_prompt = read_text_sync(PromptPaths.research_system())
        query_template = read_text_sync(PromptPaths.research_deep_query())

        # Build research query
        query = query_template.format(
            company_name=company_name,
            additional_context=additional_context or "Ei lisäkontekstia.",
        )

        # Prepare company folder and save prompt immediately
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        company_folder = company_folder_name(company_name)
        company_dir = settings.get_runs_path() / company_folder
        company_dir.mkdir(parents=True, exist_ok=True)
        prompt_path = company_dir / f"{company_folder}_Research_PROMPT_{timestamp}.md"
        prompt_content = (
            "# Deep Research - Käytetty Prompt\n\n"
            "## SYSTEM\n\n"
            f"{system_prompt}\n\n"
            "---\n\n"
            "## QUERY\n\n"
            f"{query}\n"
        )
        write_text_sync(prompt_path, prompt_content)
        logger.info("Research prompt saved", path=str(prompt_path))

        # Execute Deep Research (may take several minutes)
        logger.info("Executing Gemini Deep Research - this may take several minutes...")
        client = GeminiClient()
        raw_research = await client.deep_research(
            query=query,
            system_prompt=system_prompt,
        )
        
        # Save raw research output directly under company folder
        raw_path = company_dir / f"{company_folder}_Research_{timestamp}.md"
        write_text_sync(raw_path, raw_research)
        logger.info("Raw research saved", path=str(raw_path), raw_length=len(raw_research))

        logger.info(
            "Deep Research complete, starting synthesis",
            raw_length=len(raw_research),
        )

        # Synthesize into structured dossier with full artifact tracking
        synthesizer = ResearchSynthesizer(company_name)
        dossier, artifacts = await synthesizer.synthesize(
            raw_research=raw_research,
            research_started_at=research_started,
            run_dir=None,  # Research phase saves only raw output + prompt
        )

        logger.info(
            "Real research complete",
            company=company_name,
            tensions=len(dossier.strategic_tensions),
            sources=len(dossier.sources),
            sections_extracted=len(artifacts.extracted_sections),
        )

        return dossier, raw_research, artifacts

