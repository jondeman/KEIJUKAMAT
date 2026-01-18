"""
AD Bot - The Visual Crystallizer.

Transforms concept documents into stunning visual one-pagers
using Gemini for prompt building and Gemini Image / Nano Banana Pro for generation.

Supports two modes:
1. Concept-based: Uses structured Concept objects (legacy)
2. Treatment-based: Uses raw treatment markdown + Gemini Image model (preferred)
"""

from datetime import datetime
from pathlib import Path
import re
import shutil

from src.core.config import settings
from src.core.filesystem import PromptPaths, read_text_sync, slugify
from src.core.logger import get_logger
from src.core.models import (
    BrandStyling,
    Concept,
    ImageryStyle,
    OnePagerContent,
    OnePagerSpec,
    StrategicDossier,
    VisualDirection,
)

logger = get_logger(__name__)


class ADBot:
    """
    AD Bot for creating visual one-pagers.
    
    Uses a two-stage process:
    1. Gemini builds detailed image generation prompts
    2. Nano Banana Pro generates the visuals
    """

    def __init__(self):
        self.use_mock = settings.use_mock_apis or not settings.has_gemini_key()
        
        if self.use_mock:
            logger.info("AD Bot initialized in MOCK mode")
        else:
            logger.info("AD Bot initialized with Gemini Image (Nano Banana Pro)")

    async def generate_onepagers(
        self,
        dossier: StrategicDossier,
        concepts: list[Concept],
        output_dir: Path,
        additional_context: str = "",
    ) -> list[OnePagerSpec]:
        """
        Generate one-pager images for all concepts.
        
        Args:
            dossier: Strategic dossier with brand info
            concepts: List of concepts to visualize
            output_dir: Directory to save generated images
            
        Returns:
            List of OnePagerSpec objects with generation details
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        logos = await self._ensure_logos(dossier.company_name, output_dir)
        
        specs = []
        for concept in concepts:
            spec = await self._generate_onepager(
                dossier, concept, output_dir, logos, additional_context
            )
            specs.append(spec)
        
        return specs

    async def generate_onepagers_from_treatments(
        self,
        company_name: str,
        treatments: list[dict[str, str]],
        brand_colors: dict[str, str] | None = None,
        output_dir: Path | None = None,
        additional_context: str = "",
    ) -> list[OnePagerSpec]:
        """
        Generate one-pager images from treatment documents using Gemini Image model.

        This is the preferred method for generating one-pagers from the new treatment-based
        creative pipeline.

        Args:
            company_name: Name of the company
            treatments: List of treatment dicts with keys: slot_id, title, content
            brand_colors: Optional dict with primary_color, secondary_color, accent_color
            output_dir: Directory to save images (default: runs/{company}/ONEPAGERS/)

        Returns:
            List of OnePagerSpec objects with generation details
        """
        from src.core.filesystem import company_folder_name

        if output_dir is None:
            company_folder = company_folder_name(company_name)
            output_dir = settings.get_runs_path() / company_folder / "ONEPAGERS"

        output_dir.mkdir(parents=True, exist_ok=True)
        logos = await self._ensure_logos(company_name, output_dir)

        # Fetch brand colors automatically if not provided
        if brand_colors is None:
            company_logo = logos.get("company_logo")
            brand_colors = await self.fetch_brand_colors(company_name, company_logo)
            logger.info(
                "Brand colors determined",
                company=company_name,
                primary=brand_colors.get("primary_color"),
                secondary=brand_colors.get("secondary_color"),
                accent=brand_colors.get("accent_color"),
            )

        results: list[OnePagerSpec] = []
        for treatment in treatments:
            slot_id = treatment["slot_id"]
            title = treatment["title"]
            content = treatment["content"]

            # Build the image prompt from treatment
            prompt = self._build_treatment_image_prompt(
                company_name=company_name,
                slot_id=slot_id,
                title=title,
                treatment_content=content,
                brand_colors=brand_colors,
                logos=logos,
                additional_context=additional_context,
            )

            # Generate image
            output_path = output_dir / f"concept_{slot_id.zfill(2)}.png"

            if self.use_mock:
                await self._mock_generate_treatment_image(prompt, output_path, title)
            else:
                await self._generate_with_gemini_image(prompt, output_path)

            logger.info(
                "One-pager generated from treatment",
                slot_id=slot_id,
                title=title,
                output=str(output_path),
            )

            # Build a minimal spec for tracking and quality gates
            slot_num = int(slot_id) if slot_id.isdigit() else 0
            if slot_num == 1:
                mood = "professional, inspiring, clean"
                imagery_style = ImageryStyle.PHOTOREALISTIC
            elif slot_num == 2:
                mood = "bold, energetic, contemporary"
                imagery_style = ImageryStyle.GRAPHIC
            else:
                mood = "visionary, impactful, premium"
                imagery_style = ImageryStyle.MIXED

            subheadline = ""
            sections = self._parse_treatment_sections(content)
            if sections.get("ydinidea"):
                subheadline = sections["ydinidea"][:100].strip().replace("\n", " ")

            spec = OnePagerSpec(
                concept_id=f"concept_{slot_id.zfill(2)}",
                brand_styling=BrandStyling(
                    primary_color=brand_colors.get("primary_color", "#1a73e8"),
                    secondary_color=brand_colors.get("secondary_color", "#ffffff"),
                    accent_color=brand_colors.get("accent_color", "#f5f5f5"),
                    style_keywords=[],
                    logo_available=logos.get("company_logo") is not None,
                    logo_path=str(logos.get("company_logo")) if logos.get("company_logo") else None,
                ),
                content=OnePagerContent(
                    headline=title[:50],
                    subheadline=subheadline,
                    bullets=[],
                    call_to_action="Let's bring this to life →",
                ),
                visual_direction=VisualDirection(
                    mood=mood,
                    imagery_style=imagery_style,
                    composition_notes="A4 portrait infographic layout with multiple sections.",
                ),
                generation_prompt=prompt,
                generated_at=datetime.utcnow(),
                output_path=str(output_path),
            )
            results.append(spec)

        # Save each prompt into its own file
        prompts_dir = output_dir / "PROMPTS"
        prompts_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        for r in results:
            slot = r.concept_id.split("_")[-1]
            prompt_md = (
                f"# One-Pager Prompt — Slot {slot}\n\n"
                f"## {r.content.headline}\n\n"
                f"```\n{r.generation_prompt}\n```\n"
            )
            prompt_path = prompts_dir / f"onepager_prompt_{slot}_{timestamp}.md"
            prompt_path.write_text(prompt_md, encoding="utf-8")

        return results

    def _build_treatment_image_prompt(
        self,
        company_name: str,
        slot_id: str,
        title: str,
        treatment_content: str,
        brand_colors: dict[str, str] | None,
        logos: dict[str, Path | None],
        additional_context: str = "",
    ) -> str:
        """
        Build a comprehensive Gemini Image prompt from treatment content.

        Uses the Puuilo-style prompt structure that has proven effective.
        """
        # Extract key sections from treatment markdown
        sections = self._parse_treatment_sections(treatment_content)

        # Determine visual style based on slot
        if slot_id == "01":
            visual_style = "Professional, warm, trustworthy Finnish aesthetic. Clean lines, bright natural lighting, approachable imagery. Documentary/editorial feel inspired by premium Nordic design. Soft gradients, clean whitespace, corporate elegance with warmth."
            background_style = "Light, airy background with subtle brand color accents or soft gradient"
            mood = "trustworthy, professional, inspiring"
        elif slot_id == "02":
            visual_style = "Bold, energetic, contemporary Finnish style. Strong graphics, dynamic composition, social-media-native visual language. Urban, fresh, attention-grabbing. High contrast, unexpected color pops, modern edge."
            background_style = "Dynamic gradient or bold brand color with graphic elements"
            mood = "bold, energetic, contemporary"
        else:  # 03 - Moonshot
            visual_style = "Visionary, cinematic, premium Finnish aesthetic. Award-worthy design quality, sophisticated layering, dramatic lighting. Editorial boldness, statement-making, the kind of design that wins at Cannes Lions."
            background_style = "Rich dark base with premium lighting effects and depth, or striking bold color statement"
            mood = "visionary, impactful, premium"

        # Default brand colors if not provided
        if brand_colors is None:
            brand_colors = {
                "primary_color": "#1a73e8",
                "secondary_color": "#ffffff",
                "accent_color": "#f5f5f5",
            }

        # Extract subtitle from ydinidea section
        subtitle = sections.get("ydinidea", "")[:120]
        if len(subtitle) > 100:
            subtitle = subtitle[:97] + "..."

        # Build WHAT/HOW/WHY summaries
        def _shorten(text: str, max_len: int = 160) -> str:
            text = (text or "").strip().replace("\n", " ")
            if len(text) <= max_len:
                return text
            return text[: max_len - 3].rstrip() + "..."

        what_line = _shorten(sections.get("ydinidea", ""), 160)
        how_line = _shorten(sections.get("formaatti", "") or sections.get("jakelu", ""), 160)
        why_line = _shorten(sections.get("miksi_toimii", ""), 160)

        if not how_line:
            how_line = "Monikanavainen toteutus, selkeä rakenne ja osallistava aktivointi."
        if not why_line:
            why_line = f"Tekee {company_name}sta puheenaiheen ja muuttaa kiinnostuksen toiminnaksi."

        extra_context = ""
        if additional_context and additional_context.strip():
            extra_context = (
                "\n## LISÄHUOMIOT (kevyt painotus)\n"
                f"{additional_context.strip()}\n"
                "Käytä tätä ohjaavana sävynä, älä syrjäytä konseptin ydintä.\n"
            )

        # Build format/process description
        format_section = sections.get("formaatti", "") or sections.get("jakelu", "")
        if not format_section:
            format_section = "Monikanavainen sisältöstrategia"

        # Build main visual description from treatment
        main_visual = sections.get("ydinidea", "") + " " + sections.get("esimerkit", "")
        if len(main_visual) > 500:
            main_visual = main_visual[:500] + "..."

        # Build footer CTA from "miksi toimii" section
        footer_cta = sections.get("miksi_toimii", "")
        if not footer_cta:
            footer_cta = f"Konsepti joka tekee {company_name}sta puheenaiheen ja tavoittaa uusia yleisöjä."
        if len(footer_cta) > 200:
            footer_cta = footer_cta[:197] + "..."

        prompt = f"""High-quality vertical infographic one-pager in A4 portrait ratio (210x297). Final output should be A4-oriented for print-style one-pager layout.

