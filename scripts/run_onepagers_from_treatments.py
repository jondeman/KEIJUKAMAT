"""
Generate One-Pagers from existing treatments using Gemini Image model.

Usage:
  PYTHONPATH=. ./venv/bin/python scripts/run_onepagers_from_treatments.py "Company Name"
  PYTHONPATH=. ./venv/bin/python scripts/run_onepagers_from_treatments.py "Company Name" path/to/treatment.md [more...]

This script:
1. If treatment file paths are provided, uses them directly
2. Otherwise finds existing treatments in runs/{company}/TREATMENTS/ and uses the latest set
3. Generates one-pagers using ADBot with Gemini Image model
4. Saves one-pagers to runs/{company}/ONEPAGERS/
"""

import asyncio
import sys
from pathlib import Path

from src.bots.ad import ADBot
from src.core.config import settings
from src.core.filesystem import company_folder_name
from src.core.logger import get_logger

logger = get_logger(__name__)


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_onepagers_from_treatments.py \"Company Name\" [treatment_paths...]")
        sys.exit(1)

    company_name = sys.argv[1]
    provided_paths = [Path(p) for p in sys.argv[2:]] if len(sys.argv) > 2 else []
    company_folder = company_folder_name(company_name)
    treatments_dir = settings.get_runs_path() / company_folder / "TREATMENTS"

    if not treatments_dir.exists() and not provided_paths:
        print(f"❌ Treatments directory not found: {treatments_dir}")
        sys.exit(1)

    def _extract_title(content: str) -> str:
        for line in content.splitlines():
            if line.strip().startswith("# "):
                return line.strip().lstrip("# ").strip()
        return "Konsepti"

    def _infer_slot_id(path: Path) -> str:
        parts = path.stem.split("_")
        if "TREATMENT" in parts:
            try:
                idx = parts.index("TREATMENT")
                candidate = parts[idx + 1]
                if candidate.isdigit():
                    return candidate.zfill(2)
            except Exception:
                pass
        return "00"

    treatments = []
    if provided_paths:
        for p in provided_paths:
            if not p.exists():
                print(f"❌ Treatment file not found: {p}")
                sys.exit(1)
            content = p.read_text(encoding="utf-8")
            title = _extract_title(content)
            slot_id = _infer_slot_id(p)
            treatments.append({"slot_id": slot_id, "title": title, "content": content})
            print(f"📄 Loaded treatment {slot_id}: {title}")
    else:
        # Find latest treatments (by timestamp in filename)
        treatment_files = sorted(treatments_dir.glob(f"{company_folder}_TREATMENT_*.md"), reverse=True)

        if not treatment_files:
            print(f"❌ No treatment files found in {treatments_dir}")
            sys.exit(1)

        # Group by timestamp to get the latest set
        timestamps = set()
        for f in treatment_files:
            parts = f.stem.split("_")
            if len(parts) >= 4:
                timestamp = "_".join(parts[-2:])  # YYYYMMDD_HHMMSS
                timestamps.add(timestamp)

        latest_timestamp = sorted(timestamps, reverse=True)[0] if timestamps else None

        if not latest_timestamp:
            print("❌ Could not parse timestamps from treatment files")
            sys.exit(1)

        # Load treatments with latest timestamp
        for slot_id in ["01", "02", "03"]:
            pattern = f"{company_folder}_TREATMENT_{slot_id}_{latest_timestamp}.md"
            matches = list(treatments_dir.glob(pattern))
            if matches:
                content = matches[0].read_text(encoding="utf-8")
                title = _extract_title(content)
                treatments.append({
                    "slot_id": slot_id,
                    "title": title,
                    "content": content,
                })
                print(f"📄 Loaded treatment {slot_id}: {title}")

        if len(treatments) < 3:
            print(f"⚠️ Only found {len(treatments)} treatments (expected 3)")

    print(f"\n🖼️ Generating {len(treatments)} one-pagers for {company_name}...")
    print(f"Using model: {settings.gemini_image_model}")

    ad_bot = ADBot()
    results = await ad_bot.generate_onepagers_from_treatments(
        company_name=company_name,
        treatments=treatments,
        additional_context="",
    )

    print("\n✅ One-pagers generated:")
    for r in results:
        if hasattr(r, "concept_id"):
            slot = r.concept_id.split("_")[-1]
            print(f"  - {slot}: {r.content.headline}")
            print(f"    → {r.output_path}")
        else:
            print(f"  - {r['slot_id']}: {r['title']}")
            print(f"    → {r['image_path']}")

    output_dir = settings.get_runs_path() / company_folder / "ONEPAGERS"
    print(f"\nOutput directory: {output_dir}")
    print(f"Prompts saved to: {output_dir / 'PROMPTS'}")


if __name__ == "__main__":
    asyncio.run(main())
