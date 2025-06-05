#!/usr/bin/env python3
"""
PvZ Wiki Scraper
Scrapes content from PvZ Fandom wiki and creates clean, offline-accessible HTML
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import argparse
import time
import urllib.parse
import json
import yaml


# Import our modules
from utils.content_processor import ContentProcessor
from utils.image_downloader import ImageDownloader
from config import settings


def load_content_types():
    """Load content types from YAML file"""
    try:
        with open("plants.yaml", "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return data.get("content_types", {})
    except FileNotFoundError:
        print("Warning: plants.yaml not found, using fallback data")
        return {"plants": []}
    except yaml.YAMLError as e:
        print(f"Error parsing plants.yaml: {e}")
        return {"plants": []}


class PvZWikiScraper:
    """Main scraper class for PvZ Wiki content"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.USER_AGENT})
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Initialize metadata file path
        self.metadata_file = self.output_dir / "plant_metadata.json"
        self.plant_metadata = self._load_plant_metadata()

        self.content_processor = ContentProcessor()
        self.image_downloader = ImageDownloader(
            self.session, self.output_dir, "https://pvz.fandom.com"
        )
        self.template = self._load_template()

    def _load_plant_metadata(self):
        """Load existing plant metadata or create empty dict"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                print("Warning: Could not load plant metadata, starting fresh")
        return {}

    def _save_plant_metadata(self):
        """Save plant metadata to file"""
        try:
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump(self.plant_metadata, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Warning: Could not save plant metadata: {e}")

    def _extract_plant_metadata(self, title, main_content_html, sidebar_content_html):
        """Extract plant metadata from processed content"""
        metadata = {
            "name": title,
            "image": None,
            "last_updated": time.strftime("%Y-%m-%d %H:%M:%S UTC"),
        }

        # Extract main plant image from sidebar
        if sidebar_content_html:
            soup = BeautifulSoup(sidebar_content_html, "html.parser")
            plant_image = soup.find("img", class_="plant-image")
            if plant_image and plant_image.get("src"):
                image_src = plant_image["src"]
                # Remove './' prefix if present
                if image_src.startswith("./"):
                    image_src = image_src[2:]
                metadata["image"] = image_src

        return metadata

    def _load_template(self):
        """Load HTML template from file"""
        template_path = Path(settings.TEMPLATE_FILE)
        try:
            with open(template_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(
                f"Template file not found: {template_path}. "
                "Please ensure the templates directory exists."
            )

    def fetch_page(self, url):
        """Fetch the HTML content from the given URL"""
        print(f"Fetching: {url}")
        try:
            response = self.session.get(url, timeout=settings.REQUEST_TIMEOUT)
            response.raise_for_status()
            response.encoding = "utf-8"
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def parse_content(self, html):
        """Parse HTML and extract main article content"""
        soup = BeautifulSoup(html, "lxml")

        # Try different selectors for main content
        for selector in settings.MAIN_CONTENT_SELECTORS:
            main_content = soup.find("div", selector)
            if main_content:
                return main_content

        print("Warning: Could not find main content area")
        return None

    def extract_title(self, html):
        """Extract page title"""
        soup = BeautifulSoup(html, "lxml")

        # Try different title selectors
        for selector in settings.TITLE_SELECTORS:
            if isinstance(selector, dict):
                title_tag = soup.find("h1", selector)
            else:
                title_tag = soup.find(selector)

            if title_tag:
                return title_tag.get_text().strip()

        return "PvZ Wiki Page"

    def create_clean_html(self, title, main_content, sidebar_content=""):
        """Create final HTML using template"""
        return self.template.format(
            title=title, main_content=main_content, sidebar_content=sidebar_content
        )

    def generate_filename(self, title, custom_filename=None, content_type=None):
        """Generate safe filename from title"""
        if custom_filename:
            return custom_filename

        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        max_len = settings.MAX_FILENAME_LENGTH
        safe_title = safe_title.replace(" ", "_")[:max_len]

        return f"{safe_title}.html"

    def generate_filename_from_url(self, url, content_type=None):
        """Generate filename from URL for bulk downloads"""
        # Extract the wiki page name from URL
        parsed = urllib.parse.urlparse(url)
        page_name = parsed.path.split("/")[-1]
        # URL decode the page name
        page_name = urllib.parse.unquote(page_name)

        # Create safe filename
        allowed_chars = (" ", "-", "_", "「", "」")
        safe_name = "".join(
            c for c in page_name if c.isalnum() or c in allowed_chars
        ).strip()

        return f"{safe_name}.html"

    def scrape_page(self, url, output_filename=None, content_type=None):
        """Main scraping function"""
        # Fetch the page
        html = self.fetch_page(url)
        if not html:
            return False

        # Extract title
        title = self.extract_title(html)

        # Extract main content
        main_content = self.parse_content(html)
        if not main_content:
            print("Failed to extract main content")
            return False

        # Clean and process content
        main_content_html, sidebar_content_html = self.content_processor.clean_content(
            main_content
        )
        if not main_content_html:
            print("Failed to clean content")
            return False

        # Download and process images
        print("Processing images...")
        main_content_html = self.image_downloader.process_images_in_html(
            main_content_html, url
        )
        if sidebar_content_html:
            sidebar_content_html = self.image_downloader.process_images_in_html(
                sidebar_content_html, url
            )

        # Show download stats
        stats = self.image_downloader.get_download_stats()
        if stats["total_downloaded"] > 0:
            print(
                f"📸 Downloaded {stats['total_downloaded']} images to: {stats['images_dir']}"
            )

        # Generate filename and output path first
        if output_filename:
            filename = output_filename
        elif content_type:
            filename = self.generate_filename_from_url(url, content_type)
        else:
            filename = self.generate_filename(title)

        output_path = self.output_dir / filename

        # Ensure directory exists for organized content
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create final HTML with consistent relative paths
        final_html = self.create_clean_html(
            title, main_content_html, sidebar_content_html
        )

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_html)
            print(f"✅ Saved: {output_path}")

            # Extract and save plant metadata
            metadata = self._extract_plant_metadata(
                title, main_content_html, sidebar_content_html
            )
            self.plant_metadata[title] = metadata
            self._save_plant_metadata()

            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False

    def get_content_urls(self, content_type):
        """Get URLs for a specific content type"""
        content_types = load_content_types()
        return content_types.get(content_type, [])

    def scrape_bulk(self, content_type="plants", resume=False, delay=1.5):
        """Bulk download pages for a specific content type"""
        urls = self.get_content_urls(content_type)
        if not urls:
            print(f"❌ No URLs found for content type: {content_type}")
            return False

        total = len(urls)
        success_count = 0
        skipped_count = 0
        failed_count = 0

        print(f"🚀 Starting bulk download: {total} {content_type} pages")
        print(f"📁 Output directory: {self.output_dir / content_type}")

        for i, url in enumerate(urls, 1):
            # Generate expected filename
            expected_filename = self.generate_filename_from_url(url, content_type)
            expected_path = self.output_dir / expected_filename

            # Skip if file exists and resume mode is enabled
            if resume and expected_path.exists():
                print(f"[{i}/{total}] ⏭️  Skipping: {expected_path.name}")
                skipped_count += 1
                continue

            print(f"\n[{i}/{total}] 📄 Processing: {url}")

            # Scrape the page
            success = self.scrape_page(url, content_type=content_type)

            if success:
                success_count += 1
                print(f"[{i}/{total}] ✅ Completed: {expected_path.name}")
            else:
                failed_count += 1
                print(f"[{i}/{total}] ❌ Failed: {url}")

            # Rate limiting - be respectful to the server
            if i < total:  # Don't delay after the last item
                print(f"⏱️  Waiting {delay}s...")
                time.sleep(delay)

        # Summary report
        print("\n📊 Bulk download complete!")
        print(f"✅ Successful: {success_count}")
        if skipped_count > 0:
            print(f"⏭️  Skipped: {skipped_count}")
        if failed_count > 0:
            print(f"❌ Failed: {failed_count}")
        print(f"📁 Files saved to: {self.output_dir / content_type}")

        return failed_count == 0


def create_argument_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        description="PvZ Wiki Scraper - Download wiki pages",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single page download
  python scraper.py "https://pvz.fandom.com/zh/wiki/豌豆射手"
  python scraper.py "https://pvz.fandom.com/zh/wiki/豌豆射手" custom_name.html

  # Bulk downloads
  python scraper.py --all                    # Download all plants
  python scraper.py --plants                 # Download plants explicitly
  python scraper.py --all --resume           # Skip existing files
  python scraper.py --plants --delay 2       # Custom delay between requests
        """,
    )

    # Single page mode (positional arguments)
    parser.add_argument(
        "url", nargs="?", help="Wiki URL to scrape (for single page mode)"
    )
    parser.add_argument(
        "output_filename", nargs="?", help="Custom output filename (optional)"
    )

    # Bulk download modes
    parser.add_argument(
        "--all", action="store_true", help="Download all content (currently: plants)"
    )
    parser.add_argument(
        "--plants", action="store_true", help="Download all plant pages"
    )

    # Bulk download options
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Skip files that already exist (for bulk downloads)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=0.1,
        help="Delay between requests in seconds (default: 0.1)",
    )

    return parser


