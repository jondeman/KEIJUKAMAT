# KonseptiKeiju 🔮

**AI-powered branded entertainment concept generator**

Transform any company name into three strategically-aligned video concepts with stunning visual one-pagers—in minutes, not weeks.

## What It Does

KonseptiKeiju is an automated pipeline that:

1. **Researches** the target company using Gemini Deep Research
2. **Identifies** strategic tensions and opportunities
3. **Generates** three differentiated video concepts using Claude
4. **Creates** beautiful visual one-pagers using AI image generation
5. **Composes** a pitch email with strategic rationale
6. **Logs** one-pager prompts per concept for traceability (`artifacts/onepagers/PROMPTS/`)

Each run produces a complete pitch package: strategic dossier, three concept documents, three visual one-pagers, and a draft pitch email.

## The Three Concepts

Every run produces three strategically differentiated concepts:

| Slot | Name | Risk Profile | Platform |
|------|------|--------------|----------|
| 01 | The Safe Bet | Low | YouTube long-form |
| 02 | The Challenger | Medium | TikTok/Reels-first |
| 03 | The Moonshot | High | Cross-platform event |

This ensures the portfolio has something for every CMO's risk appetite.

## Quick Start

### Prerequisites

- Python 3.11+
- API keys for:
  - Google Gemini (research)
  - Anthropic Claude (creative)
- Gemini Image (Nano Banana Pro) (image generation)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/konseptikeiju.git
cd konseptikeiju

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies (choose one method)

# Option 1: Using requirements.txt
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For testing

# Option 2: Using pyproject.toml (editable install)
pip install -e ".[dev]"

# Copy and configure environment
cp env.example .env
# Edit .env with your API keys
```

### Running

**Option 1: Web Interface**

```bash
python -m src.main

# Open http://localhost:8000
```

**Option 2: CLI**

```bash
python -m src.main run "Nike"
```

**Option 3: Mock Mode (No API keys needed)**

```bash
# Set in .env
USE_MOCK_APIS=true

# Then run as normal
python -m src.main run "Nike"
```

## Testing

Run with mock data first to verify the pipeline works:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_research_bot.py -v

# Run with coverage
pytest --cov=src --cov-report=html
```

### Testing Individual Components

```python
# Test Research Bot
from src.bots.research import ResearchBot

bot = ResearchBot()
dossier, raw_research, artifacts = await bot.research("Nike")
print(dossier.strategic_tensions)
# artifacts contains full traceability (None for mock mode)
```

```python
# Test Creative Bot (in code)
from src.bots.creative import CreativeBot
from src.orchestrator.strategize import assign_tensions_to_slots

briefs = assign_tensions_to_slots(dossier)
creative = CreativeBot()
concepts = await creative.generate_concepts(dossier, briefs, additional_context="")
print([c.title for c in concepts])
```

```bash
# Test Creative Bot (script, uses latest research run)
python scripts/test_creative.py "Musti & Mirri"
```

```python
# Test AD Bot (treatments-first pipeline)
from src.bots.ad import ADBot
from pathlib import Path

ad = ADBot()
specs = await ad.generate_onepagers(dossier, concepts, Path("./output"), additional_context="")
```

## Project Structure

```
konseptikeiju/
├── src/
│   ├── core/           # Models, config, utilities
│   ├── orchestrator/   # Pipeline coordination
│   ├── bots/           # AI agents (research, creative, ad)
│   └── integrations/   # API clients
├── prompts/            # All AI prompts (version-controlled)
├── schemas/            # JSON validation schemas
├── web/                # Web interface
├── tests/              # Test suite
├── archive/            # Cached research (gitignored)
├── runs/               # Run artifacts (gitignored)
└── devlog/             # Development documentation
```

## Configuration

Key settings in `.env`:

```bash
# Required API keys
GEMINI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
NANOBANANA_API_KEY=your_key  # Optional name alias for Gemini Image

# Model selection (tested working configurations)
GEMINI_MODEL=gemini-3-pro-preview
GEMINI_IMAGE_MODEL=gemini-3-pro-image-preview
CLAUDE_MODEL=claude-opus-4-5-20251101

# Access control
ACCESS_CODE=your_secret_code

# Delivery (GitHub Pages)
DELIVERY_BASE_URL=https://yourusername.github.io/your-repo/deliveries
DELIVERY_PAGES_DIR=docs/deliveries

# GitHub publish (optional, for Render)
GITHUB_TOKEN=your_token
GITHUB_REPO=yourusername/your-repo
GITHUB_BRANCH=main
GIT_USER_NAME=your_name
GIT_USER_EMAIL=you@example.com

# Development
USE_MOCK_APIS=true  # Use mock responses (no API calls)
LOG_LEVEL=DEBUG     # DEBUG, INFO, WARNING, ERROR
```

