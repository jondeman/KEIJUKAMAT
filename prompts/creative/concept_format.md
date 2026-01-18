# Concept Document Format

Output your concept as a JSON object with the following structure:

```json
{
  "id": "concept_01",  // Must be concept_01, concept_02, or concept_03
  
  "title": "The Series Title",  // Punchy, memorable title
  
  "hook": "One sentence that makes a CMO care immediately.",
  
  "premise": "2-3 sentences explaining the series concept. What is it? What happens? Why does it exist?",
  
  "long_form_extension": "Explicit long-form/broadcast extension option (e.g., Ruutu+/Katsomo/Total-TV, or 3x21min broadcast cut).",
  
  "format": {
    "series_type": "ongoing",  // ongoing, limited, seasonal, or event
    "episode_length": "8-12 minutes",  // Specific duration range
    "cadence": "Weekly",  // How often episodes release
    "season_length": "10 episodes"  // null for ongoing, specific for others
  },
  
  "platform_strategy": {
    "primary": {
      "platform": "YouTube",  // Primary platform
      "rationale": "Why this platform is right for this content"
    },
    "secondary": [
      {
        "platform": "Instagram",
        "adaptation": "How content adapts for this platform"
      }
    ],
    "amplification": "How content will be promoted beyond organic reach"
  },
  
  "series_structure": {
    "recurring_elements": [
      "Elements that appear in every episode"
    ],
    "variable_elements": [
      "Elements that change to keep it fresh"
    ],
    "host_approach": "How hosting/talent is handled"
  },
  
  "brand_integration": {
    "philosophy": "Overall approach to how brand appears",
    "integration_method": "Specific tactics for brand presence",
    "screen_time_balance": "e.g., 80% content, 20% brand",
    "cta_approach": "How calls-to-action are handled"
  },
  
  "episode_concepts": [
    {
      "number": 1,
      "title": "Episode Title",
      "description": "One sentence episode description"
    }
    // Must have exactly 6 episodes
  ],
  
  "why_this_wins": {
    "strategic_alignment": "How this addresses the strategic tension",
    "competitive_differentiation": "Why this is unique in the market",
    "audience_value_proposition": "Why audiences would watch"
  },
  
  "execution": {
    "complexity": "medium",  // low, medium, or high
    "budget_tier": "mid",  // budget, mid, or premium
    "timeline_to_first_episode": "8-10 weeks"  // Realistic timeline
  },
  
  "risks": [
    {
      "risk": "Description of potential risk",
      "mitigation": "How to address this risk"
    }
  ]
}
```

## Field Requirements

### Required Fields (must not be empty)
- `id` - Must match assigned concept slot
- `title` - Must be memorable and specific
- `hook` - Must clearly state CMO value
- `premise` - Must be 2-3 complete sentences
- `long_form_extension` - Must explicitly mention the long-form/broadcast extension
- All `format` fields
- `platform_strategy.primary` with both platform and rationale
- All `series_structure` fields
- `brand_integration.philosophy`
- Exactly 6 `episode_concepts`
- All `why_this_wins` fields
- All `execution` fields
- At least 2 `risks`

### Validation Rules
- `episode_concepts` must have exactly 6 items
- `format.series_type` must be one of: ongoing, limited, seasonal, event
- `execution.complexity` must be one of: low, medium, high
- `execution.budget_tier` must be one of: budget, mid, premium
