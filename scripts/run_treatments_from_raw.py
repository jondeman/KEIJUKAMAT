"""
Generate 3 Creative treatments using ONLY an existing raw research markdown file.

This script does NOT run Gemini or any new research. It only uses the provided input file
and calls Claude (CreativeBot) to produce treatments.

Usage:
  PYTHONPATH=. ./venv/bin/python scripts/run_treatments_from_raw.py \
    "Musti & Mirri" \
    "runs/musti__mirri/musti__mirri_Research_20260116_164534.md"
"""

import asyncio
from datetime import datetime, UTC
from pathlib import Path
import sys

from src.bots.creative import CreativeBot
from src.core.config import settings
from src.core.filesystem import company_folder_name
from src.core.logger import RunLogger, get_logger

logger = get_logger(__name__)


async def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: python scripts/run_treatments_from_raw.py \"Company\" \"path/to/research.md\""
        )
        sys.exit(1)

    company_name = sys.argv[1]
    raw_path = Path(sys.argv[2])
    if not raw_path.is_absolute():
        raw_path = settings.project_root / raw_path

    company_folder = company_folder_name(company_name)
    company_dir = settings.get_runs_path() / company_folder
    company_dir.mkdir(parents=True, exist_ok=True)

    run_logger = RunLogger(company_dir / "agent_log.jsonl")
    run_logger.info(
        "Agent run started",
        company=company_name,
        company_dir=str(company_dir),
        input_path=str(raw_path),
        mode="treatments_from_raw",
    )

    raw_md = raw_path.read_text(encoding="utf-8")
    logger.info("Loaded raw research", path=str(raw_path), length=len(raw_md))
    run_logger.info("Loaded raw research", path=str(raw_path), length=len(raw_md))

    creative = CreativeBot()
    run_logger.info("Initialized CreativeBot", use_mock=creative.use_mock)
    treatments = await creative.generate_treatments_from_raw(company_name, raw_md, additional_context="")
    run_logger.info("Generated treatments", count=len(treatments))

    out_dir = company_dir / "TREATMENTS"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")

    for t in treatments:
        slot_id = t["slot_id"]
        filename = f"{company_folder}_TREATMENT_{slot_id}_{stamp}.md"
        (out_dir / filename).write_text(t["content"], encoding="utf-8")
        run_logger.artifact_created(
            artifact_type=f"treatment_{slot_id}",
            path=str(out_dir / filename),
        )

    print("✅ Treatments generated")
    print(f"Company: {company_name}")
    print(f"Input: {raw_path}")
    print(f"Output: {out_dir}")
    for t in treatments:
        print(f"- {t['slot_id']}: {t['title']}")
    run_logger.info("Agent run completed", output_dir=str(out_dir))


if __name__ == "__main__":
    asyncio.run(main())

