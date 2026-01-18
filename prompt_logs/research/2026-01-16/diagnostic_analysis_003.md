# Prompt Log: diagnostic_analysis

**Timestamp:** 2026-01-16T15:11:07.060579+00:00
**Category:** research
**Type:** diagnostic_analysis

## Metadata

```json
{
  "company": "Puuilo",
  "sections_count": 1
}
```

## Prompt

```
# Research Analysis Task

You are analyzing research about **Puuilo** to identify strategic tensions 
and opportunities for branded video content.

## RAW RESEARCH DATA

## PREAMBLE

[No response from Gemini]

---

## YOUR TASK

# Strategic Diagnostic Framework

Use this framework to synthesize raw research into a Strategic Dossier.

## Section 1: Brand Identity Snapshot

Extract:
- **Core positioning statement**: How do they describe themselves? What's their "we are" statement?
- **Visual identity markers**: Primary colors, secondary colors, style keywords, tone keywords
- **Brand voice characteristics**: How do they speak? What adjectives describe their communication style?

## Section 2: Strategic Priorities (Ranked)

Identify 3-5 strategic priorities. For each:
- **What it is**: Clear description of the priority
- **Evidence**: 2-3 pieces of evidence from research (quotes, campaigns, announcements)
- **Execution assessment**: Are they executing STRONG, MODERATE, or WEAK on this priority?

Rank by apparent importance to the organization.

## Section 3: Marketing Posture Analysis

Document:
- **Current content types**: What kinds of content do they produce?
- **Channel presence**: For each major platform (YouTube, TikTok, Instagram, LinkedIn, Twitter/X):
  - Active or inactive?
  - Brief assessment of quality/engagement
- **Apparent gaps**: What's missing from their content strategy?
- **Audience engagement**: How engaged is their audience? What's working vs. not?

## Section 4: Competitive Pressure Points

For each major competitor (2-3):
- **Name**
- **Content strategy**: What are they doing well?
- **Threat level**: HIGH, MEDIUM, or LOW

Then identify:
- **Where brand is winning**: Areas of competitive advantage
- **Where brand is losing**: Areas of competitive vulnerability

## Section 5: Strategic Tensions ⭐ (CRITICAL)

This is the most important section. Identify 3-5 strategic tensions.

A strategic tension is a GAP between where the brand is and where it wants to be (or needs to be).

For each tension:
- **ID**: tension_01, tension_02, etc.
- **Description**: Clear description of the tension (one sentence)
- **Evidence**: 2-3 pieces of evidence supporting this tension exists
- **Opportunity type**: 
  - GAP: Something they should be doing but aren't
  - THREAT: A competitive danger they need to address
  - ASPIRATION: Something they're trying to achieve but haven't yet
  - UNDERSERVED_AUDIENCE: An audience segment they're missing
- **Priority score**: 1-5 (5 = highest priority)

### Good Tension Examples:
- "The brand invests heavily in R&D but fails to communicate innovation stories to consumers" (GAP)
- "Competitor X's content strategy is capturing the youth market while the brand relies on traditional advertising" (THREAT)
- "Leadership talks about sustainability leadership but content doesn't support this positioning" (ASPIRATION)
- "Strong B2B presence but consumer awareness is minimal despite B2C products" (UNDERSERVED_AUDIENCE)

### Bad Tension Examples:
- "Needs more engagement" (too generic)
- "Should be on TikTok" (tactic, not tension)
- "Brand awareness is low" (symptom, not tension)

## Section 6: Creative Opportunity Zones

Based on tensions, identify 2-3 opportunity zones for branded content:

For each:
- **ID**: opp_01, opp_02, etc.
- **Description**: What the opportunity is
- **Rationale**: Why this is a good opportunity
- **Risk level**: LOW, MEDIUM, or HIGH

## Section 7: Sources

List all sources consulted with:
- Title
- URL
- Type (news, company_site, social, interview, report, video, other)
- Date accessed
- Relevance to the analysis


---

## OUTPUT FORMAT

Provide your analysis as structured markdown with clear sections:

### 1. BRAND IDENTITY SNAPSHOT
- Core positioning (how they describe themselves)
- Visual identity markers (colors, style, tone)
- Voice characteristics

### 2. STRATEGIC PRIORITIES (ranked 1-5)
For each priority include:
- Priority name
- Evidence (bullet points)
- Execution assessment (strong/moderate/weak)

### 3. MARKETING POSTURE
- Current content types
- Channel presence (for each: YouTube, TikTok, Instagram, LinkedIn, etc.)
- Apparent gaps
- Audience engagement assessment

### 4. COMPETITIVE ANALYSIS
- Key competitors (name, content strategy, threat level)
- Where brand is winning
- Where brand is losing

### 5. STRATEGIC TENSIONS (3-5 tensions)
For each tension:
- ID (tension_01, tension_02, etc.)
- Description (one clear sentence)
- Evidence (2-3 bullet points)
- Type (gap/threat/aspiration/underserved_audience)
- Priority score (1-5)

### 6. OPPORTUNITY ZONES (2-3 opportunities)
For each:
- ID (opp_01, opp_02, etc.)
- Description
- Rationale
- Risk level (low/medium/high)

### 7. SOURCES
List all sources from the research with URLs.

Be specific and evidence-based. Every claim should reference the research data.

```
