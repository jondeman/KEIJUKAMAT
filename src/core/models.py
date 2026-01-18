"""
Pydantic models for Concept Forge.

These models define the data structures that flow through the system:
- StrategicDossier: Output from Research Bot
- ConceptBrief: Producer's assignment to Creative Bot
- Concept: Output from Creative Bot
- OnePagerSpec: Specification for AD Bot
- RunState: Pipeline execution state
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================


class Phase(str, Enum):
    """Pipeline execution phases."""

    INPUT = "input"
    VALIDATE = "validate"
    CHECK_ARCHIVE = "check_archive"
    RESEARCH = "research"
    STRATEGIZE = "strategize"
    CREATE = "create"
    VISUALIZE = "visualize"
    COMPOSE_PITCH = "compose_pitch"
    PACKAGE = "package"
    DELIVER = "deliver"
    DONE = "done"
    ERROR = "error"


class ExecutionAssessment(str, Enum):
    """How well a company is executing on a priority."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"


class ThreatLevel(str, Enum):
    """Competitor threat level."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OpportunityType(str, Enum):
    """Type of strategic opportunity."""

    GAP = "gap"
    THREAT = "threat"
    ASPIRATION = "aspiration"
    UNDERSERVED_AUDIENCE = "underserved_audience"


class RiskLevel(str, Enum):
    """Risk profile level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class SlotType(str, Enum):
    """Concept slot type."""

    SAFE_BET = "safe_bet"
    CHALLENGER = "challenger"
    MOONSHOT = "moonshot"


class PlatformFocus(str, Enum):
    """Primary platform focus."""

    YOUTUBE = "youtube"
    TIKTOK = "tiktok"
    INSTAGRAM = "instagram"
    CROSS_PLATFORM = "cross_platform"


class SeriesType(str, Enum):
    """Video series type."""

    ONGOING = "ongoing"
    LIMITED = "limited"
    SEASONAL = "seasonal"
    EVENT = "event"


class ProductionComplexity(str, Enum):
    """Production complexity level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class BudgetTier(str, Enum):
    """Budget tier for production."""

    BUDGET = "budget"
    MID = "mid"
    PREMIUM = "premium"


class ImageryStyle(str, Enum):
    """Visual style for one-pager imagery."""

    PHOTOREALISTIC = "photorealistic"
    ILLUSTRATED = "illustrated"
    GRAPHIC = "graphic"
    ABSTRACT = "abstract"
    MIXED = "mixed"


class SourceType(str, Enum):
    """Type of research source."""

    NEWS = "news"
    COMPANY_SITE = "company_site"
    SOCIAL = "social"
    INTERVIEW = "interview"
    REPORT = "report"
    VIDEO = "video"
    OTHER = "other"


# =============================================================================
# STRATEGIC DOSSIER MODELS (Research Bot Output)
# =============================================================================


class VisualMarkers(BaseModel):
    """Brand visual identity markers."""

    primary_color: str = Field(description="Primary brand color (hex or description)")
    secondary_colors: list[str] = Field(default_factory=list)
    style_keywords: list[str] = Field(default_factory=list)
    tone_keywords: list[str] = Field(default_factory=list)


class BrandIdentity(BaseModel):
    """Brand identity snapshot."""

    positioning: str = Field(description="Core positioning statement")
    visual_markers: VisualMarkers
    voice_characteristics: list[str] = Field(default_factory=list)


class StrategicPriority(BaseModel):
    """A ranked strategic priority for the brand."""

    rank: int = Field(ge=1)
    priority: str
    evidence: list[str] = Field(default_factory=list)
    execution_assessment: ExecutionAssessment


class ChannelPresence(BaseModel):
    """Presence assessment for a single channel."""

    active: bool
    assessment: str = ""


class MarketingPosture(BaseModel):
    """Brand's current marketing posture analysis."""

    current_content_types: list[str] = Field(default_factory=list)
    channel_presence: dict[str, ChannelPresence] = Field(default_factory=dict)
    apparent_gaps: list[str] = Field(default_factory=list)
    audience_engagement: str = ""


