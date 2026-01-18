#!/usr/bin/env python3
"""
Test script for the Research Bot.

Usage:
    python scripts/test_research.py "Company Name"
    python scripts/test_research.py "Puuilo"
    
This will:
1. Run the Research Bot on the specified company
2. Save all artifacts to a test run directory
3. Clean up old prompt logs (>14 days)
4. Display summary of results
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.bots.research import ResearchBot
from src.core.config import settings
from src.core.filesystem import slugify
from src.core.prompt_logger import cleanup_prompt_logs, get_prompt_logger


async def test_research(company_name: str) -> None:
    """Run research on a company and save results."""
    
    print("=" * 60)
    print(f"🔬 RESEARCH BOT TEST")
    print(f"Company: {company_name}")
    print(f"Mode: {'MOCK' if settings.use_mock_apis else 'REAL API'}")
    print("=" * 60)
    print()
    
    # Clean up old prompt logs first
    print("🧹 Cleaning up old prompt logs (>14 days)...")
    deleted = cleanup_prompt_logs(retention_days=14)
    if deleted > 0:
        print(f"   Deleted {deleted} old log directories")
    else:
        print("   No old logs to clean up")
    print()
    
    # Create test output directory
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    company_slug = slugify(company_name)
    test_dir = Path("runs") / f"test_{company_slug}_{timestamp}"
    test_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"📁 Output directory: {test_dir}")
    print()
    
    # Run research
    print("🚀 Starting Research Bot...")
    print("-" * 40)
    
    bot = ResearchBot()
    
    try:
        dossier, raw_research, artifacts = await bot.research(
            company_name=company_name,
            additional_context="Focus on their marketing and content strategy opportunities.",
            run_dir=test_dir,
        )
        
        print("-" * 40)
        print()
        
        # Display results summary
        print("✅ RESEARCH COMPLETE!")
        print()
        print("📊 DOSSIER SUMMARY:")
        print(f"   Company: {dossier.company_name}")
        print(f"   Slug: {dossier.company_slug}")
        print(f"   Strategic Tensions: {len(dossier.strategic_tensions)}")
        print(f"   Opportunity Zones: {len(dossier.opportunity_zones)}")
        print(f"   Sources: {len(dossier.sources)}")
        print()
        
        print("📌 STRATEGIC TENSIONS:")
        for i, tension in enumerate(dossier.strategic_tensions, 1):
            print(f"   {i}. [{tension.opportunity_type.value}] {tension.description[:80]}...")
            print(f"      Priority: {tension.priority_score}/5")
        print()
        
        print("🎯 OPPORTUNITY ZONES:")
        for zone in dossier.opportunity_zones:
            print(f"   - {zone.description[:80]}...")
            print(f"     Risk: {zone.risk_level.value}")
        print()
        
        if artifacts:
            print("📦 ARTIFACTS SAVED:")
            print(f"   Sections extracted: {len(artifacts.extracted_sections)}")
            print(f"   Prompts logged: {list(artifacts.prompts_used.keys())}")
        print()
        
        # Show prompt log stats
        prompt_logger = get_prompt_logger()
        stats = prompt_logger.get_stats()
        print("📝 PROMPT LOG STATS:")
        print(f"   Total files: {stats['total_files']}")
        print(f"   Total size: {stats['total_size_bytes'] / 1024:.1f} KB")
        for cat, cat_stats in stats['categories'].items():
            print(f"   {cat}: {cat_stats['files']} files")
        print()
        
        print(f"📁 All artifacts saved to: {test_dir}")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        company_name = "Puuilo"  # Default
        print(f"No company specified, using default: {company_name}")
    else:
        company_name = sys.argv[1]
    
    asyncio.run(test_research(company_name))


if __name__ == "__main__":
    main()
