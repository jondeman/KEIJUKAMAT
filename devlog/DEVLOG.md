# KonseptiKeiju Development Log

## Project Status

**Current Phase:** Phase 4 - AD Bot Development 🚧

- Phase 1 (Foundation): ✅ Complete
- Phase 2 (Research Bot): ✅ **Complete & Tested**
- Phase 3 (Creative Bot): ✅ **Complete & Tested** (3 treatments per company)
- Phase 4 (AD Bot): 🚧 **In Progress** (Logo + Color fetching done)
- Phase 5 (Integration): 🔲 Pending

**First successful real research completed!** Puuilo company analysis produced:
- 15,564 chars of strategic research
- 4 strategic tensions with creative directions
- 5 opportunity zones
- 100+ sources

Research pipeline is robust with immediate artifact saving, retry logic for 503 errors, and fallback mechanisms for JSON parsing failures.

---

## Phase 1: Foundation (Complete)

### Components Built

#### Core (`src/core/`)
- ✅ `models.py` - All Pydantic data models
- ✅ `config.py` - Environment-based configuration
- ✅ `filesystem.py` - Path management and file I/O
- ✅ `state.py` - Run state and archive management
- ✅ `logger.py` - Structured logging with run-specific logs
- ✅ `validators.py` - Schema and quality validation
- ✅ `formatters.py` - Markdown output generation

#### Orchestrator (`src/orchestrator/`)
- ✅ `producer.py` - Main pipeline orchestration
- ✅ `state_machine.py` - Phase transition management
- ✅ `strategize.py` - Tension-to-slot assignment
- ✅ `quality_gates.py` - Phase validation
- ✅ `pitch_composer.py` - Email generation

#### Bots (`src/bots/`)
- ✅ `research/bot.py` - Research with Gemini Deep Research
- ✅ `research/synthesizer.py` - Research analysis pipeline
- ✅ `creative/bot.py` - Mock concept generation
- ✅ `ad/bot.py` - Mock one-pager generation

#### Integrations (`src/integrations/`)
- ✅ `gemini/client.py` - Gemini API with Deep Research polling
- ✅ `claude/client.py` - Claude API wrapper (stub)
- ✅ `nanobanana/client.py` - Nano Banana wrapper (stub)
- ✅ `email/client.py` - SMTP email client

#### Prompts (`prompts/`)
- ✅ Research prompts (system, query, diagnostic)
- ✅ Creative prompts (system, generation, format, critique, refinement)
- ✅ AD prompts (system, philosophy, prompt builder, brand adaptation)
- ✅ Producer prompts (strategize, pitch email, quality gates)

#### Schemas (`schemas/`)
- ✅ `strategic_dossier.schema.json`
- ✅ `concept_brief.schema.json`
- ✅ `concept.schema.json`
- ✅ `onepager_spec.schema.json`
- ✅ `run_state.schema.json`

#### Web Interface (`web/`)
- ✅ `index.html` - Input form
- ✅ `status.html` - Progress tracking
- ✅ `static/style.css` - Beautiful dark theme UI

#### Tests (`tests/`)
- ✅ `conftest.py` - Fixtures
- ✅ `test_models.py` - Model validation tests
- ✅ `test_research_bot.py` - Research bot tests
- ✅ `test_creative_bot.py` - Creative bot tests
- ✅ `test_orchestrator.py` - Orchestrator tests

### Next Steps for Testing

1. **Run the mock pipeline:**
   ```bash
   python -m src.main run "Nike"
   ```

2. **Start the web server:**
   ```bash
   python -m src.main
   # Open http://localhost:8000
   ```

3. **Run the test suite:**
   ```bash
   pytest -v
   ```

---

## Phase 2: Research Bot ✅ (Complete)

### Goals
- Real Gemini API integration
- Deep research query execution
- Dossier synthesis from raw research

### Implementation Summary

The Research Bot now has a complete analysis pipeline with full artifact traceability:

