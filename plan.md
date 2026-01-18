CONCEPT FORGE — Architecture Plan 

Executive Summary
North Star: Every component exists to produce ONE thing: irresistible one-pagers that make marketing decision-makers stop scrolling and start imagining.
The system is a pipeline where each stage refines signal-to-noise ratio:
	•	Research → Extracts the why behind the brand's strategic moves
	•	Creative → Transforms insights into resonant video concepts
	•	Art Direction → Crystallizes concepts into visual desire objects

1. THE CORE INSIGHT: Working Backwards from the One-Pager
Before defining architecture, let's define success:
What makes a one-pager irresistible to a CMO?
	1	Instant Recognition — "This is about MY brand, MY challenge"
	2	Strategic Validity — "This solves a real problem I have"
	3	Creative Surprise — "I haven't seen this approach before"
	4	Executable Clarity — "I can immediately picture this"
	5	Professional Polish — "This came from someone serious"
Therefore: Every upstream component must feed these five qualities downstream.

2. SYSTEM PHILOSOPHY
2.1 The "Strategic Resonance" Principle
Most automated pitch systems fail because they produce generic ideas. Our system must produce ideas that feel bespoke.
Key insight: Gemini Deep Research doesn't just find facts—it finds patterns. We must extract:
	•	What the brand is trying to become (aspirational gap)
	•	What's not working in their current approach (pain point)
	•	What competitors are doing that threatens them (competitive pressure)
	•	What audience segment they're underserving (opportunity space)
Each concept must explicitly address ONE of these strategic tensions.
2.2 The "Three Angles" Framework
The three concepts are not random variations. They follow a deliberate spread:
Concept
Strategic Angle
Risk Profile
Primary Platform
01: The Safe Bet
Addresses their most obvious strategic priority
Low risk, proven format
YouTube long-form
02: The Challenger
Attacks a competitor's strength or their own weakness
Medium risk, bold positioning
TikTok/Reels-first
03: The Moonshot
Unlocks a latent opportunity they haven't seen
High risk, high differentiation
Cross-platform event
This ensures the portfolio has something for every decision-maker appetite.

3. REFINED ARCHITECTURE
3.1 High-Level Flow
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER INPUT                                      │
│         [Company Name] + [User Email] + [Access Code]                       │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PRODUCER ORCHESTRATOR                              │
│  • Validates input                                                          │
│  • Checks archive for existing research                                     │
│  • Manages state machine                                                    │
│  • Ensures quality gates pass                                               │
│  • Compiles final delivery                                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            ▼                       ▼                       ▼
    ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
    │ RESEARCH BOT  │      │ CREATIVE BOT  │      │    AD BOT     │
    │   (Gemini)    │ ───► │ (Claude 4.5)  │ ───► │(Gemini+Nano)  │
    └───────────────┘      └───────────────┘      └───────────────┘
            │                       │                       │
            ▼                       ▼                       ▼
    ┌───────────────┐      ┌───────────────┐      ┌───────────────┐
    │   Strategic   │      │   3 Concept   │      │  3 Visual     │
    │   Dossier     │      │   Documents   │      │  One-Pagers   │
    └───────────────┘      └───────────────┘      └───────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           DELIVERY PACKAGE                                   │
│  • Branded folder with all materials                                        │
│  • Pitch email draft (explains WHY these concepts)                          │
│  • Link sent to user                                                        │
└─────────────────────────────────────────────────────────────────────────────┘
3.2 State Machine Phases
INPUT → VALIDATE → CHECK_ARCHIVE → [RESEARCH] → STRATEGIZE → CREATE → 
VISUALIZE → COMPOSE_PITCH → PACKAGE → DELIVER → DONE
New phase: STRATEGIZE Between research and creation, we add an explicit "Strategic Framing" step that:
	1	Identifies the 3-5 key strategic tensions from research
	2	Assigns each of the three concept slots to a specific tension
	3	Defines the "angle" and "risk profile" for each slot