## OVERALL VISUAL STYLE
{visual_style}
The design must feel premium, professional, and pitch-ready – like it could be presented at a top creative agency.
Mood: {mood}

## LOGO PLACEMENT (CRITICAL)
- TOP LEFT CORNER: Small, elegant Warner Bros. International Television Production Finland logo (use light/white version if dark background)
- TOP RIGHT CORNER: Small, elegant {company_name} company logo
- Both logos are placed discretely at the very top edge (approximately 3-4% of image height), maintaining balance and symmetry
- Logos must NOT dominate – they are subtle professional identifiers only

## HEADER SECTION (top 15%)
Below the logos:
- LARGE BOLD TITLE: "{title}"
- Subtitle: "{subtitle}"
Typography: Bold, modern Finnish advertising style, highly legible, strong visual impact

## TIIVISTYS (TOP)
Immediately after the title, include a compact 3-line summary block:
- **MITÄ?** {what_line}
- **MITEN?** {how_line}
- **MIKSI?** {why_line}
These lines must be punchy and attention-grabbing, capturing the core idea fast.

{extra_context}

## MAIN VISUAL SECTION (middle 50%)
Section title: "KONSEPTIN YDIN"

{main_visual}

This section should visually communicate the core concept in a rich, infographic style.
Use stylized illustrations, photo compositions, and graphic elements that match the brand aesthetic.
Include key characters, settings, or scenarios that bring the concept to life.
This must feel like a fully art-directed pitch visual, not a minimal poster.

## PROCESS/FORMAT SECTION (25%)
Title: "NÄIN SE TOIMII"

{format_section}

Present as a clear visual flowchart or step-by-step (3-5 stages) with:
- Each stage in a colored box connected by arrows or visual flow
- Icon or small visual + short descriptive text per stage
- Color-coded using brand palette

## BOTTOM SECTION (10%)
Title: "STRATEGINEN MONIALUSTAINEN ILMIÖ"