#### Pipeline Flow
```
1. Company Name + Context
      ↓
2. Gemini Deep Research Query (long-running agentic process)
      ↓
3. Raw Research Markdown (stored as research_raw.md)
      ↓
4. Section Extraction (stored as research_sections.json)
      ↓
5. Diagnostic Framework Analysis (stored as research_analysis.md)
      ↓
6. Structured Strategic Dossier (JSON + Markdown)
      ↓
7. All Artifacts + Metadata Saved
```

#### Artifacts Produced per Research Run

| File | Description |
|------|-------------|
| `research_raw.md` | Original Deep Research output |
| `research_sections.json` | Parsed sections (summary, news, marketing, etc.) |
| `research_analysis.md` | Diagnostic analysis applying our framework |
| `strategic_dossier.json` | Final structured dossier (Pydantic validated) |
| `strategic_dossier.md` | Human-readable version |
| `research_metadata.json` | Timing, model info, prompts used |
| `prompts_used.md` | All prompts for debugging/iteration |

#### Key Files
- `src/bots/research/bot.py` - Main ResearchBot class
- `src/bots/research/synthesizer.py` - ResearchSynthesizer analysis pipeline
- `prompts/research/diagnostic_framework.md` - Analysis framework

### Tasks
- [x] Test Gemini API key configuration
- [x] Implement real `deep_research` method with polling
- [x] Implement `ResearchSynthesizer` with section extraction
- [x] Implement `save_research_artifacts` with full traceability
- [ ] Test with 5 real companies
- [ ] Refine research prompts based on output quality

### Success Criteria
- Dossiers identify genuine strategic tensions
- Evidence is based on real, findable sources
- Tensions are specific enough to guide concepts
- All artifacts saved for debugging and prompt refinement

---

## Phase 3: Creative Bot

### Goals
- Real Claude API integration
- Concept generation with self-critique
- Quality consistency across runs

### Tasks
- [ ] Test Claude API key configuration
- [ ] Implement real concept generation
- [ ] Implement self-critique loop
- [ ] Test with 5 real dossiers
- [ ] Refine creative prompts based on quality

### Success Criteria
- Concepts clearly address assigned tensions
- Format is specific and executable
- CMO hook is compelling in every concept

---

## Phase 4: AD Bot 🚧

### Goals
- Real image generation
- Brand-adaptive styling
- Professional-quality one-pagers

### Tasks
- [x] Logo fetching (Wikipedia, Clearbit)
- [x] Producer logo copy (WVITVPlogo.png)
- [x] Brand color seeker (Brandfetch, Wikipedia, logo extraction, Gemini search)
- [x] Treatment-based one-pager prompt template
- [ ] Gemini Image model integration (gemini-3-pro-image-preview)
- [ ] Test with real treatments
- [ ] Refine image prompts based on quality

### Success Criteria
- One-pagers are visually distinctive
- Text is legible
- Brand colors are appropriately applied
- Would not embarrass if shown to a real CMO

---

## Phase 5: Integration & Polish

### Goals
- Robust error handling
- Email delivery working
- Full end-to-end reliability

### Tasks
- [ ] Add proper error recovery
- [ ] Implement email delivery
- [ ] Create shareable package links
- [ ] End-to-end testing with 10 companies
- [ ] Performance optimization

### Success Criteria
- 90%+ success rate on full runs
- Average run time under 5 minutes
- Output quality consistent across companies

---

## Architecture Decisions

### Why Mock-First?
Building the full pipeline with mocks first ensures:
1. All data flows are validated before API costs
2. Tests can run without API keys
3. Development can proceed in parallel

### Why Pydantic?
- Strong typing prevents data corruption
- Validation at boundaries catches errors early
- JSON serialization is automatic

### Why Structured Logging?
- Debug issues across async operations
- Track API usage and costs
- Audit trail for every run

### Why Markdown Prompts?
- Version control for prompt iterations
- Human-readable for collaboration
- Easy to edit without code changes

### Why Two-Phase Research Synthesis?
Instead of directly parsing Deep Research output to JSON:
1. **First pass**: Apply diagnostic framework to identify tensions (stored as `research_analysis.md`)
2. **Second pass**: Structure the analysis into validated JSON