class Competitor(BaseModel):
    """Competitor analysis."""

    name: str
    content_strategy: str
    threat_level: ThreatLevel


class CompetitiveAnalysis(BaseModel):
    """Competitive landscape analysis."""

    key_competitors: list[Competitor] = Field(default_factory=list)
    brand_winning_areas: list[str] = Field(default_factory=list)
    brand_losing_areas: list[str] = Field(default_factory=list)


class StrategicTension(BaseModel):
    """A strategic tension identified in research."""

    id: str = Field(pattern=r"^tension_\d{2}$")
    description: str
    evidence: list[str] = Field(default_factory=list)
    opportunity_type: OpportunityType
    priority_score: int = Field(ge=1, le=5)


class OpportunityZone(BaseModel):
    """A creative opportunity zone."""

    id: str = Field(pattern=r"^opp_\d{2}$")
    description: str
    rationale: str
    risk_level: RiskLevel


class Source(BaseModel):
    """A research source."""

    title: str
    url: str
    type: SourceType
    date_accessed: str  # ISO date
    relevance: str = ""


class StrategicDossier(BaseModel):
    """
    Complete strategic dossier output from Research Bot.
    This is the main input for the Creative Bot.
    """

    company_name: str
    company_slug: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)

    brand_identity: BrandIdentity
    strategic_priorities: list[StrategicPriority] = Field(default_factory=list)
    marketing_posture: MarketingPosture
    competitive_analysis: CompetitiveAnalysis
    strategic_tensions: list[StrategicTension] = Field(default_factory=list)
    opportunity_zones: list[OpportunityZone] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)


# =============================================================================
# CONCEPT BRIEF MODELS (Producer → Creative Bot)
# =============================================================================


class ConceptBrief(BaseModel):
    """
    Brief assigned by Producer to Creative Bot for one concept slot.
    """

    slot_id: Literal["01", "02", "03"]
    slot_type: SlotType
    assigned_tension_id: str
    strategic_focus: str = Field(description="One sentence strategic focus")
    platform_focus: PlatformFocus
    format_guidance: str
    risk_profile: RiskLevel
    success_hypothesis: str = Field(description="Why CMO would care")


# =============================================================================
# CONCEPT MODELS (Creative Bot Output)
# =============================================================================


class FormatSpec(BaseModel):
    """Video format specification."""

    series_type: SeriesType
    episode_length: str = Field(description="e.g., '8-12 minutes'")
    cadence: str = Field(description="e.g., 'weekly'")
    season_length: str | None = None


class PlatformSpec(BaseModel):
    """Platform specification."""

    platform: str
    rationale: str = ""
    adaptation: str = ""


class PlatformStrategy(BaseModel):
    """Platform strategy for a concept."""

    primary: PlatformSpec
    secondary: list[PlatformSpec] = Field(default_factory=list)
    amplification: str = ""


class SeriesStructure(BaseModel):
    """Series structure definition."""

    recurring_elements: list[str] = Field(default_factory=list)
    variable_elements: list[str] = Field(default_factory=list)
    host_approach: str = ""


class BrandIntegration(BaseModel):
    """Brand integration philosophy."""

    philosophy: str
    integration_method: str = ""
    screen_time_balance: str = ""
    cta_approach: str = ""


class EpisodeConcept(BaseModel):
    """Individual episode concept."""

    number: int
    title: str
    description: str


class WhyThisWins(BaseModel):
    """Strategic justification for the concept."""

    strategic_alignment: str
    competitive_differentiation: str
    audience_value_proposition: str


class ExecutionSpec(BaseModel):
    """Execution specification."""

    complexity: ProductionComplexity
    budget_tier: BudgetTier
    timeline_to_first_episode: str


class Risk(BaseModel):
    """Risk and mitigation pair."""

    risk: str
    mitigation: str


