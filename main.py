#!/usr/bin/env python3
"""
Main entry point for PvZ Wiki Scraper
"""

import sys
from scraper import main as scraper_main
from generate_index import get_plant_list, generate_index_html


def main():
    """Run the PvZ Wiki scraper and generate index page"""
    print("🌱 Starting PvZ Wiki Scraper...")

    # Set sys.argv to run scraper with --all flag
    original_argv = sys.argv
    sys.argv = ["scraper.py", "--all"]

    try:
        # Run the scraper
        scraper_main()
        print("✅ Scraping completed!")

        # Generate index page
        print("📄 Generating index page...")
        plants = get_plant_list()
        generate_index_html(plants)
        print("✅ Index page generated!")

        print(f"🎉 Complete! Generated {len(plants)} plant pages + index page")

    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    main()