Benefits:
- Intermediate output visible for debugging
- Diagnostic framework can be refined separately
- JSON structuring is more reliable with pre-analyzed content
- Full traceability: raw → sections → analysis → structured

### Why Save All Prompts Used?
Every research run saves `prompts_used.md` containing all prompts sent to APIs because:
- Enables A/B testing of prompt variations
- Debug why specific runs produced certain outputs
- Iterate on prompts with full context
- Track prompt evolution over time

---

## Known Issues

1. **Image generation in mock mode** creates minimal placeholder PNGs. Install Pillow for better mock images.

2. **Archive path** requires manual creation of `archive/` directory on first run.

3. **State resumption** is implemented but not fully tested with interrupted runs.

4. **Gemini model availability varies:**
   - `gemini-3-flash-preview` returns empty content with Search Grounding - **do not use**
   - `gemini-2.5-flash` works reliably ✅
   - API may return 503 "model overloaded" during high-traffic periods - retry logic handles this

5. **JSON structuring sometimes fails** if the diagnostic analysis is very long or complex. The fallback dossier will be created, but manual review of `research_analysis.md` is recommended.

---

## Metrics to Track

Once running with real APIs:

- **Success rate:** % of runs reaching DONE
- **Research quality:** Manual scoring of dossier insights
- **Concept quality:** Manual scoring of CMO relevance
- **One-pager quality:** Would you forward it? (binary)
- **API costs:** Tokens/images per run
- **Run time:** Total time from input to delivery

---

## Changelog

### v0.1.42 (2026-01-18)
- ✅ **Deliveries repo separation**
  - Use dedicated GitHub repo for deliveries (KEIJUKAMAT)
  - Prevents backend redeploys triggered by delivery pushes

### v0.1.41 (2026-01-18)
- ✅ **GitHub publish auto-rebase**
  - Render now fetches + rebases before pushing deliveries
  - Avoids "fetch first" push failures when remote is ahead

### v0.1.40 (2026-01-18)
- ✅ **SendGrid email support**
  - SendGrid HTTP API added (preferred for Gmail sender)
  - System test logs SendGrid/Resend/SMTP mode and config

### v0.1.39 (2026-01-18)
- ✅ **Resend email support**
  - Email now uses Resend HTTP API when configured (works on Render)
  - System test logs Resend/SMTP mode and config

### v0.1.38 (2026-01-18)
- ✅ **SMTP robustness**
  - Trim whitespace from SMTP env values (fixes trailing newline issue on Render)
  - System test logs now show SMTP user with repr for easier diagnostics

### v0.1.37 (2026-01-18)
- ✅ **GitHub publish reliability fixes**
  - Push now uses `HEAD:main` (detached HEAD safe)
  - Untracked delivery files included in change detection
  - System test logs Git identity + SMTP config details

### v0.1.36 (2026-01-17)
- ✅ **Run lock on backend**
  - New run requests are rejected while a run is active (HTTP 409)
  - Prevents accidental cancellations or overlapping runs on Render

### v0.1.35 (2026-01-17)
- ✅ **Removed PIL A4 resizing for one-pagers**
  - Reduces Render memory spikes by avoiding in‑memory bitmap resizes
  - One-pagers rely on prompt to request A4 vertical output

### v0.1.34 (2026-01-17)
- ✅ **Incremental GitHub publish**
  - Deliveries are pushed after each major phase (research/creative/onepagers)
  - Commit messages include phase suffix for traceability

### v0.1.33 (2026-01-17)
- ✅ **Status page diagnostics + raw log viewer**
  - `/api/diagnostics/{run_id}` shows phase history and last error
  - `/api/logs/{run_id}/raw` streams JSONL log lines to UI
- ✅ **Auto‑publish deliveries to GitHub**
  - Render now pushes `docs/deliveries` to GitHub on delivery
  - Added GitHub token/repo config settings

### v0.1.32 (2026-01-17)
- ✅ **Status page improvements**
  - Status UI localized to Finnish
  - Live log stream added (reads run logs)
  - Base path handling fixed for GitHub Pages subpaths