class Concept(BaseModel):
    """
    Complete concept document from Creative Bot.
    """

    id: Literal["concept_01", "concept_02", "concept_03"]
    title: str
    hook: str = Field(description="One sentence for CMO")
    premise: str = Field(description="2-3 sentences explaining the concept")
    long_form_extension: str = Field(
        description="Explicit long-form/broadcast extension option (Ruutu+/Katsomo/Total-TV)"
    )

    format: FormatSpec
    platform_strategy: PlatformStrategy
    series_structure: SeriesStructure
    brand_integration: BrandIntegration
    episode_concepts: list[EpisodeConcept] = Field(min_length=6, max_length=6)
    why_this_wins: WhyThisWins
    execution: ExecutionSpec
    risks: list[Risk] = Field(default_factory=list)


# =============================================================================
# ONE-PAGER SPEC MODELS (AD Bot)
# =============================================================================


class BrandStyling(BaseModel):
    """Brand styling for one-pager."""

    primary_color: str
    secondary_color: str
    accent_color: str
    style_keywords: list[str] = Field(default_factory=list)
    logo_available: bool = False
    logo_path: str | None = None


class OnePagerContent(BaseModel):
    """Text content for one-pager."""

    headline: str = Field(max_length=50, description="Max 6 words")
    subheadline: str = Field(max_length=100, description="Max 15 words")
    bullets: list[str] = Field(max_length=4, description="Max 10 words each")
    call_to_action: str


class VisualDirection(BaseModel):
    """Visual direction for one-pager."""

    mood: str
    imagery_style: ImageryStyle
    composition_notes: str = ""


class OnePagerSpec(BaseModel):
    """
    Complete specification for generating a one-pager image.
    """

    concept_id: Literal["concept_01", "concept_02", "concept_03"]
    brand_styling: BrandStyling
    content: OnePagerContent
    visual_direction: VisualDirection
    generation_prompt: str = ""
    generated_at: datetime | None = None
    output_path: str = ""


# =============================================================================
# RUN STATE MODEL (Pipeline Orchestration)
# =============================================================================


class PhaseResult(BaseModel):
    """Result of a pipeline phase execution."""

    phase: Phase
    started_at: datetime
    completed_at: datetime | None = None
    success: bool = False
    error_message: str | None = None
    retry_count: int = 0
    artifacts: list[str] = Field(default_factory=list)


class UserInput(BaseModel):
    """User input for a run."""

    company_name: str
    user_email: str
    access_code: str
    additional_context: str = ""


class RunState(BaseModel):
    """
    Complete state of a pipeline run.
    Persisted to run_state.json for resumability and debugging.
    """

    run_id: str
    company_slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    current_phase: Phase = Phase.INPUT
    user_input: UserInput | None = None

    # Outputs from each phase
    dossier: StrategicDossier | None = None
    concept_briefs: list[ConceptBrief] = Field(default_factory=list)
    concepts: list[Concept] = Field(default_factory=list)
    treatment_files: list[str] = Field(default_factory=list)
    onepager_specs: list[OnePagerSpec] = Field(default_factory=list)
    pitch_email: str = ""

    # Execution history
    phase_history: list[PhaseResult] = Field(default_factory=list)

    # Archive reference (if research was reused)
    archive_ref: str | None = None

    def advance_to(self, phase: Phase) -> None:
        """Advance to a new phase."""
        self.current_phase = phase
        self.updated_at = datetime.utcnow()

    def record_phase_start(self, phase: Phase) -> PhaseResult:
        """Record the start of a phase."""
        result = PhaseResult(phase=phase, started_at=datetime.utcnow())
        self.phase_history.append(result)
        return result

    def record_phase_complete(self, success: bool, error: str | None = None) -> None:
        """Record the completion of the current phase."""
        if self.phase_history:
            result = self.phase_history[-1]
            result.completed_at = datetime.utcnow()
            result.success = success
            result.error_message = error
        self.updated_at = datetime.utcnow()
