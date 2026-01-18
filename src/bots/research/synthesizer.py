"""
Research Synthesizer - Transforms raw Deep Research output into Strategic Dossier.

This module handles the analysis pipeline:
1. Parse and clean raw research markdown
2. Extract key sections and findings
3. Apply diagnostic framework to identify tensions
4. Structure data into validated Pydantic models
5. Store all artifacts with full traceability
"""

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import asyncio

from src.core.config import settings
from src.core.filesystem import PromptPaths, read_text_sync, slugify, write_json_sync, write_text_sync
from src.core.logger import get_logger
from src.core.models import StrategicDossier
from src.core.prompt_logger import log_prompt

logger = get_logger(__name__)


# Retry helper for 503 errors
async def retry_on_overload(coro_func, max_retries: int = 5, base_delay: float = 10.0):
    """Retry a coroutine with exponential backoff on 503 errors."""
    last_exception = None
    
    for attempt in range(max_retries):
        try:
            return await coro_func()
        except Exception as e:
            error_str = str(e).lower()
            if "503" in error_str or "overload" in error_str or "unavailable" in error_str:
                last_exception = e
                delay = base_delay * (2 ** attempt)  # 10, 20, 40, 80, 160 seconds
                logger.warning(
                    f"API overloaded (attempt {attempt + 1}/{max_retries}), "
                    f"retrying in {delay:.0f}s...",
                    error=str(e)[:100],
                )
                await asyncio.sleep(delay)
            else:
                raise  # Re-raise non-503 errors immediately
    
    # All retries exhausted
    raise last_exception or Exception("Max retries exceeded")


@dataclass
class ResearchArtifacts:
    """Container for all research artifacts produced during analysis."""
    
    # Raw outputs
    raw_research_md: str  # Original Deep Research markdown
    
    # Parsed sections
    extracted_sections: dict[str, str]  # Parsed sections from raw research
    
    # Analysis outputs
    diagnostic_analysis: str  # Gemini's diagnostic analysis
    structured_dossier: StrategicDossier  # Final structured output
    
    # Metadata
    company_name: str
    company_slug: str
    research_started_at: datetime
    research_completed_at: datetime
    synthesis_completed_at: datetime
    
    # Traceability
    prompts_used: dict[str, str]  # All prompts used in analysis
    model_used: str
    