> ⚠️ **Model Note:** `gemini-3-flash-preview` returns empty responses with Search Grounding. Prefer `gemini-3-pro-preview` for research.

> 🖼️ **Image Note:** One-pagers use `gemini-3-pro-image-preview` and rely on the prompt for A4 vertical sizing (no in-memory resize).

> 📦 **Delivery Note:** Use a dedicated deliveries repo (e.g. `KEIJUKAMAT`) and set `DELIVERY_BASE_URL` to its GitHub Pages URL. If running on Render, enable GitHub auto-publish with the `GITHUB_*` and `GIT_USER_*` settings above.
>
> 🔁 **Incremental Publish Note:** When GitHub publishing is configured, deliveries are pushed after each major phase so results appear progressively.
>
> 🔒 **Run Lock Note:** When a run is active, new forge requests are rejected with HTTP 409 to prevent overlapping runs on Render.
>
> ✅ **GitHub Publish Note:** Push uses `HEAD:main` (safe when Render runs in detached HEAD) and includes untracked delivery files.
> 🔄 **GitHub Sync Note:** Render now fetches + rebases before pushing to avoid "fetch first" errors.
>
> 🧪 **System Test Note:** Use the UI "Testaa toiminta" button to write a test file to `docs/deliveries/_tests/`, push to GitHub, and send a test email. Logs include SMTP config details.
>
> 📧 **Email Note:** Render free tier blocks SMTP ports; use SendGrid (HTTP API) for Gmail sender verification or Resend for domain senders. If using SMTP locally, ensure `SMTP_USER`/`SMTP_PASSWORD` have no hidden whitespace.
>
> ✉️ **SendGrid Note:** Set `SENDGRID_API_KEY` and `SENDGRID_FROM_EMAIL` (verified sender) to enable SendGrid on Render.
>
> ✉️ **Resend Note:** Set `RESEND_API_KEY` and `RESEND_FROM_EMAIL` to enable Resend on Render (requires domain verification).

> 🌐 **Hosting Note:** The UI is hosted on GitHub Pages, while the backend runs on Render (or another backend host). Set the API base URL in `web/config.js`:
> `window.KONSEPTIKEIJU_API_BASE = "https://your-backend-host";`

> 📊 **Status Note:** The status page streams recent logs via `/api/logs/{run_id}` and includes diagnostics + raw JSONL logs.

> 🧪 **One-pager Note:** The pipeline now prefers treatment-based prompts (Puuilo-style) for richer infographic layouts including the MITÄ/MITEN/MIKSI block.

## Research Analysis Pipeline

The Research Bot uses a multi-stage analysis pipeline with full traceability, **in Finnish**:

```
1. Company Input + Context
       ↓
2. Gemini Deep Research with Search Grounding (~1-2 min)
       ↓
3. Prompt + Raw Research saved IMMEDIATELY:
   runs/{company_name}/{company}_Research_PROMPT_YYYYMMDD_HHMMSS.md
   runs/{company_name}/{company}_Research_YYYYMMDD_HHMMSS.md
4. Lisähuomiot (jos annettu) tallennetaan run-kansioon:
   runs/{date}_{company}_{run_id}/additional_context.md
       ↓
4. Section Extraction (in memory)
       ↓
5. Diagnostic Framework Analysis (in memory)
       ↓
6. Structured Dossier (in memory)
```

**Robustness Features:**
- **Immediate saving**: Prompt + raw research saved instantly
- **Retry on 503**: Exponential backoff (10s → 160s) for "model overloaded" errors
- **JSON repair**: Automatic fixing of common JSON issues + AI-powered repair as fallback
- **Fallback dossier**: Minimal valid structure created if all parsing fails

Note: The Researcher phase now saves **only** the prompt and raw research output to the company folder (no subfolders).

