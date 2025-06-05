#!/usr/bin/env python3
"""
PvZ Wiki Scraper
Scrapes content from PvZ Fandom wiki and creates clean, offline-accessible HTML
"""

import requests
from bs4 import BeautifulSoup
from pathlib import Path
import sys
import shutil

# Import our modules
from utils.content_processor import ContentProcessor
from utils.image_downloader import ImageDownloader
from config import settings


class PvZWikiScraper:
    """Main scraper class for PvZ Wiki content"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": settings.USER_AGENT})
        self.output_dir = Path(settings.OUTPUT_DIR)
        self.output_dir.mkdir(exist_ok=True)
        self.content_processor = ContentProcessor()
        self.image_downloader = ImageDownloader(
            self.session, self.output_dir, "https://pvz.fandom.com"
        )

        # Ensure styles are copied to output directory
        self._ensure_styles_copied()

        # Load template
        self.template = self._load_template()

    def _ensure_styles_copied(self):
        """Ensure styles directory is copied to output for proper CSS loading"""
        styles_source = Path("styles")
        styles_dest = self.output_dir / "styles"

        if styles_source.exists():
            if styles_dest.exists():
                # Remove existing styles and copy fresh ones
                shutil.rmtree(styles_dest)
            shutil.copytree(styles_source, styles_dest)
            print(f"📎 Copied styles to: {styles_dest}")

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

    def generate_filename(self, title, custom_filename=None):
        """Generate safe filename from title"""
        if custom_filename:
            return custom_filename

        safe_title = "".join(
            c for c in title if c.isalnum() or c in (" ", "-", "_")
        ).strip()
        safe_title = safe_title.replace(" ", "_")[: settings.MAX_FILENAME_LENGTH]
        return f"{safe_title}.html"

    def scrape_page(self, url, output_filename=None):
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

        # Create final HTML
        final_html = self.create_clean_html(
            title, main_content_html, sidebar_content_html
        )

        # Generate filename and save
        output_filename = self.generate_filename(title, output_filename)
        output_path = self.output_dir / output_filename

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(final_html)
            print(f"✅ Saved: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving file: {e}")
            return False


def main():
    """Main function to run the scraper"""
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <wiki_url> [output_filename]")
        print(
            "Example: python scraper.py "
            "'https://pvz.fandom.com/zh/wiki/%E8%B1%8C%E8%B1%86%E5%B0%84%E6%89%8B'"
        )
        return

    url = sys.argv[1]
    output_filename = sys.argv[2] if len(sys.argv) > 2 else None

    scraper = PvZWikiScraper()

    print(f"Starting scrape of: {url}")
    success = scraper.scrape_page(url, output_filename)

    if success:
        print("✅ Scraping completed successfully!")
    else:
        print("❌ Scraping failed!")


if __name__ == "__main__":
    main()