Three-column layout showing distribution:
- Primary channel icon + name
- Secondary channels
- Impact/reach indicators

## FOOTER
"{footer_cta}"
A compelling summary of why this concept is perfect for this brand.

## COLOR PALETTE
- Primary brand color: {brand_colors.get('primary_color', '#1a73e8')}
- Secondary color: {brand_colors.get('secondary_color', '#ffffff')}
- Accent color: {brand_colors.get('accent_color', '#f5f5f5')}
- Background: {background_style}
- Text: High contrast for excellent readability

## TECHNICAL REQUIREMENTS
- A4 portrait layout (target 2896x4096)
- Dense infographic layout with multiple sections (header + summary + main visual + flow + distribution + footer)
- All Finnish text must be clearly readable and well-spaced
- Professional marketing document quality matching top creative agencies
- Avoid generic stock photo aesthetics
- No AI-looking artifacts or distortions in faces
- Clean, sharp typography throughout
- Premium infographic design language
- The one-pager should immediately communicate value and create desire to learn more
"""
        return prompt

    def _parse_treatment_sections(self, content: str) -> dict[str, str]:
        """Parse treatment markdown into sections."""
        sections = {}

        # Common section headers to look for
        patterns = {
            "ydinidea": r"##?\s*1\)\s*Ydinidea\s*\n(.*?)(?=##|\Z)",
            "huomio": r"##?\s*2\)\s*Miksi.*herättää.*huomiota\s*\n(.*?)(?=##|\Z)",
            "formaatti": r"##?\s*3\)\s*Formaatti.*jakelu\s*\n(.*?)(?=##|\Z)",
            "jakelu": r"##?\s*Formaatti.*jakelu\s*\n(.*?)(?=##|\Z)",
            "braindi": r"##?\s*4\)\s*Brändi.*roolissa\s*\n(.*?)(?=##|\Z)",
            "vaikuttaja": r"##?\s*5\)\s*Vaikuttaja.*yhteisö\s*\n(.*?)(?=##|\Z)",
            "esimerkit": r"##?\s*6\)\s*Konkreettiset.*esimerkit\s*\n(.*?)(?=##|\Z)",
            "miksi_toimii": r"##?\s*7\)\s*Miksi.*toimii\s*\n(.*?)(?=##|\Z)",
            "riskit": r"##?\s*8\)\s*Riskit\s*\n(.*?)(?=##|\Z)",
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
            if match:
                sections[key] = match.group(1).strip()

        return sections

    async def _mock_generate_treatment_image(
        self,
        prompt: str,
        output_path: Path,
        title: str,
    ) -> None:
        """Generate a mock placeholder image for treatment-based one-pager."""
        logger.info("Generating mock treatment one-pager", title=title)

        try:
            from PIL import Image, ImageDraw, ImageFont

            width, height = 1080, 1920
            bg_color = (26, 115, 232)

            img = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(img)

            # Gradient overlay
            for y in range(height // 2, height):
                alpha = (y - height // 2) / (height // 2)
                overlay_color = tuple(int(c * (1 - alpha * 0.5)) for c in bg_color)
                draw.line([(0, y), (width, y)], fill=overlay_color)

            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 48)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 24)
            except Exception:
                font = ImageFont.load_default()
                small_font = font

            # Title
            draw.text((width // 2, 200), title[:40], fill="white", font=font, anchor="mm")
            draw.text((width // 2, height // 2), "[MOCK ONEPAGER]", fill="white", font=font, anchor="mm")
            draw.text((width // 2, height - 100), "Gemini Image Preview", fill="white", font=small_font, anchor="mm")

            img.save(output_path, "PNG")
        except ImportError:
            # Minimal PNG fallback
            import struct
            import zlib

            def create_minimal_png(w: int, h: int, color: tuple) -> bytes:
                signature = b'\x89PNG\r\n\x1a\n'
                ihdr_data = struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0)
                ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                raw_data = b''
                for _ in range(h):
                    raw_data += b'\x00'
                    for _ in range(w):
                        raw_data += bytes(color)
                compressed = zlib.compress(raw_data)
                idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
                idat_chunk = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
                iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                return signature + ihdr_chunk + idat_chunk + iend_chunk

            png_data = create_minimal_png(200, 356, (26, 115, 232))
            output_path.write_bytes(png_data)

        logger.debug("Mock treatment image saved", path=str(output_path))

    async def _generate_with_gemini_image(
        self,
        prompt: str,
        output_path: Path,
    ) -> None:
        """Generate one-pager image using Gemini Image model."""
        from src.integrations.gemini import GeminiClient

        logger.info("Generating one-pager with Gemini Image model")

        client = GeminiClient()
        image_bytes = await client.generate_image(
            prompt=prompt,
            image_size="4K",
        )

        # Skip PIL resizing to reduce memory usage on small instances.

        output_path.write_bytes(image_bytes)
        logger.info("Gemini image saved", path=str(output_path), size_kb=len(image_bytes) / 1024)

    async def _generate_onepager(
        self,
        dossier: StrategicDossier,
        concept: Concept,
        output_dir: Path,
        logos: dict[str, Path | None],
        additional_context: str = "",
    ) -> OnePagerSpec:
        """Generate a single one-pager."""
        # Build spec
        spec = self._build_spec(dossier, concept, logos.get("company_logo"))
        
        # Build generation prompt
        spec.generation_prompt = self._build_image_prompt(
            dossier, concept, spec, additional_context
        )
        
        # Generate image
        concept_num = int(concept.id.split("_")[1])
        output_path = output_dir / f"concept_{concept_num:02d}.png"
        
        if self.use_mock:
            await self._mock_generate_image(spec, output_path)
        else:
            await self._real_generate_image(spec, output_path)
        
        spec.output_path = str(output_path)
        spec.generated_at = datetime.utcnow()
        
        logger.info(
            "One-pager generated",
            concept_id=concept.id,
            output=str(output_path),
        )
        
        return spec

    def _build_spec(
        self,
        dossier: StrategicDossier,
        concept: Concept,
        company_logo_path: Path | None,
    ) -> OnePagerSpec:
        """Build the one-pager specification from concept."""
        # Extract brand styling from dossier
        visual = dossier.brand_identity.visual_markers
        
        brand_styling = BrandStyling(
            primary_color=visual.primary_color,
            secondary_color=visual.secondary_colors[0] if visual.secondary_colors else "#ffffff",
            accent_color=visual.secondary_colors[1] if len(visual.secondary_colors) > 1 else "#f5f5f5",
            style_keywords=visual.style_keywords,
            logo_available=company_logo_path is not None,
            logo_path=str(company_logo_path) if company_logo_path else None,
        )
        
        # Build content from concept
        # Truncate title if needed for headline
        headline = concept.title
        if len(headline) > 30:
            headline = headline[:27] + "..."
        
        # Create compelling subheadline from hook
        subheadline = concept.hook
        if len(subheadline) > 100:
            subheadline = subheadline[:97] + "..."
        
        # Extract key bullets from why_this_wins
        bullets = [
            f"✓ {concept.why_this_wins.strategic_alignment[:50]}...",
            f"✓ {concept.format.series_type.value.title()} format",
            f"✓ {concept.platform_strategy.primary.platform.title()}-first",
        ]
        
        content = OnePagerContent(
            headline=headline,
            subheadline=subheadline,
            bullets=bullets,
            call_to_action="Let's bring this to life →",
        )
        
        # Determine visual direction based on slot
        slot_num = int(concept.id.split("_")[1])
        if slot_num == 1:
            # Safe bet: professional, clean
            mood = "professional, inspiring, clean"
            imagery_style = ImageryStyle.PHOTOREALISTIC
        elif slot_num == 2:
            # Challenger: bold, energetic
            mood = "bold, energetic, contemporary"
            imagery_style = ImageryStyle.GRAPHIC
        else:
            # Moonshot: visionary, impactful
            mood = "visionary, impactful, premium"
            imagery_style = ImageryStyle.MIXED
        
        visual_direction = VisualDirection(
            mood=mood,
            imagery_style=imagery_style,
            composition_notes="Vertical 9:16 format. Strong top-zone headline. Visual hierarchy emphasizing the concept title and key value prop.",
        )
        
        return OnePagerSpec(
            concept_id=concept.id,
            brand_styling=brand_styling,
            content=content,
            visual_direction=visual_direction,
        )

    def _build_image_prompt(
        self,
        dossier: StrategicDossier,
        concept: Concept,
        spec: OnePagerSpec,
        additional_context: str = "",
    ) -> str:
        """Build the image generation prompt."""
        # Map imagery style to description
        style_descriptions = {
            ImageryStyle.PHOTOREALISTIC: "high-quality photography, realistic lighting, cinematic",
            ImageryStyle.ILLUSTRATED: "modern illustration style, vector-inspired, clean lines",
            ImageryStyle.GRAPHIC: "bold graphic design, geometric shapes, strong typography",
            ImageryStyle.ABSTRACT: "abstract art, conceptual, artistic interpretation",
            ImageryStyle.MIXED: "blend of photography and graphic elements, layered composition",
        }
        
        style_desc = style_descriptions.get(spec.visual_direction.imagery_style, "professional marketing design")
        
        extra_context = ""
        if additional_context and additional_context.strip():
            extra_context = (
                "\nADDITIONAL CONTEXT (light weighting):\n"
                f"{additional_context.strip()}\n"
                "Use this as a subtle guidance only, not as a strict requirement.\n"
            )

        prompt = f"""Create an A4 portrait marketing one-pager (210x297 ratio) with the following specifications:

OVERALL STYLE:
{spec.visual_direction.mood}, {style_desc}

BRAND ALIGNMENT:
- Primary color: {spec.brand_styling.primary_color}
- Secondary color: {spec.brand_styling.secondary_color}
- Accent color: {spec.brand_styling.accent_color}
- Visual tone: {', '.join(spec.brand_styling.style_keywords[:3]) if spec.brand_styling.style_keywords else 'modern, professional'}

COMPOSITION:
- Top zone (20%): Headline area with bold typography
- Middle zone (50%): Concept visualization and key imagery
- Bottom zone (30%): Value propositions and call-to-action

TEXT ELEMENTS (exact copy):
- Headline: "{spec.content.headline}"
- Subheadline: "{spec.content.subheadline[:80]}..."
- Bullet 1: "{spec.content.bullets[0] if spec.content.bullets else ''}"
- Bullet 2: "{spec.content.bullets[1] if len(spec.content.bullets) > 1 else ''}"
- Bullet 3: "{spec.content.bullets[2] if len(spec.content.bullets) > 2 else ''}"
- Call-to-action: "{spec.content.call_to_action}"

IMAGERY DIRECTION:
The visual should convey the essence of a {concept.format.series_type.value} video series focused on {concept.platform_strategy.primary.platform}. 
Include visual elements that suggest {concept.series_structure.recurring_elements[0] if concept.series_structure.recurring_elements else 'engaging content'}.
The imagery should feel like it belongs to {dossier.company_name}'s brand world.

TECHNICAL REQUIREMENTS:
- Aspect ratio: A4 portrait (target 2896x4096)
- Style: {style_desc}
- Text must be clearly readable against background
- Professional marketing document aesthetic
- No stock photo watermarks or artifacts
- Clean, production-ready output

{extra_context}