def main():
    """Main function to run the scraper"""
    parser = create_argument_parser()

    # Handle legacy usage (no arguments)
    if len(sys.argv) == 1:
        parser.print_help()
        return

    # Check for legacy positional arguments (backward compatibility)
    if len(sys.argv) >= 2 and not sys.argv[1].startswith("--"):
        # Legacy mode: python scraper.py <url> [filename]
        url = sys.argv[1]
        output_filename = sys.argv[2] if len(sys.argv) > 2 else None

        scraper = PvZWikiScraper()
        print(f"Starting scrape of: {url}")
        success = scraper.scrape_page(url, output_filename)

        if success:
            print("✅ Scraping completed successfully!")
        else:
            print("❌ Scraping failed!")
        return

    # Parse modern command line arguments
    args = parser.parse_args()
    scraper = PvZWikiScraper()

    # Determine mode and execute
    if args.all or args.plants:
        # Bulk download mode
        content_type = "plants"  # For now, --all defaults to plants
        print("🔄 Bulk download mode: " + content_type)
        success = scraper.scrape_bulk(
            content_type=content_type, resume=args.resume, delay=args.delay
        )

        if success:
            print("✅ Bulk scraping completed successfully!")
        else:
            print("⚠️  Bulk scraping completed with some failures!")

    elif args.url:
        # Single page mode
        print(f"Starting scrape of: {args.url}")
        success = scraper.scrape_page(args.url, args.output_filename)

        if success:
            print("✅ Scraping completed successfully!")
        else:
            print("❌ Scraping failed!")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