**Sources note:** When using Search Grounding, Gemini may return citations/sources in metadata rather than inside the plain text. We automatically append them to the end of the raw report under `## Lähteet (Search Grounding)` when available.

## Prompt Engineering

All prompts are in the `prompts/` directory as markdown files. To refine:

1. Edit the relevant prompt file
2. Run with a test company
3. Evaluate output quality
4. Iterate

Key prompts to tune:
- `prompts/research/diagnostic_framework.md` - How tensions are identified
- `prompts/creative/system.md` - Creative philosophy
- `prompts/creative/concept_format.md` - Output structure
- `prompts/creative/treatment_generation.md` - Treatment structure (FI)
- `prompts/ad/prompt_builder.md` - Image generation

## Pipeline Phases

```
INPUT → VALIDATE → CHECK_ARCHIVE → [RESEARCH] → STRATEGIZE → 
CREATE → VISUALIZE → COMPOSE_PITCH → PACKAGE → DELIVER → DONE
```

Each phase has quality gates that must pass before proceeding.

## Quality Gates

| Transition | Requirements |
|------------|--------------|
| RESEARCH → STRATEGIZE | 3+ tensions, 1+ opportunity, 5+ sources |
| STRATEGIZE → CREATE | 3 briefs, different tensions, risk spread |
| CREATE → VISUALIZE | 3 concepts, 6 episodes each, platform diversity |
| VISUALIZE → COMPOSE | 3 PNG files, each >100KB |
| COMPOSE → PACKAGE | Email with hypothesis, all concepts mentioned |

## Output Files

After a successful run:

```
runs/{date}_{company}_{run_id}/
├── run_state.json          # Full state for debugging
├── logs.jsonl              # Detailed execution log
└── artifacts/
    ├── research/
    │   ├── research_raw.md         # Original Deep Research output
    │   ├── research_sections.json  # Parsed sections for analysis
    │   ├── research_analysis.md    # Diagnostic framework analysis
    │   ├── strategic_dossier.json  # Final structured dossier
    │   ├── strategic_dossier.md    # Human-readable version
    │   ├── research_metadata.json  # Timing, model info, traceability
    │   └── prompts_used.md         # All prompts (for debugging)
    ├── concepts/
    │   ├── concepts.json
    │   ├── concept_briefs.json
    │   ├── concept_01.md
    │   ├── concept_02.md
    │   ├── concept_03.md
    │   └── concept_summary.md
    ├── onepagers/
    │   ├── concept_01.png        # Generated during visualize; removed after delivery
    │   ├── concept_02.png
    │   ├── concept_03.png
    │   └── prompts.md
    └── delivery/
        ├── pitch_email.md
        └── package_index.md
```

**Delivery site (GitHub Pages-ready):**

```
docs/deliveries/{company_slug}/{run_id}/
├── research/
├── treatments/
├── onepagers/
└── delivery/
```

**Researcher outputs (saved separately):**

```
runs/{company_name}/
├── {company}_Research_PROMPT_YYYYMMDD_HHMMSS.md
└── {company}_Research_YYYYMMDD_HHMMSS.md
```

**Creative treatments (saved separately):**

```
runs/{company_name}/TREATMENTS/
├── {company}_TREATMENT_01_YYYYMMDD_HHMMSS.md
├── {company}_TREATMENT_02_YYYYMMDD_HHMMSS.md
└── {company}_TREATMENT_03_YYYYMMDD_HHMMSS.md
```


## Development Roadmap

- [x] Phase 1: Foundation (skeleton with mocks)
- [x] Phase 2: Research Bot (Gemini Deep Research integration) ✅ **TESTED**
  - [x] Deep Research with `google-genai` SDK + Search Grounding
  - [x] Research synthesis pipeline with full artifact traceability
  - [x] **First successful real research: Puuilo (15,564 chars)**
  - [x] Robust error handling (retry on 503, JSON fixing, fallbacks)
  - [x] Prompt logging system with auto-cleanup
- [ ] Phase 3: Creative Bot (real Claude integration)
- [ ] Phase 4: AD Bot (real image generation)
- [ ] Phase 5: Integration & Polish

## Contributing

1. Check `devlog/DEVLOG.md` for current status
2. Run tests before making changes
3. Update prompts thoughtfully (they're code)
4. Document any new patterns

## License

MIT

---

Built for creators who pitch brands. 🎬
