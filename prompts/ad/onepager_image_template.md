# One-Pager Image Generation Template

Tämä on perusprompti, joka täytetään dynaamisesti jokaiselle konseptille.

---

## PROMPT TEMPLATE

```
High-quality vertical infographic one-pager in A4 portrait ratio (210x297) for a Finnish branded content concept pitch.

## OVERALL VISUAL STYLE
{visual_style}
The design must feel premium, professional, and pitch-ready – like it could be presented at a top creative agency.

## LOGO PLACEMENT (CRITICAL)
- TOP LEFT CORNER: Small, elegant Warner Bros. International Television Production Finland logo (white/light version if dark background, dark version if light background)
- TOP RIGHT CORNER: Small, elegant {company_name} company logo
- Both logos are placed discretely at the very top edge, approximately 3-4% of image height, maintaining balance and symmetry
- Logos must NOT dominate – they are subtle professional identifiers only

## HEADER SECTION (top 15%)
Below the logos:
- LARGE BOLD TITLE: "{title}"
- Subtitle: "{subtitle}"
Typography: Bold, modern Finnish advertising style, highly legible

## TIIVISTYS (TOP)
Immediately after the title, include a compact 3-line summary block:
- **MITÄ?** {what_line}
- **MITEN?** {how_line}
- **MIKSI?** {why_line}

## MAIN VISUAL SECTION (middle 50%)
Section title: "KONSEPTIN YDIN"

{main_visual_description}

This section should visually communicate the core concept in an engaging, infographic style.
Use stylized illustrations, photo compositions, or graphic elements that match the brand aesthetic.
Include key characters, settings, or scenarios that bring the concept to life.

## PROCESS/FORMAT SECTION (25%)
Title: "NÄIN SE TOIMII" or "FORMAATTI"

{format_description}

Present as a clear visual flowchart or step-by-step with:
- {step_count} distinct stages connected by arrows or visual flow
- Each stage with icon/small visual + short descriptive text
- Color-coded boxes matching brand palette

## BOTTOM SECTION (10%)
Title: "STRATEGINEN MONIALUSTAINEN ILMIÖ" or "JAKELUSTRATEGIA"

Three-column layout showing:
- Primary channel icon + name + format details
- Secondary channels icons + names
- Impact/benefit statement

## FOOTER
{footer_cta}
A compelling one-liner that summarizes why this concept is perfect for this brand.

## COLOR PALETTE
- Primary brand color: {primary_color}
- Secondary color: {secondary_color}
- Accent color: {accent_color}
- Background: {background_style}
- Text: High contrast for readability

## TECHNICAL REQUIREMENTS
- A4 portrait layout (target 2896x4096)
- All Finnish text must be clearly readable
- Professional marketing document quality
- Avoid generic stock photo aesthetics
- No AI-looking artifacts or distortions in faces
- Clean, sharp typography
- Premium infographic design language
```

---

## SLOT-SPECIFIC STYLE GUIDES

### SLOT 01: SAFE BET
```
visual_style: "Professional, warm, trustworthy Finnish aesthetic. Clean lines, bright natural lighting, approachable imagery. Documentary/editorial feel inspired by premium Nordic design. Soft gradients, clean whitespace, corporate elegance with warmth."
background_style: "Light, airy background with subtle brand color accents or soft gradient"
```

### SLOT 02: CHALLENGER  
```
visual_style: "Bold, energetic, contemporary Finnish style. Strong graphics, dynamic composition, social-media-native visual language. Urban, fresh, attention-grabbing. High contrast, unexpected color pops, modern edge."
background_style: "Dynamic gradient or bold brand color with graphic elements"
```

### SLOT 03: MOONSHOT
```
visual_style: "Visionary, cinematic, premium Finnish aesthetic. Award-worthy design quality, sophisticated layering, dramatic lighting. Editorial boldness, statement-making, the kind of design that wins at Cannes Lions."
background_style: "Rich dark base with premium lighting effects and depth, or striking bold color statement"
```

---

## PLACEHOLDER DEFINITIONS

| Placeholder | Source | Description |
|-------------|--------|-------------|
| `{company_name}` | dossier.company_name | Yrityksen nimi |
| `{title}` | treatment title / H1 | Konseptin pääotsikko |
| `{subtitle}` | treatment hook | Lyhyt iskulause |
| `{what_line}` | extracted from treatment | MITÄ? tiivistelmä |
| `{how_line}` | extracted from treatment | MITEN? tiivistelmä |
| `{why_line}` | extracted from treatment | MIKSI? tiivistelmä |
| `{primary_color}` | brand_styling.primary_color | Pääväri (hex) |
| `{secondary_color}` | brand_styling.secondary_color | Toissijainen väri |
| `{accent_color}` | brand_styling.accent_color | Korostusväri |
| `{visual_style}` | slot-dependent | Visuaalinen tyyli slotista |
| `{background_style}` | slot-dependent | Taustatyyli |
| `{main_visual_description}` | extracted from treatment | Päävisuaalin kuvaus |
| `{format_description}` | extracted from treatment | Formaattikuvaus |
| `{step_count}` | 3-5 | Vaiheiden määrä flowchartissa |
| `{footer_cta}` | generated | Miksi tämä toimii -tiivistelmä |
