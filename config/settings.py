"""
Configuration settings for PvZ Wiki Scraper
"""

# Request settings
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
REQUEST_TIMEOUT = 10

# Output settings
OUTPUT_DIR = "docs"
MAX_FILENAME_LENGTH = 100

# Template files
TEMPLATE_FILE = "templates/template.html"
CSS_FILE = "styles/style.css"

# Content selectors
MAIN_CONTENT_SELECTORS = [{"id": "mw-content-text"}, {"class": "mw-parser-output"}]

TITLE_SELECTORS = [{"class": "mw-page-title-main"}, {"id": "firstHeading"}, "h1"]

# Unwanted content selectors
UNWANTED_SELECTORS = [
    # Ads and promotional content
    ".fandom-community-header",
    ".global-navigation",
    ".page-header",
    ".rail-module",
    ".wikia-ad",
    ".ad-slot",
    # Comments and edit sections
    ".mw-editsection",
    ".comments",
    ".article-comments",
    # Other clutter
    ".stub",
    ".ambox",
    ".mbox",
    # Other filters
    ".pi-title-image",
    ".navbox-div .navbar ul",
]

# Sidebar content selectors
SIDEBAR_SELECTORS = [".pi-item", ".pi-panel", ".portable-infobox"]
