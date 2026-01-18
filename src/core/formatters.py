"""
Formatters for converting data models to human-readable formats.

These formatters produce markdown documents from the structured data
for human review and as pitch materials.
"""

from .models import Concept, ConceptBrief, StrategicDossier


def dossier_to_markdown(dossier: StrategicDossier) -> str:
    """
    Convert a strategic dossier to human-readable markdown.
    
    Args:
        dossier: The strategic dossier to format
        
    Returns:
        Markdown formatted string
    """
    lines = [
        f"# Strategic Dossier: {dossier.company_name}",
        "",
        f"*Generated: {dossier.generated_at.strftime('%Y-%m-%d %H:%M UTC')}*",
        "",
        "---",
        "",
        "## 1. Brand Identity Snapshot",
        "",
        f"**Positioning:** {dossier.brand_identity.positioning}",
        "",
        "### Visual Identity",
        f"- Primary Color: {dossier.brand_identity.visual_markers.primary_color}",
    ]
    
    if dossier.brand_identity.visual_markers.secondary_colors:
        lines.append(
            f"- Secondary Colors: {', '.join(dossier.brand_identity.visual_markers.secondary_colors)}"
        )
    
    if dossier.brand_identity.visual_markers.style_keywords:
        lines.append(
            f"- Style Keywords: {', '.join(dossier.brand_identity.visual_markers.style_keywords)}"
        )
    
    if dossier.brand_identity.visual_markers.tone_keywords:
        lines.append(
            f"- Tone Keywords: {', '.join(dossier.brand_identity.visual_markers.tone_keywords)}"
        )
    
    if dossier.brand_identity.voice_characteristics:
        lines.extend([
            "",
            "### Voice Characteristics",
        ])
        for char in dossier.brand_identity.voice_characteristics:
            lines.append(f"- {char}")
    
    # Strategic Priorities
    lines.extend([
        "",
        "---",
        "",
        "## 2. Strategic Priorities (Ranked)",
        "",
    ])
    
    for priority in sorted(dossier.strategic_priorities, key=lambda p: p.rank):
        lines.extend([
            f"### #{priority.rank}: {priority.priority}",
            f"*Execution: {priority.execution_assessment.value.title()}*",
            "",
        ])
        if priority.evidence:
            lines.append("**Evidence:**")
            for ev in priority.evidence:
                lines.append(f"- {ev}")
            lines.append("")
    
    # Marketing Posture
    lines.extend([
        "---",
        "",
        "## 3. Marketing Posture Analysis",
        "",
    ])
    
    if dossier.marketing_posture.current_content_types:
        lines.append("### Current Content Types")
        for ct in dossier.marketing_posture.current_content_types:
            lines.append(f"- {ct}")
        lines.append("")
    
    if dossier.marketing_posture.channel_presence:
        lines.append("### Channel Presence")
        for channel, presence in dossier.marketing_posture.channel_presence.items():
            status = "✅ Active" if presence.active else "❌ Inactive"
            lines.append(f"- **{channel.title()}:** {status}")
            if presence.assessment:
                lines.append(f"  - {presence.assessment}")
        lines.append("")
    
    if dossier.marketing_posture.apparent_gaps:
        lines.append("### Apparent Gaps")
        for gap in dossier.marketing_posture.apparent_gaps:
            lines.append(f"- {gap}")
        lines.append("")
    
    if dossier.marketing_posture.audience_engagement:
        lines.extend([
            "### Audience Engagement",
            dossier.marketing_posture.audience_engagement,
            "",
        ])
    
    # Competitive Analysis
    lines.extend([
        "---",
        "",
        "## 4. Competitive Pressure Points",
        "",
    ])
    
    if dossier.competitive_analysis.key_competitors:
        lines.append("### Key Competitors")
        for comp in dossier.competitive_analysis.key_competitors:
            threat_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[comp.threat_level.value]
            lines.extend([
                f"#### {comp.name} {threat_emoji}",
                f"*Threat Level: {comp.threat_level.value.title()}*",
                "",
                f"Content Strategy: {comp.content_strategy}",
                "",
            ])
    
    if dossier.competitive_analysis.brand_winning_areas:
        lines.append("### Where Brand is Winning")
        for area in dossier.competitive_analysis.brand_winning_areas:
            lines.append(f"- ✅ {area}")
        lines.append("")
    
    if dossier.competitive_analysis.brand_losing_areas:
        lines.append("### Where Brand is Losing")
        for area in dossier.competitive_analysis.brand_losing_areas:
            lines.append(f"- ⚠️ {area}")
        lines.append("")
    
    # Strategic Tensions (THE GOLD)
    lines.extend([
        "---",
        "",
        "## 5. Strategic Tensions ⭐",
        "",
        "*These tensions are the primary input for concept generation.*",
        "",
    ])
    
    for tension in sorted(dossier.strategic_tensions, key=lambda t: t.priority_score, reverse=True):
        priority_stars = "⭐" * tension.priority_score
        lines.extend([
            f"### {tension.id}: {tension.description}",
            f"*Type: {tension.opportunity_type.value.replace('_', ' ').title()}* | "
            f"*Priority: {priority_stars}*",
            "",
        ])
        if tension.evidence:
            lines.append("**Evidence:**")
            for ev in tension.evidence:
                lines.append(f"- {ev}")
            lines.append("")
    
    # Opportunity Zones
    lines.extend([
        "---",
        "",
        "## 6. Creative Opportunity Zones",
        "",
    ])
    
    for opp in dossier.opportunity_zones:
        risk_emoji = {"low": "🟢", "medium": "🟡", "high": "🔴"}[opp.risk_level.value]
        lines.extend([
            f"### {opp.id}: {opp.description}",
            f"*Risk: {opp.risk_level.value.title()}* {risk_emoji}",
            "",
            f"**Rationale:** {opp.rationale}",
            "",
        ])
    
    # Sources
    lines.extend([
        "---",
        "",
        "## 7. Sources",
        "",
    ])
    
    for i, source in enumerate(dossier.sources, 1):
        lines.append(f"{i}. [{source.title}]({source.url}) - *{source.type.value}*")
    
    return "\n".join(lines)


