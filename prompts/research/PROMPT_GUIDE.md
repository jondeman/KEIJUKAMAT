# Deep Research Prompting Guide

## How Gemini Deep Research Works

Gemini Deep Research is an **autonomous agent** that:

1. **Receives a query** and optional context
2. **Creates a research plan** (sub-questions, sources to check)
3. **Iteratively gathers information** (searches → reads → identifies gaps → searches more)
4. **Synthesizes a report** with findings and source citations

### Key Insight
> The agent is designed to PLAN its own research methodology. 
> Over-specifying HOW to research reduces effectiveness.

---

## Prompting Best Practices

### ✅ DO: Be Outcome-Focused

```
GOOD: "Research Nike to understand their strategic priorities 
       and content gaps for a branded video opportunity analysis"

BAD:  "First search for Nike press releases, then check their 
       YouTube channel, then analyze competitors..."
```

### ✅ DO: Use Clear Research Questions

```
GOOD: "Answer these questions:
       1. What are their top 3 strategic priorities?
       2. Where is their content strategy weak?
       3. What are competitors doing better?"

BAD:  "Tell me everything about the company's marketing"
```

### ✅ DO: Request Specific Evidence Types

```
GOOD: "Look for evidence in CEO interviews, earnings calls, 
       recent press releases, and social media activity"

BAD:  "Research their strategy"
```

### ✅ DO: Separate Research from Analysis

```
PIPELINE:
1. Deep Research → Raw findings with sources
2. Diagnostic Analysis → Apply strategic framework
3. Structuring → Convert to validated JSON
```

### ❌ DON'T: Over-Specify Methodology

```
BAD: "### Phase 1: Wide Scan
      Query areas to explore:
      - Recent news and announcements (last 6 months)
      - Marketing campaigns (last 3 years)..."
```

The agent will create its own research plan. Let it.

### ❌ DON'T: Request Too Many Output Formats

```
BAD: "Output as JSON with these exact fields:
      company_name, brand_identity.positioning..."
```

Let the agent produce natural findings first, then structure separately.

---

## Optimal Prompt Structure

```markdown
# Research Mission
[1-2 sentences: What you need and why]

## Core Research Questions
[3-5 specific questions to answer]

## Context (optional)
[Any additional guidance or focus areas]

## Output Requirements
[What the output should contain, not its exact format]
```

### Example: Optimal Deep Research Prompt

```markdown
# Research Mission
Research **Puuilo** to prepare strategic intelligence for a 
branded video content opportunity assessment.

## Core Research Questions
1. **IDENTITY**: How do they position themselves? Brand personality?
2. **STRATEGY**: What are their top 3-5 priorities right now?
3. **CONTENT GAP**: What content should they be producing but aren't?
4. **COMPETITION**: Who threatens them? Who has better content?
5. **TENSION**: Where do aspirations not match execution?

## Context
Focus on opportunities for branded entertainment, not traditional ads.

## Output Requirements
- Evidence-based findings with source citations
- Specific observations, not generic statements
- All URLs consulted
```

---

## The Two-Phase Analysis Pipeline

### Phase 1: Research (Agent-Driven)
- Let Gemini Deep Research do what it does best
- Don't constrain its methodology
- Collect raw findings with sources

### Phase 2: Analysis (Framework-Driven)
- Apply our diagnostic framework to raw findings
- Extract strategic tensions using our template
- Structure into validated data models

### Why Separate?
1. **Agent autonomy** → Better research quality
2. **Framework consistency** → Reliable outputs
3. **Debugging** → See raw vs analyzed separately
4. **Iteration** → Improve prompts independently

---

## Prompt Versions

| Version | File | Description |
|---------|------|-------------|
| v1 (original) | `deep_research_query.md` | Detailed, prescriptive |
| v2 (optimized) | `deep_research_query_v2.md` | Concise, outcome-focused |

### Recommendation
Use **v2** for production. It's shorter, clearer, and lets the 
agent leverage its planning capabilities.

---

## Metrics to Track

When comparing prompt versions:

1. **Research Quality**
   - Number of sources found
   - Relevance of sources
   - Depth of findings

2. **Tension Quality**
   - Specificity (not generic)
   - Evidence-backed
   - Actionable for creative

3. **Efficiency**
   - Token usage
   - Time to complete
   - Retries needed

---

## Sources

- [Google AI: Deep Research Docs](https://ai.google.dev/gemini-api/docs/deep-research)
- [Google Blog: Deep Research Tips](https://blog.google/products-and-platforms/products/gemini/tips-how-to-use-deep-research/)
- [Google Blog: Deep Research for Developers](https://blog.google/innovation-and-ai/technology/developers-tools/deep-research-agent-gemini-api/)