- ✅ **Backend support for live logs**
  - New `/api/logs/{run_id}` endpoint
  - CORS enabled for GitHub Pages origin

### v0.1.31 (2026-01-17)
- ✅ **Frontend/back‑end hosting split documented**
  - UI served via GitHub Pages
  - Backend expected to run on Render (or another host)

### v0.1.30 (2026-01-17)
- ✅ **One-pager storage trimmed to delivery only**
  - Run one-pager PNGs are deleted after delivery is built
  - Archive no longer creates onepager paths or folders

### v0.1.29 (2026-01-17)
- ✅ **Prompt logging split per one-pager**
  - One-pager prompts now saved as three separate `.md` files
  - Treatment-based prompts enforced in visualize pipeline
- ✅ **Concepts require explicit long-form extension**
  - `long_form_extension` added to concept schema and validation
  - Ensures Ruutu+/Katsomo/Total-TV option is always present

### v0.1.28 (2026-01-17)
- ✅ **AD Bot now uses treatment-based prompts in pipeline**
  - Visualize phase prefers treatments to produce Puuilo-style infographics
  - One-pagers saved as `concept_01/02/03.png` with full prompt logging
  - NanoBanana client now wraps Gemini Image (gemini-3-pro-image-preview)

### v0.1.27 (2026-01-16)
- ✅ **Creative concept generation updated**
  - All three concepts now generated in one Claude call for diversity
  - Prompt guidance includes WBITVP long‑form options, Akun Tehdas live tie‑in, and genAI as flavor (not the core)

### v0.1.26 (2026-01-16)
- ✅ **Additional context wired through prompts**
  - Lisähuomiot now injected into research, creative, and AD prompts
  - Stored as `additional_context.md` and included in delivery links
  - NanoBanana image generation falls back to Gemini on connection errors

### v0.1.25 (2026-01-16)
- ✅ **Lisähuomiot (Additional Context) end-to-end**
  - Tallennetaan `additional_context.md` run-kansioon
  - Lisäpainotus mukana tutkimus-, luova- ja AD‑prompteissa (kevyt painotus)
  - Lisähuomiot kopioidaan GitHub Pages -toimitukseen

### v0.1.24 (2026-01-16)
- ✅ **One-pager summary block**
  - Added MITÄ / MITEN / MIKSI summary lines near the title
  - Summaries are auto-extracted from treatment sections

### v0.1.23 (2026-01-16)
- ✅ **End-to-end delivery wiring**
  - Web form labels updated (FI) and two-column layout for name/email
  - Producer now builds GitHub Pages delivery folder with research, treatments, onepagers
  - SMTP delivery email sends links to published materials
  - New settings: `DELIVERY_BASE_URL`, `DELIVERY_PAGES_DIR`

### v0.1.22 (2026-01-16)
- ✅ **One-pager prompts saved per run**
  - Prompts now saved under `ONEPAGERS/PROMPTS/` with timestamped filename
  - Removes overwrite risk of `prompts_used.md`

### v0.1.21 (2026-01-16)
- ✅ **One-pager script supports explicit treatment paths**
  - `run_onepagers_from_treatments.py` now accepts specific treatment files
  - Enables generating a single one-pager without loading all three

### v0.1.20 (2026-01-16)
- ✅ **Brandfetch logo fetching**
  - Logo retrieval now uses Brandfetch assets when API key is set
  - Prefers PNG, then SVG, then any available format

### v0.1.19 (2026-01-16)
- ✅ **Improved logo/domain discovery**
  - Added domain variants for `&` → `and` / `ja`
  - Uses expanded domain candidates for Brandfetch, website scraping, and Clearbit logo

### v0.1.18 (2026-01-16)
- ✅ **Brandfetch API key support**
  - Added `BRANDFETCH_API_KEY` to settings and env.example
  - Brandfetch color lookup now uses Authorization header when key is present

### v0.1.17 (2026-01-16)
- ✅ **Brand color scraping from company website**
  - New website strategy parses homepage CSS + inline styles
  - Reads external stylesheets (limited) and `theme-color` meta
  - Extracts hex/rgb colors and ranks by frequency/colorfulness

