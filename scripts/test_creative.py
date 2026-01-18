"""
Standalone test for the Creative Bot using an existing research dossier.

Usage:
  python scripts/test_creative.py "Musti & Mirri"
"""

import asyncio
import json
from pathlib import Path
import sys
from datetime import datetime, UTC

from src.bots.creative import CreativeBot
from src.bots.research.synthesizer import ResearchSynthesizer
from src.core.filesystem import company_folder_name, slugify
from src.core.logger import get_logger
from src.core.models import StrategicDossier
from src.orchestrator.strategize import assign_tensions_to_slots
from src.core.config import settings

logger = get_logger(__name__)


def _find_latest_run_dir(company_slug: str) -> Path:
    runs_dir = settings.get_runs_path()
    candidates = sorted(runs_dir.glob(f"test_{company_slug}_*"))
    if not candidates:
        raise FileNotFoundError(
            f"No test run found for slug '{company_slug}' under {runs_dir}"
        )
    return candidates[-1]


def _load_dossier_from_run(run_dir: Path) -> StrategicDossier | None:
    dossier_path = run_dir / "artifacts" / "research" / "strategic_dossier.json"
    if not dossier_path.exists():
        return None
    with open(dossier_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return StrategicDossier.model_validate(data)


def _find_latest_raw_research(company_folder: str) -> Path:
    company_dir = settings.get_runs_path() / company_folder
    candidates = sorted(company_dir.glob(f"{company_folder}_Research_*.md"))
    if not candidates:
        raise FileNotFoundError(f"No raw research found under {company_dir}")
    return candidates[-1]


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_creative.py \"Company Name\"")
        sys.exit(1)

    company_name = sys.argv[1]
    company_slug = slugify(company_name)
    run_dir = _find_latest_run_dir(company_slug)
    dossier = _load_dossier_from_run(run_dir)
    if dossier is None:
        company_folder = company_folder_name(company_name)
        raw_path = _find_latest_raw_research(company_folder)
        raw_research = raw_path.read_text(encoding="utf-8")
        logger.info("Synthesizing dossier from raw research", raw_path=str(raw_path))
        synthesizer = ResearchSynthesizer(company_name)
        dossier, _ = await synthesizer.synthesize(
            raw_research=raw_research,
            research_started_at=datetime.now(UTC),
            run_dir=None,
        )

    logger.info("Loaded dossier", company=dossier.company_name, run_dir=str(run_dir))

    briefs = assign_tensions_to_slots(dossier)
    creative = CreativeBot()

    concepts = await creative.generate_concepts(dossier, briefs, additional_context="")
    treatments = await creative.generate_treatments(dossier, briefs, additional_context="")

    # Save treatments to company folder
    company_folder = company_folder_name(dossier.company_name)
    treatments_dir = settings.get_runs_path() / company_folder / "TREATMENTS"
    treatments_dir.mkdir(parents=True, exist_ok=True)
    safe_stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    for item in treatments:
        slot_id = item.get("slot_id", "00")
        filename = f"{company_folder}_TREATMENT_{slot_id}_{safe_stamp}.md"
        (treatments_dir / filename).write_text(item.get("content", ""), encoding="utf-8")

    print("✅ CREATIVE COMPLETE")
    print(f"Company: {dossier.company_name}")
    print(f"Run source: {run_dir}")
    print(f"Treatments saved to: {treatments_dir}")
    for concept in concepts:
        print(f"- {concept.id}: {concept.title}")


if __name__ == "__main__":
    asyncio.run(main())
