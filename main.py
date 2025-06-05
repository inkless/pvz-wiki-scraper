#!/usr/bin/env python3
"""
Main entry point for PvZ Wiki Scraper
"""

import sys
from scraper import main as scraper_main
from generate_index import get_content_list_with_images, generate_index_html


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

        # Generate plants index page
        print("📄 Generating plants index page...")
        plants = get_content_list_with_images("docs", "plants")
        generate_index_html(plants, "docs/plants.html")
        print("✅ Plants index page generated!")

        # Generate zombies index page
        print("📄 Generating zombies index page...")
        zombies = get_content_list_with_images("docs", "zombies")
        generate_index_html(zombies, "docs/zombies.html")
        print("✅ Zombies index page generated!")

        # Generate combined index page (default for backwards compatibility)
        print("📄 Generating combined index page...")
        all_content = plants + zombies
        generate_index_html(all_content, "docs/index.html")
        print("✅ Combined index page generated!")

        print(
            f"🎉 Complete! Generated {len(plants)} plant pages + "
            f"{len(zombies)} zombie pages + 3 index pages"
        )

    finally:
        # Restore original argv
        sys.argv = original_argv


if __name__ == "__main__":
    main()