### v0.1.16 (2026-01-16)
- ✅ **A4 one-pager sizing**
  - AD bot now enforces A4 portrait ratio with exact 2896×4096 output
  - Prompt updated to request A4 layout for one-pagers
  - Post-processing crops/fits Gemini output to A4 before saving

### v0.1.15 (2026-01-16)
- ✅ **Gemini Image fix**
  - Removed invalid `response_mime_type` for image generation
  - Uses `response_modalities=["IMAGE"]` for `gemini-3-pro-image-preview`

### v0.1.14 (2026-01-16)
- ✅ **Gemini Image 4K support**
  - `GeminiClient.generate_image()` now accepts `aspect_ratio` and `image_size`
  - AD one-pagers use `aspect_ratio="9:16"` and `image_size="4K"` for vertical 4K output
  - Prompt logging includes image size and aspect ratio metadata

### v0.1.13 (2026-01-16)
- ✅ **AD Bot: Brand Color Seeker**
  - New method `fetch_brand_colors()` automatically fetches company brand colors from web
  - Multi-strategy approach:
    1. **Brandfetch API** - Professional brand asset database
    2. **Wikipedia** - Extracts hex colors from company infoboxes
    3. **Logo color extraction** - Uses PIL to extract dominant colors from fetched logo
    4. **Gemini search** - Asks Gemini to find brand colors with search grounding
  - Falls back to professional blue theme if no colors found
  - Automatically integrated into `generate_onepagers_from_treatments()` flow
  - Returns dict with `primary_color`, `secondary_color`, `accent_color` (hex codes)
- ✅ **One-pager color integration**
  - Brand colors now automatically used in prompt when generating one-pagers
  - No manual color specification needed

### v0.1.12 (2026-01-16)
- ✅ **AD Bot: Treatment-based one-pager generation**
  - New method `generate_onepagers_from_treatments()` uses treatment markdown directly
  - Comprehensive prompt template `prompts/ad/onepager_image_template.md`
  - Prompt style based on proven Puuilo example (infographic layout, flowcharts, multi-section)
  - Slot-specific visual styles: Safe (warm/professional), Challenger (bold/energetic), Moonshot (cinematic/premium)
- ✅ **Gemini Image model integration**
  - New config `GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview`
  - `GeminiClient.generate_image()` method for image generation
  - Test script `scripts/run_onepagers_from_treatments.py`
- ✅ **Logo placement in prompts**
  - Warner Bros. logo (top left) + company logo (top right)
  - Discrete placement as professional identifiers

### v0.1.11 (2026-01-16)
- ✅ **AD Bot logo fetching**
  - Fetches company logo from web (Wikipedia, Clearbit fallback)
  - Copies `WVITVPlogo.png` into onepager logos folder
  - Saves logos to `runs/{run}/artifacts/onepagers/logos/`

### v0.1.10 (2026-01-16)
- ✅ **Claude prompt logging for treatments**
  - Treatment prompts + responses saved to `prompt_logs/creative/`
  - Log includes system + user prompt and full response
- ✅ **Treatment prompt aligned to single-call**
  - `treatment_generation.md` now instructs one concept per call

### v0.1.9 (2026-01-16)
- ✅ **Research model updated**
  - Default research model now `gemini-3-pro-preview` (was flash/2.5)
  - Config, README, and env.example aligned

### v0.1.8 (2026-01-16)
- ✅ **Treatments naming handled in Claude prompt**
  - Removed separate Gemini naming pass due to instability/timeouts
  - Added explicit instruction for strong, selling, on-brand naming in `treatment_generation.md`

### v0.1.7 (2026-01-16)
- ✅ **Creative testing script**
  - Added `scripts/test_creative.py` to generate concepts + treatments
  - Uses latest `runs/test_{company_slug}_*` dossier as input
  - Saves treatments under `runs/{company_name}/TREATMENTS/`