This ensures concepts are strategically differentiated, not just creatively different.

4. COMPONENT DEEP DIVES
4.1 RESEARCH BOT — "The Strategic Detective"
Purpose: Transform raw company information into actionable creative intelligence.
Key Innovation: We don't just summarize—we diagnose.
Input
	•	Company name
	•	Optional: Industry vertical, known competitors, specific questions
Process (Gemini Deep Research)
Phase 1: Wide Scan Query areas:
	•	Recent news and announcements (last 6 months)
	•	Marketing campaigns (last 3 years)
	•	Video content audit (YouTube, social, TV if findable)
	•	Leadership statements (CEO/CMO interviews, earnings calls)
	•	Brand guidelines (if public)
	•	Competitor landscape
Phase 2: Deep Analysis The critical step: We prompt Gemini to synthesize findings into a Strategic Diagnostic:
## Strategic Diagnostic Template

### 1. BRAND IDENTITY SNAPSHOT
- Core positioning statement (how they describe themselves)
- Visual identity markers (colors, style, tone)
- Brand voice characteristics

### 2. STRATEGIC PRIORITIES (ranked)
For each priority:
- What it is
- Evidence from research
- How well they're executing on it

### 3. MARKETING POSTURE ANALYSIS
- Current content strategy (what they're doing)
- Apparent gaps (what's missing)
- Channel presence assessment
- Audience engagement patterns

### 4. COMPETITIVE PRESSURE POINTS
- Key competitors' content strategies
- Where brand is winning
- Where brand is losing or absent

### 5. STRATEGIC TENSIONS (the gold)
Tension = gap between where they are and where they want to be
- Tension A: [description + evidence]
- Tension B: [description + evidence]
- Tension C: [description + evidence]
- Tension D: [description + evidence]
- Tension E: [description + evidence]

### 6. AUDIENCE HYPOTHESES
- Primary audience they're serving
- Underserved audience opportunity
- Audience pain points brand could address

### 7. CREATIVE OPPORTUNITY ZONES
Based on above analysis:
- Opportunity 1: [description]
- Opportunity 2: [description]
- Opportunity 3: [description]
Output Files
	•	strategic_dossier.json — structured data for Creative Bot
	•	strategic_dossier.md — human-readable report
	•	research_raw.md — Gemini's full research output (preserved as source)
	•	sources.json — all URLs and references
	•	brand_assets/ — downloaded logos, style samples if found

4.2 STRATEGIZE PHASE — "The Angle Selector"
Purpose: Deliberately choose which strategic tensions to address with each concept.
This is a PRODUCER responsibility, not a separate bot.
The Producer reads the strategic_dossier.json and executes an assignment algorithm:
FOR the 3 concept slots:
  Slot 01 (Safe Bet):
    - Select the #1 ranked strategic priority
    - Assign low-risk format approach
    
  Slot 02 (Challenger):
    - Select either a competitive pressure point OR a known gap
    - Assign medium-risk, bold format
    
  Slot 03 (Moonshot):
    - Select the most intriguing opportunity zone
    - Assign high-risk, innovative format
Output
	•	concept_briefs.json — contains for each slot:
	◦	slot_id
	◦	strategic_tension_addressed
	◦	angle_type (safe/challenger/moonshot)
	◦	platform_focus
	◦	format_constraints
	◦	success_hypothesis (why this would resonate)
This becomes the CREATIVE BOT's input brief.

4.3 CREATIVE BOT — "The Concept Architect"
Purpose: Transform strategic briefs into compelling, executable video concepts.
Key Principle: Each concept must answer "Why would a CMO care?" within the first sentence.
Input
	•	strategic_dossier.json
	•	concept_briefs.json (the three assigned slots)
	•	Brand voice/tone guidelines from research
Process (Claude Opus 4.5)
The Creative Bot operates in TWO phases:
Phase A: Concept Generation For each of the 3 briefs, generate a concept following this structure:
## CONCEPT DOCUMENT TEMPLATE

### HEADLINE
[Punchy title that captures the essence]

### THE HOOK (why CMO cares)
[One sentence connecting to their strategic priority]

### THE PREMISE
[2-3 sentences explaining the series concept]

### FORMAT SPECIFICATION
- Series type: [ongoing/limited/seasonal/event]
- Episode length: [specific duration]
- Episode cadence: [weekly/biweekly/etc]
- Season length: [if applicable]

### PLATFORM STRATEGY
Primary: [platform + rationale]
Secondary: [platforms + how content adapts]
Amplification: [paid/organic/influencer]

### SERIES STRUCTURE
- Recurring elements (what audiences expect)
- Variable elements (what keeps it fresh)
- Host/talent approach

### BRAND INTEGRATION PHILOSOPHY
[How the brand appears without feeling like ads]
- Integration method
- Screen time balance
- Call-to-action approach

### EPISODE CONCEPTS (6 examples)
1. [Title] — [one-line description]
2. [Title] — [one-line description]
...

### WHY THIS WINS
- Strategic alignment: [connects to their stated priority]
- Competitive differentiation: [what makes this unique]
- Audience value proposition: [why viewers would watch]

### EXECUTION PATHWAY
- Production complexity: [Low/Medium/High]
- Estimated per-episode budget tier: [Budget/Mid/Premium]
- Timeline to first episode: [estimate]

### RISKS & MITIGATIONS
- Risk 1: [description] → Mitigation: [approach]
- Risk 2: [description] → Mitigation: [approach]
Phase B: Concept Refinement Claude self-critiques each concept against criteria:
	•	Does it clearly address the assigned strategic tension?
	•	Is the format genuinely differentiated from their current content?
	•	Would the CMO be able to immediately picture this?
	•	Is this executable with reasonable resources?
If any check fails, Claude revises before outputting.
Output Files
	•	concepts.json — structured data for AD Bot
	•	concept_01.md, concept_02.md, concept_03.md — full documents
	•	concept_summary.md — one-paragraph summary of each (for email)

4.4 AD BOT — "The Visual Crystallizer"
Purpose: Transform concept documents into stunning visual one-pagers that sell themselves.
Key Principle: The one-pager is NOT a summary. It's a desire object. It must make the viewer want to know more.
The One-Pager Philosophy
A great one-pager is:
	1	Scannable in 3 seconds — hierarchy is crystal clear
	2	Beautiful — professional design, not template-feeling
	3	Intriguing — reveals enough to create desire, not so much it satisfies curiosity
	4	Branded — feels like it belongs to that company's world
Process (Two-Stage Generation)
Stage 1: Prompt Engineering (Gemini 2.5 Pro)
Gemini receives:
	•	The concept document
	•	Brand visual guidelines (colors, style, tone)
	•	Logo/brand assets if available
	•	One-pager requirements
Gemini outputs a detailed image generation prompt that includes:
	•	Overall composition description
	•	Color palette specification
	•	Typography direction
	•	Imagery style and mood
	•	Specific text elements to include
	•	Layout zones and hierarchy
The Prompt Structure:
Create a vertical (9:16) marketing one-pager with the following specifications:

OVERALL STYLE:
[Description of mood, aesthetic, genre]

BRAND ALIGNMENT:
- Primary color: [hex or description]
- Secondary color: [hex or description]
- Accent color: [hex or description]
- Visual tone: [corporate/playful/premium/edgy/etc]

COMPOSITION:
- Top zone: [what goes here]
- Middle zone: [what goes here]
- Bottom zone: [what goes here]

TEXT ELEMENTS (exact copy):
- Headline: "[exact text]"
- Subheadline: "[exact text]"
- Bullet 1: "[exact text]"
- Bullet 2: "[exact text]"
- Bullet 3: "[exact text]"
- Call-to-action: "[exact text]"

IMAGERY DIRECTION:
[Description of any illustrative elements, photography style, or graphic devices]

TECHNICAL REQUIREMENTS:
- Aspect ratio: 9:16 vertical
- Style: [photorealistic/illustrated/graphic/mixed]
- Text must be clearly readable
- Professional marketing document aesthetic
Stage 2: Image Generation (Nano Banana Pro)
The refined prompt goes to Nano Banana Pro for generation.
Quality Control:
	•	Generate 2-3 variants per concept
	•	Validate text legibility (if possible via vision model check)
	•	Select best variant or regenerate if quality threshold not met
Output Files
	•	onepagers/concept_01.png
	•	onepagers/concept_02.png
	•	onepagers/concept_03.png
	•	onepagers/prompts.md — the exact prompts used (for debugging/iteration)
	•	onepagers/variants/ — alternate versions if generated

4.5 PITCH COMPOSER — "The Story Teller"
Purpose: Create the email that accompanies the materials and explains why these concepts matter.
This is a PRODUCER responsibility, not a separate bot.
The Producer generates a pitch email draft that the user can customize before sending.
Email Template
Subject: Three video concepts for [Company Name] — addressing [key challenge/opportunity]

---

Hi [Contact Name],

I've been studying [Company Name]'s recent marketing activities and strategic direction, 
and I noticed [specific observation that shows you've done homework].

Based on this analysis, I've developed three branded entertainment concepts that I believe 
could help [Company Name] achieve [specific goal tied to their priorities]:

**Concept 1: "[Title]"**
[One sentence on what it is + why it addresses their priority]

**Concept 2: "[Title]"**
[One sentence on what it is + why it addresses their priority]

**Concept 3: "[Title]"**
[One sentence on what it is + why it addresses their priority]

I've attached visual one-pagers for each concept, along with detailed format specifications.

The strategic hypothesis behind this outreach: [2-3 sentences explaining why you believe 
these concepts would resonate with their current challenges/opportunities]

I'd welcome 15 minutes to walk through these ideas and get your initial reactions.

Best,
[User Name]

---
[Link to full materials folder]

5. DATA MODELS (REFINED)
5.1 StrategicDossier
{
  "company_name": "string",
  "company_slug": "string",
  "generated_at": "ISO datetime",
  
  "brand_identity": {
    "positioning": "string",
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
      "youtube": {"active": true, "assessment": "string"},
      "tiktok": {"active": false, "assessment": "string"},
      ...
    },
    "apparent_gaps": ["string"],
    "audience_engagement": "string"
  },
  
  "competitive_analysis": {
    "key_competitors": [
      {
        "name": "string",
        "content_strategy": "string",
        "threat_level": "high|medium|low"
      }
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
      "type": "news|company_site|social|interview|report",
      "date_accessed": "ISO date",
      "relevance": "string"
    }
  ]
}
5.2 ConceptBrief (Producer output → Creative input)
{
  "slot_id": "01|02|03",
  "slot_type": "safe_bet|challenger|moonshot",
  "assigned_tension_id": "tension_XX",
  "strategic_focus": "string (one sentence)",
  "platform_focus": "youtube|tiktok|instagram|cross_platform",
  "format_guidance": "string",
  "risk_profile": "low|medium|high",
  "success_hypothesis": "string (why CMO would care)"
}
5.3 Concept
{
  "id": "concept_01|concept_02|concept_03",
  "title": "string",
  "hook": "string (one sentence for CMO)",
  "premise": "string (2-3 sentences)",
  
  "format": {
    "series_type": "ongoing|limited|seasonal|event",
    "episode_length": "string (e.g., '8-12 minutes')",
    "cadence": "string (e.g., 'weekly')",
    "season_length": "string|null"
  },
  
  "platform_strategy": {
    "primary": {"platform": "string", "rationale": "string"},
    "secondary": [{"platform": "string", "adaptation": "string"}],
    "amplification": "string"
  },
  
  "series_structure": {
    "recurring_elements": ["string"],
    "variable_elements": ["string"],
    "host_approach": "string"
  },
  
  "brand_integration": {
    "philosophy": "string",
    "integration_method": "string",
    "screen_time_balance": "string",
    "cta_approach": "string"
  },
  
  "episode_concepts": [
    {"number": 1, "title": "string", "description": "string"}
  ],
  
  "why_this_wins": {
    "strategic_alignment": "string",
    "competitive_differentiation": "string",
    "audience_value_proposition": "string"
  },
  
  "execution": {
    "complexity": "low|medium|high",
    "budget_tier": "budget|mid|premium",
    "timeline_to_first_episode": "string"
  },
  
  "risks": [
    {"risk": "string", "mitigation": "string"}
  ]
}
5.4 OnePagerSpec
{
  "concept_id": "concept_01|concept_02|concept_03",
  
  "brand_styling": {
    "primary_color": "string",
    "secondary_color": "string",
    "accent_color": "string",
    "style_keywords": ["string"],
    "logo_available": true|false,
    "logo_path": "string|null"
  },
  
  "content": {
    "headline": "string (max 6 words)",
    "subheadline": "string (max 15 words)",
    "bullets": ["string (max 10 words each)"],
    "call_to_action": "string"
  },
  
  "visual_direction": {
    "mood": "string",
    "imagery_style": "photorealistic|illustrated|graphic|abstract",
    "composition_notes": "string"
  },
  
  "generation_prompt": "string (full prompt sent to Nano Banana)",
  "generated_at": "ISO datetime",
  "output_path": "string"
}

6. PROMPT ARCHITECTURE
6.1 Prompt File Organization
prompts/
  research/
    system.md              # Research bot personality & rules
    deep_research_query.md # The actual query structure for Gemini
    diagnostic_framework.md # How to synthesize into strategic tensions
    
  creative/
    system.md              # Creative bot personality & rules
    concept_generation.md  # Main concept creation prompt
    concept_format.md      # Required output structure
    self_critique.md       # Quality check criteria
    refinement.md          # How to improve rejected concepts
    
  ad/
    system.md              # AD bot personality & rules
    onepager_philosophy.md # What makes a great one-pager
    prompt_builder.md      # How to construct image gen prompts
    brand_adaptation.md    # How to adapt to brand guidelines
    
  producer/
    strategize.md          # How to assign tensions to slots
    pitch_email.md         # Email composition template
    quality_gates.md       # What must pass at each stage
6.2 Key Prompt Contents
prompts/research/system.md
# Research Bot System Prompt

You are a strategic brand analyst. Your job is not to summarize information—
it is to DIAGNOSE strategic situations.

## Your Mindset
Think like a brand strategist at a top consultancy who has been asked to 
prepare a briefing for a creative team. You're looking for:
- Patterns in behavior (not just facts)
- Gaps between aspiration and reality
- Competitive vulnerabilities
- Underexploited opportunities

## Your Output Philosophy
Everything you produce must be actionable for a creative team developing
video content concepts. Ask yourself: "Would this insight help generate
a specific content idea?"

## What You Must Find
1. What the brand SAYS it wants to achieve (public statements, strategy)
2. What the brand ACTUALLY does (marketing/content activity analysis)
3. Where there's a GAP between 1 and 2
4. What COMPETITORS are doing that threatens the brand
5. What AUDIENCES the brand isn't reaching

## Quality Standard
Your "strategic tensions" are the most important output. Each tension must:
- Be specific (not generic like "needs more engagement")
- Be evidence-based (cite what you found)
- Suggest a content direction (without defining it)
prompts/creative/system.md
# Creative Bot System Prompt

You are a branded entertainment concept developer. You create video series 
concepts that solve real business problems while being genuinely entertaining.

## Your North Star
Every concept must pass the "CMO Test": If this lands on a CMO's desk, 
they should think "This actually addresses something I'm struggling with" 
within 10 seconds of reading.

## Your Creative Philosophy
- SPECIFIC beats generic (name the format, define the structure)
- STRATEGIC beats clever (connection to business goals trumps creativity)
- EXECUTABLE beats ambitious (a doable good idea beats an impossible great one)
- DIFFERENTIATED beats safe (the concept must not feel like something they could have thought of)

## What Makes Bad Concepts
- Generic "brand storytelling" without specific format
- Ideas that sound creative but don't address strategic needs
- Concepts that are just "content" without a clear why-watch proposition
- Formats that require unsustainable production resources

## Your Output Must Include
For each concept:
1. Why a CMO would care (strategic hook)
2. Why an audience would watch (entertainment hook)
3. Why this specific brand should do this (differentiation)
4. Why this is executable (production reality)
prompts/ad/system.md
# AD Bot System Prompt

You are a visual communication expert who creates desire through design.
Your one-pagers are not documents—they are invitations to imagine.

## Your Design Philosophy
The one-pager must work at THREE distances:
1. ACROSS THE ROOM: Color and composition create visual pull
2. AT ARM'S LENGTH: Headline and hierarchy communicate essence
3. UP CLOSE: Details reward attention and build credibility

## What Makes a Great One-Pager
- Immediate visual impact (not template-feeling)
- Clear information hierarchy (scannable in 3 seconds)
- Brand alignment (feels like it belongs to this company)
- Strategic resonance (the WHY is embedded in the WHAT)
- Professional polish (signals serious capability)

## What Makes a Bad One-Pager
- Too much text (it's a teaser, not an explainer)
- Generic stock imagery feel
- Unclear hierarchy (everything competes for attention)
- Off-brand colors/style
- Cluttered composition

## The Test
Would a CMO forward this to a colleague with "worth a look"? 
If not, it's not done.

7. REPOSITORY STRUCTURE (REFINED)
concept-forge/
├── README.md
├── pyproject.toml
├── .env.example
├── .gitignore
│
├── web/                           # Simple web interface
│   ├── index.html                 # Input form
│   ├── status.html                # Progress tracking
│   └── static/
│       └── style.css
│
├── src/
│   ├── __init__.py
│   ├── main.py                    # Entry point
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Environment & settings
│   │   ├── models.py              # All data models (Pydantic)
│   │   ├── state.py               # Run state management
│   │   ├── filesystem.py          # Path management
│   │   ├── validators.py          # Schema validation
│   │   └── logger.py              # Structured logging
│   │
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   ├── producer.py            # Main orchestration logic
│   │   ├── state_machine.py       # Phase transitions
│   │   ├── strategize.py          # Tension → Slot assignment
│   │   ├── quality_gates.py       # Pass/fail checks
│   │   └── pitch_composer.py      # Email generation
│   │
│   ├── bots/
│   │   ├── __init__.py
│   │   ├── research/
│   │   │   ├── __init__.py
│   │   │   ├── bot.py             # Research bot main
│   │   │   ├── query_builder.py   # Deep research query construction
│   │   │   └── synthesizer.py     # Raw → Strategic dossier
│   │   │
│   │   ├── creative/
│   │   │   ├── __init__.py
│   │   │   ├── bot.py             # Creative bot main
│   │   │   ├── generator.py       # Concept generation
│   │   │   └── refiner.py         # Self-critique & improvement
│   │   │
│   │   └── ad/
│   │       ├── __init__.py
│   │       ├── bot.py             # AD bot main
│   │       ├── prompt_builder.py  # Image prompt construction
│   │       └── generator.py       # Image generation wrapper
│   │
│   └── integrations/
│       ├── __init__.py
│       ├── gemini/
│       │   ├── __init__.py
│       │   ├── client.py          # Gemini API wrapper
│       │   └── deep_research.py   # Deep research specific
│       │
│       ├── claude/
│       │   ├── __init__.py
│       │   └── client.py          # Claude API wrapper
│       │
│       ├── nanobanana/
│       │   ├── __init__.py
│       │   └── client.py          # Nano Banana Pro wrapper
│       │
│       └── email/
│           ├── __init__.py
│           ├── client.py          # Email sending
│           └── templates/
│               ├── subject.md
│               └── body.md
│
├── prompts/
│   ├── research/
│   │   ├── system.md
│   │   ├── deep_research_query.md
│   │   └── diagnostic_framework.md
│   │
│   ├── creative/
│   │   ├── system.md
│   │   ├── concept_generation.md
│   │   ├── concept_format.md
│   │   ├── self_critique.md
│   │   └── refinement.md
│   │
│   ├── ad/
│   │   ├── system.md
│   │   ├── onepager_philosophy.md
│   │   ├── prompt_builder.md
│   │   └── brand_adaptation.md
│   │
│   └── producer/
│       ├── strategize.md
│       ├── pitch_email.md
│       └── quality_gates.md
│
├── schemas/
│   ├── strategic_dossier.schema.json
│   ├── concept_brief.schema.json
│   ├── concept.schema.json
│   ├── onepager_spec.schema.json
│   └── run_state.schema.json
│
├── archive/
│   ├── index.json
│   └── companies/
│       └── {company_slug}/
│           ├── metadata.json
│           ├── research/
│           │   ├── strategic_dossier.json
│           │   ├── strategic_dossier.md
│           │   ├── research_raw.md
│           │   └── sources.json
│           ├── concepts/
│           │   ├── concepts.json
│           │   ├── concept_01.md
│           │   ├── concept_02.md
│           │   └── concept_03.md
│           ├── onepagers/
│           │   ├── concept_01.png
│           │   ├── concept_02.png
│           │   ├── concept_03.png
│           │   └── prompts.md
│           └── delivery/
│               ├── pitch_email.md
│               └── package_index.md
│
├── runs/
│   └── {YYYY-MM-DD}_{company_slug}_{run_id}/
│       ├── run_state.json
│       ├── logs.jsonl
│       └── artifacts/
│           └── (same structure as archive)
│
├── devlog/
│   ├── DEVLOG.md
│   └── runs/
│       └── {run_id}.md
│
└── tests/
    ├── __init__.py
    ├── test_research_bot.py
    ├── test_creative_bot.py
    ├── test_ad_bot.py
    ├── test_orchestrator.py
    └── fixtures/
        └── sample_dossiers/

8. IMPLEMENTATION PHASES
Phase 1: Foundation (Week 1)
Goal: Working skeleton with stub bots
Deliverables:
	•	[ ] Repository structure created
	•	[ ] Core models defined (Pydantic)
	•	[ ] State machine implemented
	•	[ ] Filesystem utilities working
	•	[ ] Logger configured
	•	[ ] Web form functional (triggers run)
	•	[ ] Stub bots return mock data
	•	[ ] Archive read/write working
	•	[ ] End-to-end flow with mocks complete
Testing: Run entire pipeline with mock data, verify folder structure and state transitions.
Phase 2: Research Bot (Week 2)
Goal: Real strategic dossiers from Gemini Deep Research
Deliverables:
	•	[ ] Gemini API client implemented
	•	[ ] Deep research query builder working
	•	[ ] Raw research → Strategic dossier synthesizer
	•	[ ] Strategic tension extraction tested
	•	[ ] Archive storage working
	•	[ ] Research prompts refined through testing
Testing: Run against 5 real companies, manually evaluate dossier quality.
Phase 3: Creative Bot (Week 3)
Goal: Real concepts from Claude Opus 4.5
Deliverables:
	•	[ ] Claude API client implemented
	•	[ ] Concept generation working
	•	[ ] Self-critique loop implemented
	•	[ ] "Exactly 3 concepts" enforcement
	•	[ ] Concept quality validation
	•	[ ] Creative prompts refined through testing
Testing: Run against 5 real dossiers, manually evaluate concept quality and strategic alignment.
Phase 4: AD Bot (Week 4)
Goal: Real one-pagers from Nano Banana Pro
Deliverables:
	•	[ ] Gemini prompt builder working
	•	[ ] Nano Banana Pro client implemented
	•	[ ] Brand adaptation logic working
	•	[ ] One-pager quality validation
	•	[ ] Multi-variant generation (pick best)
	•	[ ] AD prompts refined through testing
Testing: Generate one-pagers for 5 concepts, get feedback from real humans.
Phase 5: Integration & Polish (Week 5)
Goal: Complete pipeline with email delivery
Deliverables:
	•	[ ] Pitch email composer working
	•	[ ] Email delivery functional
	•	[ ] Full end-to-end pipeline tested
	•	[ ] Error handling robust
	•	[ ] Devlog automatically updated
	•	[ ] Documentation complete
Testing: Full runs for 10 companies, measure success rate and output quality.

9. QUALITY GATES
Each phase transition requires passing specific quality gates:
RESEARCH → STRATEGIZE
	•	[ ] strategic_dossier.json validates against schema
	•	[ ] At least 3 strategic tensions identified
	•	[ ] At least 1 opportunity zone identified
	•	[ ] Brand visual markers present (even if partial)
	•	[ ] At least 5 sources cited
STRATEGIZE → CREATE
	•	[ ] 3 concept briefs generated
	•	[ ] Each brief assigned to different tension
	•	[ ] Risk profile spread (low/medium/high)
	•	[ ] Platform focus spread
CREATE → VISUALIZE
	•	[ ] Exactly 3 concepts generated
	•	[ ] Each concept validates against schema
	•	[ ] Each concept passes "CMO test" (strategic hook present)
	•	[ ] No two concepts have same primary platform
VISUALIZE → COMPOSE
	•	[ ] 3 PNG files generated (9:16 aspect ratio)
	•	[ ] Each file > 100KB (not error/blank image)
	•	[ ] Prompts logged
COMPOSE → PACKAGE
	•	[ ] Pitch email generated
	•	[ ] Strategic hypothesis articulated
	•	[ ] All file paths valid
PACKAGE → DELIVER
	•	[ ] All files in archive location
	•	[ ] Package index complete
	•	[ ] Share link generated

10. SUCCESS METRICS
System Health
	•	Completion rate: % of runs that reach DONE state
	•	Retry rate: Average retries per phase
	•	Time to completion: Minutes from input to delivery
Output Quality (requires human evaluation)
	•	Strategic relevance: Does dossier identify real tensions? (1-5)
	•	Concept creativity: Are concepts differentiated and fresh? (1-5)
	•	One-pager appeal: Would you forward this? (Yes/No)
	•	Email clarity: Does hypothesis make sense? (1-5)
Business Impact (track if possible)
	•	Response rate: % of sent pitches that get reply
	•	Meeting rate: % of replies that lead to meeting
	•	Conversion rate: % of meetings that lead to engagement

11. FINAL NOTES FOR CODING LLM
When you begin implementation:
	1	Start with models.py — All data structures must be defined first. Use Pydantic for validation.
	2	Implement filesystem.py early — Consistent path handling prevents chaos.
	3	Build the state machine before the bots — The orchestrator logic should work with stubs before real APIs.
	4	One integration at a time — Get Gemini working alone, then Claude, then Nano Banana.
	5	Prompts are code — Treat prompt files with the same care as source files. Version them, test them, iterate them.
	6	Log everything — Every API call, every state transition, every validation result. Debug will thank you.
	7	Test with real companies — Don't just test with mocks. Real data reveals real problems.
	8	The one-pager is the product — If you're ever unsure about a design decision, ask "Does this help make better one-pagers?"

End of Plan v2.0
