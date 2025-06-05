#!/usr/bin/env python3
"""
Main entry point for PvZ Wiki Scraper
"""

import sys
from scraper import main as scraper_main
from generate_index import generate_combined_index_html


def main():
    """Run the PvZ Wiki scraper and generate index pages"""
    print("🌱 Starting PvZ Wiki Scraper...")

    # Set sys.argv to run scraper with --all flag
    original_argv = sys.argv
    sys.argv = ["scraper.py", "--all"]

    try:
        # Run the scraper
        scraper_main()
        print("✅ Scraping completed!")

        # Generate combined index page
        print("📄 Generating index page...")
        generate_combined_index_html("docs", "docs/index.html")
        print("✅ Index page generated!")

        print("🎉 Complete! Check docs/index.html to view the results")

    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    main()