def concept_to_markdown(concept: Concept) -> str:
    """
    Convert a concept to human-readable markdown.
    
    Args:
        concept: The concept to format
        
    Returns:
        Markdown formatted string
    """
    lines = [
        f"# {concept.title}",
        "",
        f"**{concept.id.replace('_', ' ').title()}**",
        "",
        "---",
        "",
        "## The Hook",
        "",
        f"> {concept.hook}",
        "",
        "## The Premise",
        "",
        concept.premise,
        "",
        "---",
        "",
        "## Format Specification",
        "",
        f"- **Series Type:** {concept.format.series_type.value.title()}",
        f"- **Episode Length:** {concept.format.episode_length}",
        f"- **Cadence:** {concept.format.cadence}",
    ]
    
    if concept.format.season_length:
        lines.append(f"- **Season Length:** {concept.format.season_length}")
    
    # Platform Strategy
    lines.extend([
        "",
        "## Platform Strategy",
        "",
        f"### Primary: {concept.platform_strategy.primary.platform.title()}",
        f"{concept.platform_strategy.primary.rationale}",
        "",
    ])
    
    if concept.platform_strategy.secondary:
        lines.append("### Secondary Platforms")
        for plat in concept.platform_strategy.secondary:
            lines.append(f"- **{plat.platform.title()}:** {plat.adaptation}")
        lines.append("")
    
    if concept.platform_strategy.amplification:
        lines.extend([
            "### Amplification",
            concept.platform_strategy.amplification,
            "",
        ])
    
    # Series Structure
    lines.extend([
        "---",
        "",
        "## Series Structure",
        "",
    ])
    
    if concept.series_structure.recurring_elements:
        lines.append("### Recurring Elements")
        for elem in concept.series_structure.recurring_elements:
            lines.append(f"- {elem}")
        lines.append("")
    
    if concept.series_structure.variable_elements:
        lines.append("### Variable Elements")
        for elem in concept.series_structure.variable_elements:
            lines.append(f"- {elem}")
        lines.append("")
    
    if concept.series_structure.host_approach:
        lines.extend([
            "### Host/Talent Approach",
            concept.series_structure.host_approach,
            "",
        ])
    
    # Brand Integration
    lines.extend([
        "---",
        "",
        "## Brand Integration Philosophy",
        "",
        concept.brand_integration.philosophy,
        "",
    ])
    
    if concept.brand_integration.integration_method:
        lines.append(f"**Integration Method:** {concept.brand_integration.integration_method}")
    if concept.brand_integration.screen_time_balance:
        lines.append(f"**Screen Time Balance:** {concept.brand_integration.screen_time_balance}")
    if concept.brand_integration.cta_approach:
        lines.append(f"**CTA Approach:** {concept.brand_integration.cta_approach}")
    
    # Episode Concepts
    lines.extend([
        "",
        "---",
        "",
        "## Episode Concepts",
        "",
    ])
    
    for ep in concept.episode_concepts:
        lines.append(f"{ep.number}. **{ep.title}** — {ep.description}")
    
    # Why This Wins
    lines.extend([
        "",
        "---",
        "",
        "## Why This Wins",
        "",
        f"### Strategic Alignment",
        concept.why_this_wins.strategic_alignment,
        "",
        f"### Competitive Differentiation",
        concept.why_this_wins.competitive_differentiation,
        "",
        f"### Audience Value Proposition",
        concept.why_this_wins.audience_value_proposition,
        "",
    ])
    
    # Execution
    lines.extend([
        "---",
        "",
        "## Execution Pathway",
        "",
        f"- **Production Complexity:** {concept.execution.complexity.value.title()}",
        f"- **Budget Tier:** {concept.execution.budget_tier.value.title()}",
        f"- **Timeline to First Episode:** {concept.execution.timeline_to_first_episode}",
        "",
    ])
    
    # Risks
    if concept.risks:
        lines.extend([
            "---",
            "",
            "## Risks & Mitigations",
            "",
        ])
        for risk in concept.risks:
            lines.extend([
                f"**Risk:** {risk.risk}",
                f"**Mitigation:** {risk.mitigation}",
                "",
            ])
    
    return "\n".join(lines)