class ResearchSynthesizer:
    """
    Synthesizes raw Deep Research output into a Strategic Dossier.
    
    Pipeline:
    1. receive_raw_research() - Store and parse raw markdown
    2. extract_sections() - Pull out key sections
    3. apply_diagnostic_framework() - Identify strategic tensions
    4. structure_dossier() - Create validated Pydantic model
    5. save_artifacts() - Store all outputs with traceability
    """

    def __init__(self, company_name: str):
        self.company_name = company_name
        self.company_slug = slugify(company_name)
        self.raw_research: str = ""
        self.extracted_sections: dict[str, str] = {}
        self.diagnostic_analysis: str = ""
        self.research_started_at: datetime | None = None
        self.research_completed_at: datetime | None = None
        self.prompts_used: dict[str, str] = {}

    async def synthesize(
        self,
        raw_research: str,
        research_started_at: datetime,
        run_dir: Path | None = None,
    ) -> tuple[StrategicDossier, ResearchArtifacts]:
        """
        Full synthesis pipeline: raw research → Strategic Dossier.
        
        Args:
            raw_research: Raw markdown from Gemini Deep Research
            research_started_at: When the research query was initiated
            run_dir: Optional run directory to save intermediate artifacts
            
        Returns:
            Tuple of (StrategicDossier, ResearchArtifacts)
        """
        self.research_started_at = research_started_at
        self.research_completed_at = datetime.utcnow()
        
        logger.info("Starting research synthesis", company=self.company_name)
        
        # Step 1: Store and parse raw research
        self.raw_research = raw_research
        self._extract_sections()
        
        # IMMEDIATELY save raw research so we don't lose it if later steps fail
        if run_dir:
            self._save_raw_research_immediately(run_dir)
        
        # Step 2: Apply diagnostic framework
        await self._apply_diagnostic_framework()
        
        # Save diagnostic analysis immediately
        if run_dir:
            self._save_diagnostic_analysis_immediately(run_dir)
        
        # Step 3: Structure into dossier
        dossier = await self._structure_dossier()
        
        # Step 4: Create artifacts container
        artifacts = ResearchArtifacts(
            raw_research_md=self.raw_research,
            extracted_sections=self.extracted_sections,
            diagnostic_analysis=self.diagnostic_analysis,
            structured_dossier=dossier,
            company_name=self.company_name,
            company_slug=self.company_slug,
            research_started_at=self.research_started_at,
            research_completed_at=self.research_completed_at,
            synthesis_completed_at=datetime.utcnow(),
            prompts_used=self.prompts_used,
            model_used=settings.gemini_model,
        )
        
        logger.info(
            "Synthesis complete",
            company=self.company_name,
            tensions=len(dossier.strategic_tensions),
            sources=len(dossier.sources),
        )
        
        return dossier, artifacts

    def _extract_sections(self) -> None:
        """
        Parse raw research markdown into logical sections.
        
        Expected sections from Deep Research:
        - Executive Summary / Overview
        - Company Background
        - Recent News & Announcements
        - Marketing & Content Analysis
        - Competitive Landscape
        - Audience & Market
        - Sources / References
        """
        logger.debug("Extracting sections from raw research")
        
        sections = {}
        current_section = "preamble"
        current_content = []
        
        # Common section headers in Deep Research output
        section_patterns = [
            (r"^#+\s*(?:executive\s+)?summary", "summary"),
            (r"^#+\s*(?:company\s+)?(?:background|overview|about)", "background"),
            (r"^#+\s*(?:recent\s+)?news", "news"),
            (r"^#+\s*(?:marketing|content|digital)", "marketing"),
            (r"^#+\s*(?:competitive?|competitors?)", "competitive"),
            (r"^#+\s*(?:audience|market|customer)", "audience"),
            (r"^#+\s*(?:social\s+media|channels?)", "social"),
            (r"^#+\s*(?:brand|identity|positioning)", "brand"),
            (r"^#+\s*(?:financ|revenue|business)", "business"),
            (r"^#+\s*(?:sources?|references?|citations?)", "sources"),
            (r"^#+\s*(?:key\s+)?(?:findings?|insights?|takeaways?)", "findings"),
        ]
        
        for line in self.raw_research.split("\n"):
            # Check if this line starts a new section
            new_section = None
            for pattern, section_name in section_patterns:
                if re.match(pattern, line.lower().strip()):
                    new_section = section_name
                    break
            
            if new_section:
                # Save previous section
                if current_content:
                    sections[current_section] = "\n".join(current_content).strip()
                current_section = new_section
                current_content = [line]
            else:
                current_content.append(line)
        
        # Save last section
        if current_content:
            sections[current_section] = "\n".join(current_content).strip()
        
        self.extracted_sections = sections
        
        logger.info(
            "Sections extracted",
            count=len(sections),
            sections=list(sections.keys()),
        )

    def _save_raw_research_immediately(self, run_dir: Path) -> None:
        """Save raw research immediately so we don't lose it if synthesis fails."""
        research_dir = run_dir / "artifacts" / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        
        # Save raw research
        raw_path = research_dir / "research_raw.md"
        write_text_sync(raw_path, self.raw_research)
        logger.info(f"✓ Raw research saved to {raw_path}")
        
        # Save sections
        sections_path = research_dir / "research_sections.json"
        write_json_sync(sections_path, self.extracted_sections)
        logger.info(f"✓ Extracted sections saved to {sections_path}")

    async def _apply_diagnostic_framework(self) -> None:
        """
        Apply the diagnostic framework to identify strategic tensions.
        
        Uses Gemini to analyze the extracted sections against our
        diagnostic framework, producing a structured analysis.
        """
        from src.integrations.gemini import GeminiClient
        
        logger.info("Applying diagnostic framework")
        
        # Load the diagnostic framework prompt
        diagnostic_prompt = read_text_sync(PromptPaths.research_diagnostic())
        self.prompts_used["diagnostic_framework"] = diagnostic_prompt
        
        # Build comprehensive analysis prompt
        sections_text = "\n\n---\n\n".join([
            f"## {section.upper()}\n\n{content}"
            for section, content in self.extracted_sections.items()
            if content.strip()
        ])
        
        prompt = f"""# Tutkimusanalyysin tehtävä

Analysoit tutkimusta yrityksestä **{self.company_name}** tunnistaaksesi strategiset jännitteet
ja luovalle tiimille relevantit mahdollisuudet.

## RAATUTKIMUS

{sections_text}

---

## TEHTÄVÄSI

{diagnostic_prompt}

---

## ULKOASU / RAKENNE

Tuota analyysi jäsenneltynä markdownina selkeillä osioilla:

### 1. BRÄNDI-IDENTITEETIN TIIVISTELMÄ
- Ydinpositiointi (miten he kuvaavat itseään)
- Visuaaliset tunnusmerkit (värit, tyyli, sävy)
- Äänensävy ja viestinnän piirteet

### 2. STRATEGISET PRIORITEETIT (rankkaa 1–5)
Jokaisesta prioriteetista:
- Prioriteetin nimi
- Näyttö (bullet-lista)
- Toteutuksen arvio (strong/moderate/weak)

### 3. MARKKINOINTIPOSTUURI
- Nykyiset sisältötyypit
- Kanavien läsnäolo (YouTube, TikTok, Instagram, LinkedIn, jne.)
- Havaitut aukot
- Yleisön sitoutumisen arvio

### 4. KILPAILUANALYYSI
- Keskeiset kilpailijat (nimi, sisältöstrategia, uhkataso)
- Missä brändi voittaa
- Missä brändi häviää

### 5. STRATEGISET JÄNNITTEET (3–5)
Kullekin jännitteelle:
- ID (tension_01, tension_02, jne.)
- Kuvaus (yksi selkeä lause)
- Näyttö (2–3 bullet-pistettä)
- Tyyppi (gap/threat/aspiration/underserved_audience)
- Prioriteettipisteet (1–5)

### 6. MAHDOLLISUUSALUEET (2–3)
Kullekin:
- ID (opp_01, opp_02, jne.)
- Kuvaus
- Perustelu
- Riskitaso (low/medium/high)

### 7. LÄHTEET
Listaa kaikki lähteet URL-osoitteineen.

Ole täsmällinen ja näyttöön perustuva. ÄLÄ tee luovia konseptiehdotuksia.
"""
        self.prompts_used["analysis_prompt"] = prompt
        
        # Log the prompt
        log_prompt(
            category="research",
            prompt_type="diagnostic_analysis",
            prompt=prompt,
            metadata={
                "company": self.company_name,
                "sections_count": len(self.extracted_sections),
            },
        )
        
        # Execute analysis with retry on 503 errors
        client = GeminiClient()
        
        async def _do_diagnostic():
            return await client.generate(
                prompt=prompt,
                temperature=0.4,  # Lower for analytical work
                max_tokens=12000,
            )
        
        self.diagnostic_analysis = await retry_on_overload(_do_diagnostic)
        
        # Log result
        log_prompt(
            category="research",
            prompt_type="diagnostic_analysis_result",
            prompt="[See diagnostic_analysis prompt]",
            metadata={"company": self.company_name},
            response=self.diagnostic_analysis,
        )
        
        logger.info(
            "Diagnostic analysis complete",
            analysis_length=len(self.diagnostic_analysis),
        )

    def _save_diagnostic_analysis_immediately(self, run_dir: Path) -> None:
        """Save diagnostic analysis immediately so we don't lose it if JSON parsing fails."""
        research_dir = run_dir / "artifacts" / "research"
        research_dir.mkdir(parents=True, exist_ok=True)
        
        # Save diagnostic analysis
        analysis_path = research_dir / "research_analysis.md"
        write_text_sync(analysis_path, self.diagnostic_analysis)
        logger.info(f"✓ Diagnostic analysis saved to {analysis_path}")

    async def _structure_dossier(self) -> StrategicDossier:
        """
        Convert diagnostic analysis into a validated StrategicDossier.
        
        Uses Gemini to parse the markdown analysis into JSON,
        then validates with Pydantic.
        """
        from src.integrations.gemini import GeminiClient
        
        logger.info("Structuring dossier from analysis")
        
        # Load schema for reference
        schema_prompt = """
Muunna analyysi validiksi JSONiksi seuraavan rakenteen mukaan:

{
  "company_name": "string",
  "company_slug": "string (lowercase-hyphenated)",
  "brand_identity": {
    "positioning": "string (their core positioning statement)",
    "visual_markers": {
      "primary_color": "string (hex or description)",
      "secondary_colors": ["string"],
      "style_keywords": ["string"],
      "tone_keywords": ["string"]
    },
    "voice_characteristics": ["string"]
  },
  "strategic_priorities": [
    {
      "rank": 1,
      "priority": "string",
      "evidence": ["string"],
      "execution_assessment": "strong|moderate|weak"
    }
  ],
  "marketing_posture": {
    "current_content_types": ["string"],
    "channel_presence": {
      "youtube": {"active": true|false, "assessment": "string"},
      "tiktok": {"active": true|false, "assessment": "string"},
      "instagram": {"active": true|false, "assessment": "string"},
      "linkedin": {"active": true|false, "assessment": "string"}
    },
    "apparent_gaps": ["string"],
    "audience_engagement": "string"
  },
  "competitive_analysis": {
    "key_competitors": [
      {"name": "string", "content_strategy": "string", "threat_level": "high|medium|low"}
    ],
    "brand_winning_areas": ["string"],
    "brand_losing_areas": ["string"]
  },
  "strategic_tensions": [
    {
      "id": "tension_01",
      "description": "string",
      "evidence": ["string"],
      "opportunity_type": "gap|threat|aspiration|underserved_audience",
      "priority_score": 1-5
    }
  ],
  "opportunity_zones": [
    {
      "id": "opp_01",
      "description": "string",
      "rationale": "string",
      "risk_level": "low|medium|high"
    }
  ],
  "sources": [
    {
      "title": "string",
      "url": "string",
      "type": "news|company_site|social|interview|report|video|other",
      "date_accessed": "YYYY-MM-DD",
      "relevance": "string"
    }
  ]
}

TÄRKEÄÄ:
- Vähintään 3 strategista jännitettä
- Vähintään 1 mahdollisuusalue
- Vähintään 5 lähdettä
- Kaikkien jännite-ID:iden tulee olla muodossa "tension_XX"
- Kaikkien mahdollisuus-ID:iden tulee olla muodossa "opp_XX"
- Palauta VAIN validi JSON (ei markdownia)
"""
        self.prompts_used["structure_prompt"] = schema_prompt
        
        prompt = f"""Muunna tämä diagnostiikka-analyysi rakenteiseksi JSONiksi:

{self.diagnostic_analysis}

{schema_prompt}
"""
        
        # Log the structuring prompt
        log_prompt(
            category="research",
            prompt_type="structure_dossier",
            prompt=prompt,
            metadata={"company": self.company_name},
        )
        
        client = GeminiClient()
        
        async def _do_structure():
            return await client.generate(
                prompt=prompt,
                temperature=0.2,  # Very low for structured output
                max_tokens=8000,
            )
        
        response = await retry_on_overload(_do_structure)
        
        # Parse JSON from response
        json_str = self._extract_json(response)
        json_str = self._fix_json(json_str)
        
        try:
            data = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.warning(f"JSON parsing failed, attempting AI fix: {e}")
            try:
                data = await self._try_parse_json_with_ai_fix(json_str, str(e))
            except Exception as e2:
                logger.error(f"AI JSON fix also failed: {e2}")
                # Create minimal valid dossier from diagnostic analysis
                data = self._create_fallback_dossier()
        
        # Ensure required fields
        data["company_name"] = self.company_name
        data["company_slug"] = self.company_slug
        data["generated_at"] = datetime.utcnow().isoformat()
        
        # Validate and create dossier
        dossier = StrategicDossier.model_validate(data)
        
        logger.info(
            "Dossier structured",
            tensions=len(dossier.strategic_tensions),
            opportunities=len(dossier.opportunity_zones),
            sources=len(dossier.sources),
        )
        
        return dossier

    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that may contain markdown code blocks."""
        # Try to find JSON in code blocks first
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if json_match:
            return json_match.group(1).strip()
        
        # Try to find raw JSON (starts with {)
        json_match = re.search(r"\{[\s\S]*\}", text)
        if json_match:
            return json_match.group(0).strip()
        
        # Return as-is and hope for the best
        return text.strip()

    def _fix_json(self, json_str: str) -> str:
        """Attempt to fix common JSON issues."""
        # Remove trailing commas before ] or }
        json_str = re.sub(r',\s*(\]|\})', r'\1', json_str)
        
        # Fix unescaped quotes in strings (crude but helps)
        # This is tricky, so we do a simple approach
        
        # Remove any control characters
        json_str = re.sub(r'[\x00-\x1f]', ' ', json_str)
        
        return json_str

    async def _try_parse_json_with_ai_fix(self, broken_json: str, error: str) -> dict:
        """Use AI to fix malformed JSON."""
        from src.integrations.gemini import GeminiClient
        
        fix_prompt = f"""Seuraava JSON sisältää jäsennysvirheen: {error}

