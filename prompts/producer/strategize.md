# Strategize Phase Prompt

## Purpose

Assign strategic tensions from the research dossier to the three concept slots, ensuring a balanced portfolio with clear differentiation.

## The Three Slots

### Slot 01: The Safe Bet
**Goal**: Address the brand's most obvious strategic priority with a proven, low-risk format.
**Platform**: YouTube long-form
**Risk**: Low
**Audience**: Broad, existing brand followers + interested prospects

**Assignment criteria**:
- Select the #1 ranked strategic priority OR the highest-scoring tension
- Choose tensions with clear, established solutions
- Prefer gaps over threats (building positive vs. defensive)

### Slot 02: The Challenger
**Goal**: Attack a competitive pressure point or directly address a known gap.
**Platform**: TikTok/Reels-first
**Risk**: Medium
**Audience**: New audiences, younger demographics

**Assignment criteria**:
- Select a tension related to competition or market positioning
- Prefer "threat" or "gap" opportunity types
- Look for tensions where boldness would be rewarded

### Slot 03: The Moonshot
**Goal**: Unlock a latent opportunity the brand hasn't seen.
**Platform**: Cross-platform event
**Risk**: High
**Audience**: Broad cultural reach, potential viral impact

**Assignment criteria**:
- Select the most intriguing opportunity zone
- Prefer "underserved_audience" or "aspiration" types
- Look for tensions where innovation could create breakthrough

## Assignment Algorithm

```
1. Sort tensions by priority_score (descending)

2. For Slot 01 (Safe Bet):
   - Assign tension with highest priority_score
   - OR if top tension is threat-focused, use second-highest
   - Mark assigned tension as used

3. For Slot 02 (Challenger):
   - From remaining tensions, find one with type = "threat" or "gap"
   - If none found, use highest remaining priority_score
   - Mark assigned tension as used

4. For Slot 03 (Moonshot):
   - From remaining tensions, find one with type = "underserved_audience" or "aspiration"
   - If none found, check opportunity_zones for inspiration
   - Use most interesting remaining tension
   - Mark assigned tension as used

5. Verify:
   - Each slot has a different tension assigned
   - Risk profiles match slot expectations (low/medium/high)
   - Platform focuses are differentiated
```

## Output: Concept Briefs

For each slot, generate a ConceptBrief with:

- **slot_id**: "01", "02", or "03"
- **slot_type**: "safe_bet", "challenger", or "moonshot"
- **assigned_tension_id**: The tension_XX id
- **strategic_focus**: One sentence summary of the tension
- **platform_focus**: "youtube", "tiktok", or "cross_platform"
- **format_guidance**: Specific guidance for this slot type
- **risk_profile**: "low", "medium", or "high"
- **success_hypothesis**: Why a CMO would care about solving this tension

## Quality Checks

Before finalizing briefs:

1. **Diversity Check**: Are all three tensions different?
2. **Risk Spread Check**: Is there low, medium, and high representation?
3. **Platform Spread Check**: Are primary platforms differentiated?
4. **Strategic Coherence**: Do all three address real tensions from research?
5. **Opportunity Alignment**: Do briefs align with opportunity zones?

## Example Assignment

Given tensions:
- tension_01: Youth engagement gap (priority 5, GAP)
- tension_02: Competitor content threat (priority 4, THREAT)
- tension_03: B2B-to-B2C bridge (priority 3, UNDERSERVED_AUDIENCE)
- tension_04: Innovation storytelling (priority 3, ASPIRATION)

Assignment:
- Slot 01 → tension_01 (highest priority, clear gap to fill)
- Slot 02 → tension_02 (competitive threat, good for challenger)
- Slot 03 → tension_03 (underserved audience, good moonshot territory)