def brief_to_markdown(brief: ConceptBrief) -> str:
    """
    Convert a concept brief to markdown.
    
    Args:
        brief: The brief to format
        
    Returns:
        Markdown formatted string
    """
    slot_names = {
        "safe_bet": "The Safe Bet",
        "challenger": "The Challenger",
        "moonshot": "The Moonshot",
    }
    
    lines = [
        f"# Concept Brief: Slot {brief.slot_id}",
        "",
        f"**Type:** {slot_names.get(brief.slot_type.value, brief.slot_type.value)}",
        "",
        "---",
        "",
        "## Strategic Assignment",
        "",
        f"**Tension ID:** `{brief.assigned_tension_id}`",
        "",
        f"**Focus:** {brief.strategic_focus}",
        "",
        "## Creative Parameters",
        "",
        f"- **Platform Focus:** {brief.platform_focus.value.title()}",
        f"- **Risk Profile:** {brief.risk_profile.value.title()}",
        "",
        "### Format Guidance",
        brief.format_guidance,
        "",
        "## Success Hypothesis",
        "",
        f"> {brief.success_hypothesis}",
        "",
    ]
    
    return "\n".join(lines)


def concepts_summary_markdown(concepts: list[Concept]) -> str:
    """
    Create a summary of all concepts for quick reference.
    
    Args:
        concepts: List of concepts to summarize
        
    Returns:
        Markdown formatted summary
    """
    lines = [
        "# Concept Summary",
        "",
        "---",
        "",
    ]
    
    for concept in concepts:
        concept_num = concept.id.split("_")[1]
        lines.extend([
            f"## Concept {concept_num}: {concept.title}",
            "",
            f"**Hook:** {concept.hook}",
            "",
            f"{concept.premise}",
            "",
            f"- **Format:** {concept.format.series_type.value.title()} | "
            f"{concept.format.episode_length} | {concept.format.cadence}",
            f"- **Primary Platform:** {concept.platform_strategy.primary.platform.title()}",
            f"- **Production:** {concept.execution.complexity.value.title()} complexity | "
            f"{concept.execution.budget_tier.value.title()} budget",
            "",
            "---",
            "",
        ])
    
    return "\n".join(lines)