### v0.1.6 (2026-01-16)
- ✅ **Creative phase: Treatments output**
  - `CreativeBot.generate_treatments()` produces 3 Finnish treatment texts
  - Treatments saved to `runs/{company_name}/TREATMENTS/`
  - Filenames: `{company}_TREATMENT_{slot}_YYYYMMDD_HHMMSS.md`
- ✅ **New prompt: treatment generation**
  - Added `prompts/creative/treatment_generation.md` (Finnish structure)
  - `creative/system.md` localized to Finnish for creative stage
- ✅ **Pipeline wiring**
  - Producer now writes treatments during CREATE phase
  - Shared `company_folder_name()` utility added to filesystem
- ✅ **Concept generation prompt upgraded**
  - `prompts/creative/concept_generation.md` rewritten in Finnish with stronger creative and strategic requirements
  - Prompt now enforces non-generic, big-idea concepts while staying on brand
  - Concept generation uses fuller research context + Claude Opus 4.5 via `creative_generate()`

### v0.1.5 (2026-01-16)
- ✅ **Search Grounding -lähteet mukaan raw-raporttiin**
  - `GeminiClient.deep_research()` poimii grounding-citations/grounding metadata -lähteet, jos SDK palauttaa ne
  - Lähteet appendataan automaattisesti raw-tuloksen loppuun osioon: `## Lähteet (Search Grounding)`
  - Tavoite: raw-tuloksessa on lähteet, vaikka malli ei kirjoittaisi URL:eja itse tekstiosuuteen
- ✅ **Docs**
  - README päivitetty kuvaamaan lähteiden liittämistä raw-outputtiin

### v0.1.4 (2026-01-16)
- ✅ **Researcher outputs in Finnish**
  - Research system + deep research prompts translated to Finnish
  - Diagnostic framework and synthesis prompts localized to Finnish
  - Explicit "no creative ideation" constraint added
- ✅ **New research storage scheme**
  - On research start, prompt + raw output saved under `runs/{company_name}/`
  - No subfolders; filenames: `{company}_Research_YYYYMMDD_HHMMSS.md` and `{company}_Research_PROMPT_YYYYMMDD_HHMMSS.md`
  - Research phase no longer writes extra artifacts to run folders

### v0.1.3 (2026-01-16)
- ✅ **First Successful Real Research** - Puuilo company research completed!
  - **15,564 characters** of high-quality strategic research
  - Identified 4 strategic tensions with content directions
  - 5 creative opportunity zones
  - 100+ sources consulted
- ✅ **Robustness Improvements**
  - **Immediate artifact saving**: Raw research and sections saved instantly, preventing data loss if later steps fail
  - **`retry_on_overload()`**: New helper function with exponential backoff (10s → 20s → 40s → 80s → 160s) for 503 "model overloaded" errors
  - **Diagnostic analysis saved early**: Analysis saved before JSON structuring attempt
  - **JSON fixing**: `_fix_json()` removes trailing commas and control characters
  - **AI-powered JSON repair**: `_try_parse_json_with_ai_fix()` attempts to fix malformed JSON using Gemini
  - **Fallback dossier**: `_create_fallback_dossier()` creates minimal valid structure if all parsing fails
- ✅ **Model Selection**
  - `gemini-3-flash-preview` produced **empty responses** - switched to `gemini-2.5-flash`
  - `gemini-2.5-flash` works reliably with Search Grounding
- ✅ **Prompt Logging System** (`src/core/prompt_logger.py`)
  - Logs all prompts and responses for traceability
  - Automatic cleanup of logs older than 14 days
  - Categorized by bot and date

### v0.1.2 (2026-01-16)
- ✅ **Research Synthesis Pipeline** - Complete analysis system with traceability
  - `ResearchSynthesizer` class for structured analysis
  - Section extraction from raw research (summary, news, marketing, competitive, etc.)
  - Diagnostic framework application with Gemini
  - Full artifact saving with metadata
  - Prompts used logged for iteration
- ✅ **ResearchArtifacts dataclass** - Container for all research outputs
- ✅ **save_research_artifacts()** - Saves 7 artifact files per research run
- ✅ **Updated ResearchBot** - Returns artifacts alongside dossier
- ✅ **Updated Producer** - Handles new research return format