Korjaa JSON ja palauta VAIN validi JSON (ei selitystä, ei markdownia):

{broken_json[:8000]}
"""
        
        client = GeminiClient()
        
        async def _do_fix():
            return await client.generate(
                prompt=fix_prompt,
                temperature=0.1,
                max_tokens=8000,
            )
        
        fixed_response = await retry_on_overload(_do_fix)
        fixed_json = self._extract_json(fixed_response)
        fixed_json = self._fix_json(fixed_json)
        return json.loads(fixed_json)

    def _create_fallback_dossier(self) -> dict:
        """Create a minimal valid dossier structure from available data."""
        logger.warning("Creating fallback dossier from diagnostic analysis")
        
        return {
            "company_name": self.company_name,
            "company_slug": self.company_slug,
            "brand_identity": {
                "positioning": "Katso yksityiskohdat tutkimusanalyysistä",
                "visual_markers": {
                    "primary_color": "unknown",
                    "secondary_colors": [],
                    "style_keywords": [],
                    "tone_keywords": [],
                },
                "voice_characteristics": [],
            },
            "strategic_priorities": [],
            "marketing_posture": {
                "current_content_types": [],
                "channel_presence": {},
                "apparent_gaps": [],
                "audience_engagement": "Katso tutkimusanalyysi",
            },
            "competitive_analysis": {
                "key_competitors": [],
                "brand_winning_areas": [],
                "brand_losing_areas": [],
            },
            "strategic_tensions": [
                {
                    "id": "tension_01",
                    "description": "Katso tutkimusanalyysi täydellistä jänniteanalyysia varten",
                    "evidence": ["Viite: research_analysis.md"],
                    "opportunity_type": "gap",
                    "priority_score": 3,
                }
            ],
            "opportunity_zones": [
                {
                    "id": "opp_01",
                    "description": "Katso tutkimusanalyysi mahdollisuuksien yksityiskohtia varten",
                    "rationale": "Viite: research_analysis.md",
                    "risk_level": "medium",
                }
            ],
            "sources": [
                {
                    "title": "Tutkimuksen raakatiedot",
                    "url": "research_raw.md",
                    "type": "other",
                    "date_accessed": datetime.utcnow().strftime("%Y-%m-%d"),
                    "relevance": "Täysi tutkimusdata löytyy raakatiedosta",
                }
            ],
        }


def save_research_artifacts(
    artifacts: ResearchArtifacts,
    run_dir: Path,
    archive_dir: Path | None = None,
) -> dict[str, Path]:
    """
    Save all research artifacts to disk with full traceability.
    
    Directory structure (under run_dir/artifacts/research/):
    - research_raw.md - Original Deep Research output
    - research_sections.json - Parsed sections from raw research
    - research_analysis.md - Diagnostic analysis (intermediate step)
    - strategic_dossier.json - Final structured dossier
    - strategic_dossier.md - Human-readable dossier
    - research_metadata.json - Timing, prompts, model info for traceability
    - prompts_used.md - All prompts used (for debugging/refinement)
    
    Args:
        artifacts: ResearchArtifacts container
        run_dir: Base directory for this run (e.g., runs/2025-01-16_company_123456/)
        archive_dir: Optional archive directory for caching
        
    Returns:
        Dict mapping artifact name to saved path
    """
    from src.core.formatters import dossier_to_markdown
    
    # Align with RunPaths structure: run_dir/artifacts/research/
    research_dir = run_dir / "artifacts" / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    
    saved_paths = {}
    
    # 1. Raw research
    raw_path = research_dir / "research_raw.md"
    write_text_sync(raw_path, artifacts.raw_research_md)
    saved_paths["raw_research"] = raw_path
    
    # 2. Extracted sections
    sections_path = research_dir / "research_sections.json"
    write_json_sync(sections_path, artifacts.extracted_sections)
    saved_paths["sections"] = sections_path
    
    # 3. Diagnostic analysis
    analysis_path = research_dir / "research_analysis.md"
    write_text_sync(analysis_path, artifacts.diagnostic_analysis)
    saved_paths["analysis"] = analysis_path
    
    # 4. Structured dossier (JSON)
    dossier_json_path = research_dir / "strategic_dossier.json"
    write_json_sync(dossier_json_path, artifacts.structured_dossier.model_dump(mode="json"))
    saved_paths["dossier_json"] = dossier_json_path
    
    # 5. Human-readable dossier (Markdown)
    dossier_md_path = research_dir / "strategic_dossier.md"
    write_text_sync(dossier_md_path, dossier_to_markdown(artifacts.structured_dossier))
    saved_paths["dossier_md"] = dossier_md_path
    
    # 6. Metadata for traceability
    metadata = {
        "company_name": artifacts.company_name,
        "company_slug": artifacts.company_slug,
        "model_used": artifacts.model_used,
        "research_started_at": artifacts.research_started_at.isoformat() if artifacts.research_started_at else None,
        "research_completed_at": artifacts.research_completed_at.isoformat() if artifacts.research_completed_at else None,
        "synthesis_completed_at": artifacts.synthesis_completed_at.isoformat() if artifacts.synthesis_completed_at else None,
        "sections_extracted": list(artifacts.extracted_sections.keys()),
        "tensions_identified": len(artifacts.structured_dossier.strategic_tensions),
        "sources_found": len(artifacts.structured_dossier.sources),
        "prompts_used": list(artifacts.prompts_used.keys()),
    }
    metadata_path = research_dir / "research_metadata.json"
    write_json_sync(metadata_path, metadata)
    saved_paths["metadata"] = metadata_path
    
    # 7. Prompts log (for debugging/iteration)
    prompts_path = research_dir / "prompts_used.md"
    prompts_md = "# Prompts Used in Research Analysis\n\n"
    for name, prompt in artifacts.prompts_used.items():
        prompts_md += f"## {name}\n\n```\n{prompt}\n```\n\n---\n\n"
    write_text_sync(prompts_path, prompts_md)
    saved_paths["prompts"] = prompts_path
    
    # Copy to archive if provided
    if archive_dir:
        archive_research = archive_dir / "research"
        archive_research.mkdir(parents=True, exist_ok=True)
        
        for name, path in saved_paths.items():
            archive_path = archive_research / path.name
            archive_path.write_text(path.read_text())
    
    logger.info(
        "Research artifacts saved",
        count=len(saved_paths),
        directory=str(research_dir),
    )
    
    return saved_paths