The one-pager should immediately communicate value and create desire to learn more.
It should look like something a top creative agency would produce.
"""
        
        return prompt

    async def _mock_generate_image(
        self,
        spec: OnePagerSpec,
        output_path: Path,
    ) -> None:
        """Generate a mock placeholder image."""
        logger.info("Generating mock one-pager image", concept=spec.concept_id)
        
        # Create a simple placeholder PNG
        # In production, this would call Nano Banana Pro
        # For testing, we create a minimal valid PNG
        
        # Minimal 1x1 PNG (expands to full size in real implementation)
        # This is a valid PNG that won't cause file size validation issues
        # We'll create a simple colored placeholder
        
        try:
            # Try to use PIL if available
            from PIL import Image, ImageDraw, ImageFont
            
            # Create image
            width, height = 1080, 1920
            
            # Parse primary color
            primary_color = spec.brand_styling.primary_color
            if primary_color.startswith("#"):
                r = int(primary_color[1:3], 16)
                g = int(primary_color[3:5], 16)
                b = int(primary_color[5:7], 16)
                bg_color = (r, g, b)
            else:
                bg_color = (26, 115, 232)  # Default blue
            
            # Create gradient-ish background
            img = Image.new("RGB", (width, height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # Add some visual elements
            # Darker overlay at bottom
            for y in range(height // 2, height):
                alpha = (y - height // 2) / (height // 2)
                overlay_color = tuple(int(c * (1 - alpha * 0.5)) for c in bg_color)
                draw.line([(0, y), (width, y)], fill=overlay_color)
            
            # Add text placeholder
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 60)
                small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
            except Exception:
                font = ImageFont.load_default()
                small_font = font
            
            # Draw headline
            draw.text(
                (width // 2, 200),
                spec.content.headline,
                fill="white",
                font=font,
                anchor="mm",
            )
            
            # Draw concept ID
            draw.text(
                (width // 2, height - 100),
                f"[MOCK] {spec.concept_id}",
                fill="white",
                font=small_font,
                anchor="mm",
            )
            
            # Save
            img.save(output_path, "PNG")
            
        except ImportError:
            # PIL not available, create minimal valid PNG
            # This is a valid 100x100 blue PNG (base64 decoded would be ~15KB)
            import struct
            import zlib
            
            def create_minimal_png(width: int, height: int, color: tuple) -> bytes:
                """Create a minimal valid PNG file."""
                # PNG signature
                signature = b'\x89PNG\r\n\x1a\n'
                
                # IHDR chunk
                ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
                ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data) & 0xffffffff
                ihdr_chunk = struct.pack('>I', 13) + b'IHDR' + ihdr_data + struct.pack('>I', ihdr_crc)
                
                # IDAT chunk (image data)
                raw_data = b''
                for _ in range(height):
                    raw_data += b'\x00'  # Filter byte
                    for _ in range(width):
                        raw_data += bytes(color)
                
                compressed = zlib.compress(raw_data)
                idat_crc = zlib.crc32(b'IDAT' + compressed) & 0xffffffff
                idat_chunk = struct.pack('>I', len(compressed)) + b'IDAT' + compressed + struct.pack('>I', idat_crc)
                
                # IEND chunk
                iend_crc = zlib.crc32(b'IEND') & 0xffffffff
                iend_chunk = struct.pack('>I', 0) + b'IEND' + struct.pack('>I', iend_crc)
                
                return signature + ihdr_chunk + idat_chunk + iend_chunk
            
            # Create 200x356 PNG (maintains 9:16 ratio, keeps file size reasonable)
            png_data = create_minimal_png(200, 356, (26, 115, 232))
            output_path.write_bytes(png_data)
        
        logger.debug("Mock image saved", path=str(output_path), size=output_path.stat().st_size)

    async def _real_generate_image(
        self,
        spec: OnePagerSpec,
        output_path: Path,
    ) -> None:
        """Generate image using Nano Banana Pro API (fallback to Gemini Image)."""
        from src.integrations.nanobanana import NanoBananaClient
        
        logger.info("Generating real one-pager image", concept=spec.concept_id)
        
        try:
            client = NanoBananaClient()
            image_bytes = await client.generate_image(
                prompt=spec.generation_prompt,
                width=2896,
                height=4096,
            )
        except Exception as e:
            logger.warning("Nano Banana failed, falling back to Gemini Image", error=str(e))
            from src.integrations.gemini import GeminiClient
            gemini = GeminiClient()
            image_bytes = await gemini.generate_image(
                prompt=spec.generation_prompt,
                image_size="4K",
            )

        # Skip PIL resizing to reduce memory usage on small instances.
        
        output_path.write_bytes(image_bytes)
        logger.info("Real image saved", path=str(output_path))

    async def _ensure_logos(self, company_name: str, output_dir: Path) -> dict[str, Path | None]:
        """
        Fetch and store logos needed for one-pagers.

        Returns:
            Dict with keys: company_logo, producer_logo
        """
        logos_dir = output_dir / "logos"
        logos_dir.mkdir(parents=True, exist_ok=True)

        company_logo = await self._fetch_company_logo(company_name, logos_dir)
        producer_logo = self._copy_producer_logo(logos_dir)

        if company_logo:
            logger.info("Company logo available", path=str(company_logo))
        else:
            logger.warning("Company logo not found", company=company_name)

        if producer_logo:
            logger.info("Producer logo available", path=str(producer_logo))
        else:
            logger.warning("Producer logo missing", path=str(self._producer_logo_source()))

        return {"company_logo": company_logo, "producer_logo": producer_logo}

    def _producer_logo_source(self) -> Path:
        return settings.project_root / "WVITVPlogo.png"

    def _copy_producer_logo(self, logos_dir: Path) -> Path | None:
        src = self._producer_logo_source()
        if not src.exists():
            return None
        target = logos_dir / "wbitvp_logo.png"
        if not target.exists():
            shutil.copyfile(src, target)
        return target

    async def _fetch_company_logo(self, company_name: str, logos_dir: Path) -> Path | None:
        """Best-effort logo fetch from the web (prefers PNG if available)."""
        import httpx

        slug = slugify(company_name) or "company"
        for ext in (".png", ".svg", ".jpg", ".jpeg", ".webp"):
            existing = logos_dir / f"{slug}_logo{ext}"
            if existing.exists() and existing.stat().st_size > 0:
                return existing

        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            # Brandfetch logos (if API key available)
            brandfetch_logo = await self._try_brandfetch_logo(client, company_name, slug, logos_dir)
            if brandfetch_logo:
                return brandfetch_logo

            for lang in ("fi", "en"):
                url = f"https://{lang}.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "titles": company_name,
                    "prop": "pageimages",
                    "piprop": "original",
                    "pithumbsize": 800,
                    "redirects": 1,
                }
                try:
                    resp = await client.get(url, params=params)
                    resp.raise_for_status()
                    data = resp.json()
                    pages = (data.get("query") or {}).get("pages") or {}
                    for page in pages.values():
                        original = (page.get("original") or {}).get("source")
                        thumb = (page.get("thumbnail") or {}).get("source")
                        candidate = original or thumb
                        if candidate:
                            saved = await self._download_logo_url(client, candidate, logos_dir, slug)
                            if saved:
                                return saved
                except Exception:
                    continue

            domain_candidates = self._build_domain_candidates(company_name, slug)
            for domain in domain_candidates:
                logo_url = f"https://logo.clearbit.com/{domain}"
                try:
                    saved = await self._download_logo_url(client, logo_url, logos_dir, slug)
                    if saved:
                        return saved
                except Exception:
                    continue

        return None

    async def _try_brandfetch_logo(
        self,
        client,  # httpx.AsyncClient
        company_name: str,
        slug: str,
        logos_dir: Path,
    ) -> Path | None:
        """Try to download a logo from Brandfetch API."""
        if not settings.brandfetch_api_key:
            return None

        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {settings.brandfetch_api_key}",
        }
        domain_candidates = self._build_domain_candidates(company_name, slug)

        for domain in domain_candidates:
            try:
                url = f"https://api.brandfetch.io/v2/brands/{domain}"
                resp = await client.get(url, headers=headers)
                if resp.status_code != 200:
                    continue
                data = resp.json()
                logo_url = self._select_brandfetch_logo_url(data)
                if logo_url:
                    return await self._download_logo_url(client, logo_url, logos_dir, slug)
            except Exception:
                continue

        return None

    def _select_brandfetch_logo_url(self, data: dict) -> str | None:
        """Pick a suitable logo URL from Brandfetch response (prefer PNG)."""
        logos = data.get("logos", []) or []
        if not logos:
            return None

        # Flatten formats with src/type/format
        candidates: list[dict] = []
        for logo in logos:
            formats = logo.get("formats", []) or []
            for fmt in formats:
                if fmt.get("src"):
                    candidates.append(fmt)

        if not candidates:
            return None

        # Prefer PNG then SVG then any
        def score(fmt: dict) -> int:
            fmt_type = (fmt.get("format") or fmt.get("type") or "").lower()
            src = (fmt.get("src") or "").lower()
            if "png" in fmt_type or src.endswith(".png"):
                return 3
            if "svg" in fmt_type or src.endswith(".svg"):
                return 2
            return 1

        candidates.sort(key=score, reverse=True)
        return candidates[0].get("src")

    async def _download_logo_url(
        self,
        client,  # httpx.AsyncClient
        url: str,
        logos_dir: Path,
        slug: str,
    ) -> Path | None:
        """Download a logo URL and save to disk; returns saved path if successful."""
        import mimetypes
        import os

        resp = await client.get(url)
        if resp.status_code != 200:
            return None
        content_type = resp.headers.get("content-type", "")
        if "image" not in content_type:
            return None

        ext = ""
        if "png" in content_type:
            ext = ".png"
        elif "svg" in content_type:
            ext = ".svg"
        elif "jpeg" in content_type or "jpg" in content_type:
            ext = ".jpg"
        elif "webp" in content_type:
            ext = ".webp"
        else:
            guessed = mimetypes.guess_extension(content_type) or ""
            ext = guessed if guessed else ""

        if not ext:
            _, url_ext = os.path.splitext(url)
            ext = url_ext if url_ext else ".png"

        target = logos_dir / f"{slug}_logo{ext}"
        target.write_bytes(resp.content)
        return target

    # ─────────────────────────────────────────────────────────────────────
    # Brand Color Seeker
    # ─────────────────────────────────────────────────────────────────────

    async def fetch_brand_colors(
        self,
        company_name: str,
        logo_path: Path | None = None,
    ) -> dict[str, str]:
        """
        Fetch brand colors from the web for a company.

        Uses multiple strategies:
        1. Brandfetch API (free endpoint)
        2. Company website CSS/theme color extraction
        3. Wikipedia infobox color extraction
        4. Color extraction from logo image (if available)
        5. Web search via Gemini for brand guidelines

        Args:
            company_name: Name of the company
            logo_path: Optional path to already-fetched logo for color extraction

        Returns:
            Dict with keys: primary_color, secondary_color, accent_color (hex codes)
        """
        slug = slugify(company_name) or "company"
        logger.info("Fetching brand colors", company=company_name)

        # Strategy 1: Try Brandfetch API
        colors = await self._try_brandfetch_colors(company_name, slug)
        if colors:
            logger.info("Brand colors found via Brandfetch", colors=colors)
            return colors

        # Strategy 2: Try company website CSS/theme colors
        colors = await self._try_website_colors(company_name, slug)
        if colors:
            logger.info("Brand colors found via website", colors=colors)
            return colors

        # Strategy 3: Try Wikipedia for brand colors
        colors = await self._try_wikipedia_colors(company_name)
        if colors:
            logger.info("Brand colors found via Wikipedia", colors=colors)
            return colors

        # Strategy 4: Extract dominant colors from logo
        if logo_path and logo_path.exists():
            colors = await self._extract_colors_from_logo(logo_path)
            if colors:
                logger.info("Brand colors extracted from logo", colors=colors)
                return colors

        # Strategy 5: Use Gemini to search for brand colors
        colors = await self._search_brand_colors_with_gemini(company_name)
        if colors:
            logger.info("Brand colors found via Gemini search", colors=colors)
            return colors

        # Fallback: Generic professional colors
        logger.warning("No brand colors found, using defaults", company=company_name)
        return {
            "primary_color": "#1a73e8",  # Professional blue
            "secondary_color": "#ffffff",  # White
            "accent_color": "#f5f5f5",  # Light gray
        }

    async def _try_brandfetch_colors(
        self,
        company_name: str,
        slug: str,
    ) -> dict[str, str] | None:
        """Try to get brand colors from Brandfetch API."""
        import httpx

        # Brandfetch public endpoint (limited free tier)
        domain_candidates = self._build_domain_candidates(company_name, slug)

        headers = {"Accept": "application/json"}
        if settings.brandfetch_api_key:
            headers["Authorization"] = f"Bearer {settings.brandfetch_api_key}"

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for domain in domain_candidates:
                try:
                    # Brandfetch public API
                    url = f"https://api.brandfetch.io/v2/brands/{domain}"
                    resp = await client.get(url, headers=headers)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        colors = self._parse_brandfetch_colors(data)
                        if colors:
                            return colors
                except Exception as e:
                    logger.debug("Brandfetch failed for domain", domain=domain, error=str(e))
                    continue

        return None

    async def _try_website_colors(
        self,
        company_name: str,
        slug: str,
    ) -> dict[str, str] | None:
        """Try to extract brand colors from the company's website CSS/theme colors."""
        import httpx
        import re
        from urllib.parse import urljoin

        domain_candidates = self._build_domain_candidates(company_name, slug)

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for domain in domain_candidates:
                for scheme in ("https", "http"):
                    base_url = f"{scheme}://{domain}"
                    try:
                        resp = await client.get(base_url, headers={"User-Agent": "Mozilla/5.0"})
                        if resp.status_code >= 400:
                            continue

                        html = resp.text or ""

                        # Theme color from meta tag (strong signal)
                        theme_color = None
                        theme_match = re.search(
                            r'<meta[^>]+name=["\']theme-color["\'][^>]+content=["\']([^"\']+)["\']',
                            html,
                            re.IGNORECASE,
                        )
                        if theme_match:
                            theme_color = self._normalize_hex(theme_match.group(1))

                        css_chunks: list[str] = []
                        css_chunks.extend(
                            re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.DOTALL | re.IGNORECASE)
                        )
                        css_chunks.extend(
                            re.findall(r'style=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
                        )

                        # External CSS links (limit to keep it fast)
                        link_tags = re.findall(
                            r'<link[^>]+rel=["\']stylesheet["\'][^>]*>',
                            html,
                            flags=re.IGNORECASE,
                        )
                        css_urls = []
                        for tag in link_tags:
                            href_match = re.search(r'href=["\']([^"\']+)["\']', tag, flags=re.IGNORECASE)
                            if href_match:
                                css_urls.append(urljoin(base_url, href_match.group(1)))
                        css_urls = css_urls[:3]

                        for css_url in css_urls:
                            try:
                                css_resp = await client.get(css_url)
                                if css_resp.status_code < 400:
                                    css_chunks.append(css_resp.text or "")
                            except Exception:
                                continue

                        css_text = "\n".join(css_chunks)
                        colors = self._extract_colors_from_css_text(css_text)
                        if colors:
                            if theme_color and theme_color not in colors:
                                colors.insert(0, theme_color)
                            return self._select_top_brand_colors(colors)
                    except Exception as e:
                        logger.debug("Website color extraction failed", domain=domain, error=str(e))
                        continue

        return None

    def _parse_brandfetch_colors(self, data: dict) -> dict[str, str] | None:
        """Parse brand colors from Brandfetch API response."""
        colors_list = data.get("colors", [])
        if not colors_list:
            return None

        primary = None
        secondary = None
        accent = None

        for color_obj in colors_list:
            color_type = color_obj.get("type", "")
            hex_value = color_obj.get("hex", "")
            
            if not hex_value:
                continue
            if not hex_value.startswith("#"):
                hex_value = f"#{hex_value}"

            if color_type == "primary" or (not primary and color_type in ["brand", "dark"]):
                primary = hex_value
            elif color_type == "secondary" or (not secondary and primary and color_type in ["light", "accent"]):
                secondary = hex_value
            elif not accent:
                accent = hex_value

        if primary:
            return {
                "primary_color": primary,
                "secondary_color": secondary or "#ffffff",
                "accent_color": accent or "#f5f5f5",
            }
        return None

    async def _try_wikipedia_colors(self, company_name: str) -> dict[str, str] | None:
        """Try to extract brand colors from Wikipedia infobox."""
        import httpx
        import re

        async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
            for lang in ("fi", "en"):
                try:
                    url = f"https://{lang}.wikipedia.org/api/rest_v1/page/html/{company_name.replace(' ', '_')}"
                    resp = await client.get(url)
                    
                    if resp.status_code != 200:
                        continue

                    html = resp.text
                    
                    # Look for hex colors in the HTML (often in infoboxes)
                    hex_pattern = r'#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})\b'
                    matches = re.findall(hex_pattern, html)
                    
                    if matches:
                        # Filter out common generic colors
                        generic_colors = {'ffffff', 'FFFFFF', '000000', 'f5f5f5', 'F5F5F5', 'eeeeee', 'EEEEEE'}
                        brand_colors = [f"#{m}" for m in matches if m.lower() not in generic_colors]
                        
                        if len(brand_colors) >= 1:
                            return {
                                "primary_color": brand_colors[0],
                                "secondary_color": brand_colors[1] if len(brand_colors) > 1 else "#ffffff",
                                "accent_color": brand_colors[2] if len(brand_colors) > 2 else "#f5f5f5",
                            }
                except Exception as e:
                    logger.debug("Wikipedia color extraction failed", lang=lang, error=str(e))
                    continue

        return None

    def _extract_colors_from_css_text(self, css_text: str) -> list[str]:
        """Extract color values from CSS/HTML style blocks."""
        import re

        if not css_text:
            return []

        colors: list[str] = []

        # Hex colors
        for hex_match in re.findall(r'#([A-Fa-f0-9]{3}|[A-Fa-f0-9]{6})\b', css_text):
            colors.append(self._normalize_hex(f"#{hex_match}"))

        # rgb()/rgba()
        for rgb_match in re.findall(r'rgba?\(([^)]+)\)', css_text, flags=re.IGNORECASE):
            parts = [p.strip() for p in rgb_match.split(",")]
            if len(parts) >= 3:
                try:
                    r = int(float(parts[0]))
                    g = int(float(parts[1]))
                    b = int(float(parts[2]))
                    colors.append(self._rgb_to_hex((r, g, b)))
                except ValueError:
                    continue

        # CSS variables like --brand: #00ffcc;
        for var_match in re.findall(r'--[a-zA-Z0-9\-_]+\s*:\s*(#[A-Fa-f0-9]{3,6})', css_text):
            colors.append(self._normalize_hex(var_match))

        return [c for c in colors if c]

    def _build_domain_candidates(self, company_name: str, slug: str) -> list[str]:
        """Build domain candidates from company name (handles & -> and/ja variants)."""
        import re

        base = company_name.lower()
        base = re.sub(r"[’'\"`]", "", base)

        variants: set[str] = set()
        if slug:
            variants.add(slug)
            variants.add(slug.replace("-", ""))

        # Plain alnum, no spaces
        no_space = re.sub(r"\s+", "", base)
        variants.add(re.sub(r"[^a-z0-9]", "", no_space))

        # Replace & with common equivalents
        for repl in ("and", "ja"):
            v = base.replace("&", repl)
            v = re.sub(r"\s+", "", v)
            v = re.sub(r"[^a-z0-9]", "", v)
            if v:
                variants.add(v)

        # Keep hyphenated version
        v = re.sub(r"\s*&\s*", "-", base)
        v = re.sub(r"[^a-z0-9-]", "", v)
        v = re.sub(r"-+", "-", v).strip("-")
        if v:
            variants.add(v)
            variants.add(v.replace("-", ""))

        domains: list[str] = []
        tlds = ("fi", "com", "net", "org", "co")
        for variant in sorted(variants):
            for tld in tlds:
                domains.append(f"{variant}.{tld}")
                domains.append(f"www.{variant}.{tld}")
        return domains

    def _select_top_brand_colors(self, colors: list[str]) -> dict[str, str] | None:
        """Pick primary/secondary/accent from a list of colors based on frequency and colorfulness."""
        from collections import Counter

        if not colors:
            return None

        normalized = [self._normalize_hex(c) for c in colors if c]
        normalized = [c for c in normalized if c]

        # Filter out near-white and near-black for primary selection
        colorful = [c for c in normalized if self._is_colorful(c)]

        if not colorful:
            colorful = normalized

        counts = Counter(colorful)
        most_common = [c for c, _ in counts.most_common(6)]

        primary = most_common[0] if most_common else None
        secondary = most_common[1] if len(most_common) > 1 else "#ffffff"
        accent = most_common[2] if len(most_common) > 2 else "#f5f5f5"

        if primary:
            return {
                "primary_color": primary,
                "secondary_color": secondary,
                "accent_color": accent,
            }
        return None

    def _normalize_hex(self, value: str) -> str | None:
        """Normalize hex color to #rrggbb."""
        import re

        if not value:
            return None
        value = value.strip()
        if not value.startswith("#"):
            return None
        hex_part = value[1:]
        if re.fullmatch(r"[A-Fa-f0-9]{3}", hex_part):
            return f"#{hex_part[0]}{hex_part[0]}{hex_part[1]}{hex_part[1]}{hex_part[2]}{hex_part[2]}".lower()
        if re.fullmatch(r"[A-Fa-f0-9]{6}", hex_part):
            return f"#{hex_part}".lower()
        return None

    def _rgb_to_hex(self, rgb: tuple[int, int, int]) -> str:
        r, g, b = rgb
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        return "#{:02x}{:02x}{:02x}".format(r, g, b)

    def _is_colorful(self, hex_color: str) -> bool:
        """Heuristic to filter out near-white/near-black/gray colors."""
        hex_color = self._normalize_hex(hex_color)
        if not hex_color:
            return False
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        max_c = max(r, g, b)
        min_c = min(r, g, b)
        chroma = max_c - min_c

        # Exclude very light and very dark unless strongly colored
        if max_c > 240 and chroma < 20:
            return False
        if max_c < 20 and chroma < 20:
            return False
        if chroma < 15:
            return False
        return True

    async def _extract_colors_from_logo(self, logo_path: Path) -> dict[str, str] | None:
        """Extract dominant colors from a logo image using PIL."""
        try:
            from PIL import Image
            from collections import Counter
        except ImportError:
            logger.debug("PIL not available for color extraction")
            return None

        try:
            img = Image.open(logo_path)
            
            # Convert to RGB if necessary
            if img.mode != "RGB":
                img = img.convert("RGB")
            
            # Resize for faster processing
            img = img.resize((150, 150))
            
            # Get all pixels
            pixels = list(img.getdata())
            
            # Count colors, ignoring very light (white-ish) and very dark (black-ish) pixels
            filtered_pixels = []
            for r, g, b in pixels:
                # Skip near-white pixels
                if r > 240 and g > 240 and b > 240:
                    continue
                # Skip near-black pixels
                if r < 15 and g < 15 and b < 15:
                    continue
                # Skip very gray pixels
                if abs(r - g) < 20 and abs(g - b) < 20 and abs(r - b) < 20:
                    continue
                filtered_pixels.append((r, g, b))

            if not filtered_pixels:
                return None

            # Quantize to reduce color space (group similar colors)
            def quantize_color(rgb, levels=32):
                return tuple(int(c // levels) * levels for c in rgb)

            quantized = [quantize_color(p) for p in filtered_pixels]
            color_counts = Counter(quantized)
            most_common = color_counts.most_common(3)

            def rgb_to_hex(rgb):
                return "#{:02x}{:02x}{:02x}".format(*rgb)

            colors = [rgb_to_hex(c[0]) for c in most_common]
            
            if colors:
                return {
                    "primary_color": colors[0],
                    "secondary_color": colors[1] if len(colors) > 1 else "#ffffff",
                    "accent_color": colors[2] if len(colors) > 2 else "#f5f5f5",
                }
        except Exception as e:
            logger.debug("Logo color extraction failed", error=str(e))

        return None

    async def _search_brand_colors_with_gemini(
        self,
        company_name: str,
    ) -> dict[str, str] | None:
        """Use Gemini to search for brand colors on the web."""
        try:
            from src.integrations.gemini.client import GeminiClient

            gemini = GeminiClient()
            
            query = f"""Etsi yrityksen {company_name} viralliset brändivärit (brand colors).

Vastaa AINOASTAAN JSON-muodossa näin:
{{
  "primary_color": "#XXXXXX",
  "secondary_color": "#XXXXXX", 
  "accent_color": "#XXXXXX"
}}

Jos et löydä tarkkoja värejä, arvioi ne yrityksen logon ja visuaalisen ilmeen perusteella.
VASTAA VAIN JSON, ei muuta tekstiä."""

            response = await gemini.generate(query)
            
            if response:
                # Extract JSON from response
                import json
                import re
                
                # Try to find JSON in response
                json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
                if json_match:
                    try:
                        colors = json.loads(json_match.group())
                        if "primary_color" in colors:
                            # Validate hex codes
                            for key in ["primary_color", "secondary_color", "accent_color"]:
                                if key in colors:
                                    val = colors[key]
                                    if not val.startswith("#"):
                                        colors[key] = f"#{val}"
                            return colors
                    except json.JSONDecodeError:
                        pass

        except Exception as e:
            logger.debug("Gemini brand color search failed", error=str(e))

        return None