### v0.1.1 (2026-01-16)
- ✅ **Gemini Deep Research Integration** - Implementation using `google-genai` SDK
  - Uses Search Grounding with `generate_content()` for reliable research
  - Falls back to direct generation if search grounding unavailable
  - Console status updates during research
- ✅ **Updated AI Models**
  - Gemini: `gemini-2.5-flash` (stable, works with Search Grounding)
  - Claude: `claude-opus-4-20250514`
- ✅ **Added requirements.txt** - Standalone pip install support
- ✅ **Added requirements-dev.txt** - Development dependencies
- ✅ **Added google-genai SDK** - New dependency for Deep Research

### v0.1.0 (Initial)
- Complete foundation with mock implementations
- Web interface with progress tracking
- Full test suite
- All prompts and schemas

---

## Installation

### Option 1: Using pip with requirements.txt
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# For development
pip install -r requirements-dev.txt
```

### Option 2: Using pip with pyproject.toml
```bash
# Install as editable package
pip install -e .

# With dev dependencies
pip install -e ".[dev]"
```

---

## API Keys Required

| Service | Environment Variable | Used For |
|---------|---------------------|----------|
| Google Gemini | `GEMINI_API_KEY` | Deep Research |
| Anthropic Claude | `ANTHROPIC_API_KEY` | Concept Generation |
| Nano Banana Pro | `NANOBANANA_API_KEY` | Image Generation |

Set `USE_MOCK_APIS=true` in `.env` to test without API keys.

---

## Key Files Reference

### Research Pipeline
| File | Purpose |
|------|---------|
| `src/bots/research/bot.py` | Main ResearchBot class, orchestrates research |
| `src/bots/research/synthesizer.py` | ResearchSynthesizer, artifact management, JSON repair |
| `src/integrations/gemini/client.py` | Gemini API client with Search Grounding |
| `src/core/prompt_logger.py` | Prompt/response logging with auto-cleanup |
| `prompts/research/system.md` | Research bot system prompt |
| `prompts/research/deep_research_query_v2.md` | Optimized query for autonomous agents |
| `prompts/research/diagnostic_framework.md` | Framework for identifying tensions |
| `prompts/research/PROMPT_GUIDE.md` | Guide for writing Deep Research prompts |

### Creative Pipeline
| File | Purpose |
|------|---------|
| `src/bots/creative/bot.py` | Main CreativeBot class |
| `src/integrations/claude/client.py` | Claude API client |
| `prompts/creative/system.md` | Creative bot system prompt |
| `prompts/creative/concept_generation.md` | Concept generation prompt |
| `prompts/creative/self_critique.md` | Self-critique loop prompt |

### Visual Pipeline
| File | Purpose |
|------|---------|
| `src/bots/ad/bot.py` | Main ADBot class, logo fetching, brand color seeker |
| `src/integrations/nanobanana/client.py` | Image generation client |
| `prompts/ad/system.md` | AD bot system prompt |
| `prompts/ad/prompt_builder.md` | Image prompt construction |
| `prompts/ad/onepager_image_template.md` | Treatment-to-image prompt template |

### Orchestration
| File | Purpose |
|------|---------|
| `src/orchestrator/producer.py` | Main pipeline orchestrator |
| `src/orchestrator/state_machine.py` | Phase transitions |
| `src/orchestrator/strategize.py` | Tension-to-concept-slot assignment |
| `src/orchestrator/quality_gates.py` | Phase validation logic |
| `src/orchestrator/pitch_composer.py` | Email generation |

### Core
| File | Purpose |
|------|---------|
| `src/core/models.py` | All Pydantic data models |
| `src/core/config.py` | Environment configuration |
| `src/core/filesystem.py` | Path management, file I/O |
| `src/core/state.py` | Run state, archive management |
| `src/core/logger.py` | Structured logging |
| `src/core/prompt_logger.py` | Prompt/response logging, auto-cleanup |

---

*Last updated: 2026-01-18 14:08*
