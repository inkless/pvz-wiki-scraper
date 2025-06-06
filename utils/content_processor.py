"""
Content processing utilities for PvZ Wiki Scraper
"""

from bs4 import BeautifulSoup
from config import settings
from .chinese_translator import ChineseTranslator
import re


class ContentProcessor:
    """Handles cleaning and processing of scraped wiki content"""

    def __init__(self):
        """Initialize content processor with Chinese translator"""
        self.translator = ChineseTranslator()

    def clean_content(self, content_soup, content_type="plants"):
        """Remove unwanted elements and clean up the content"""
        if not content_soup:
            return None, None

        # Make a copy to avoid modifying the original
        cleaned = BeautifulSoup(str(content_soup), "lxml")

        # Remove unwanted elements (keep navbox and infoboxes)
        for selector in settings.UNWANTED_SELECTORS:
            for element in cleaned.select(selector):
                element.decompose()

        # Additional content filtering improvements
        self._apply_content_filters(cleaned)

        # Convert internal wiki links to local HTML files
        self._convert_wiki_links(cleaned)

        # Remove empty paragraphs and divs (but preserve divs with images)
        for tag in cleaned.find_all(["p", "div"]):
            if not tag.get_text(strip=True):
                # Don't remove divs that contain images, even if they have no text
                if tag.name == "div" and tag.find("img"):
                    continue
                tag.decompose()

        # Extract and process infobox data
        sidebar_content = self._create_enhanced_infobox(cleaned, content_type)

        # Remove processed infobox elements from main content
        for selector in settings.SIDEBAR_SELECTORS:
            for element in cleaned.select(selector):
                element.decompose()

        main_content = str(cleaned)

        # Convert traditional Chinese to simplified Chinese
        main_content = self.translator.convert_html(main_content)
        sidebar_content = self.translator.convert_html(sidebar_content)

        return main_content, sidebar_content

    def _apply_content_filters(self, soup):
        """Apply specific content filtering improvements"""

        # 1. Remove .hatnote sections (disambiguation notes)
        for hatnote in soup.find_all(class_="hatnote"):
            hatnote.decompose()

        # 2. Filter out "衍生内容" (Derivative Content) sections
        self._remove_section_by_title(soup, "衍生内容")

        # 3. Remove "图库" (Gallery) sections
        self._remove_section_by_title(soup, "图库")

        # 4. In "参见" (See Also) sections, remove .navbar div
        self._clean_see_also_section(soup)

        # 5. Remove SVG icons from figure captions
        self._remove_svg_icons(soup)

        # 6. Clean up TOC entries for removed sections
        self._clean_toc_entries(soup)

        # 7. Remove MediaWiki performance comments
        self._remove_mediawiki_comments(soup)

    def _sanitize_page_name_for_filename(self, page_name):
        """Sanitize page name to match the filename generation logic"""
        # Use the same character filtering as generate_filename_from_url
        allowed_chars = (" ", "-", "_", "「", "」")
        safe_name = "".join(
            c for c in page_name if c.isalnum() or c in allowed_chars
        ).strip()
        return safe_name

    def _process_wiki_link(self, link, page_name):
        """Process a wiki link by mapping page name to local href and adding wiki-link class"""
        import urllib.parse

        # URL decode the page name
        page_name = urllib.parse.unquote(page_name)

        # Special case: Convert "植物大战僵尸" links to index.html
        if page_name == "植物大战僵尸":
            local_href = "./index.html"
        # Special case: Redirect "橄榄球僵尸（在线试玩）" to "暗黑橄榄球僵尸"
        elif page_name == "橄榄球僵尸（在线试玩）":
            local_href = "./暗黑橄榄球僵尸.html"
        else:
            # Sanitize page name to match filename generation
            sanitized_name = self._sanitize_page_name_for_filename(page_name)
            # Convert to local HTML file
            local_href = f"./{sanitized_name}.html"

        link["href"] = local_href

        # Add a class to indicate it's a local wiki link
        existing_class = link.get("class", [])
        if isinstance(existing_class, str):
            existing_class = [existing_class]
        existing_class.append("wiki-link")
        link["class"] = existing_class

    def _convert_wiki_links(self, soup):
        """Convert internal wiki links to local HTML files"""
        import urllib.parse

        for link in soup.find_all("a"):
            href = link.get("href", "")

            # Check if it's an internal wiki link
            if href.startswith("/zh/wiki/") or href.startswith("/wiki/"):
                # Extract the page name from the URL
                page_name = href.split("/")[-1]
                self._process_wiki_link(link, page_name)

            elif "fandom.com" in href and "/wiki/" in href:
                # Handle full fandom URLs
                # Extract page name from full URL
                parsed = urllib.parse.urlparse(href)
                if parsed.path and "/wiki/" in parsed.path:
                    page_name = parsed.path.split("/")[-1]
                    self._process_wiki_link(link, page_name)

            # For external links, we can leave them as-is or mark them
            # so they open in new tabs when viewed locally

    def _remove_section_by_title(self, soup, section_title):
        """Remove entire sections by their heading title"""
        # Look for headings that contain the section title
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            if section_title in heading.get_text(strip=True):
                # Find all content until the next heading of same or higher level
                current_level = int(heading.name[1])  # Extract level number

                # Collect all elements to remove
                elements_to_remove = [heading]

                # Find all following siblings until next heading of same/higher level
                current = heading.next_sibling
                while current:
                    # Check if this is a heading of same or higher level
                    if (
                        hasattr(current, "name")
                        and current.name
                        and current.name.startswith("h")
                        and len(current.name) == 2
                        and int(current.name[1]) <= current_level
                    ):
                        break

                    # Add to removal list and move to next sibling
                    elements_to_remove.append(current)
                    current = current.next_sibling

                # Remove all collected elements
                for element in elements_to_remove:
                    if hasattr(element, "decompose"):
                        element.decompose()
                    elif hasattr(element, "extract"):
                        element.extract()

                break

    def _clean_see_also_section(self, soup):
        """Clean the 参见 (See Also) section by removing .navbar divs and first ul"""
        for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
            heading_text = heading.get_text(strip=True)
            if (
                "参见" in heading_text
                or "另见" in heading_text
                or "参考" in heading_text
            ):
                # Find the next content until the next heading
                current_level = int(heading.name[1])
                element = heading.next_sibling

                while element:
                    if (
                        element.name
                        and element.name.startswith("h")
                        and len(element.name) == 2
                        and int(element.name[1]) <= current_level
                    ):
                        break

                    # Remove .navbar divs in this section
                    if hasattr(element, "find_all"):
                        for navbar in element.find_all(class_="navbar"):
                            navbar.decompose()

                    element = element.next_sibling

    def _create_enhanced_infobox(self, soup, content_type="plants"):
        """Create enhanced infobox with tabs matching the screenshot design"""

        # Find portable infobox (the actual structure used by the wiki)
        infobox = soup.find("aside", class_=re.compile(r"portable-infobox"))

        # Fallback to older infobox patterns if portable infobox not found
        if not infobox:
            infobox = soup.find(["div", "table"], class_=re.compile(r"infobox|pi-item"))

        if not infobox:
            return ""

            # Extract data from existing infobox
        infobox_data = self._extract_infobox_data(infobox)

        # Extract title from portable infobox
        title_elem = infobox.find("h2", class_=re.compile(r"pi-title"))
        if not title_elem:
            # Try alternative title selectors
            title_elem = infobox.find(
                ["h1", "h2", "div"], class_=re.compile(r"pi-title|infobox-title")
            )

        if title_elem:
            title_text = title_elem.get_text(strip=True)
            # Clean up the title if it looks garbled
            if title_text and len(title_text) > 1 and not title_text.isspace():
                title = title_text
            else:
                # Extract from page URL or try to find page title elsewhere
                title = self._extract_page_title_fallback(soup)
        else:
            title = self._extract_page_title_fallback(soup)

        # Extract main image from portable infobox
        img_elem = infobox.find("img")
        if img_elem:
            src = img_elem.get("data-src") or img_elem.get("src", "")
            alt = title
            if src:
                image = f'<img src="{src}" alt="{alt}" class="plant-image">'
            else:
                image = ""
        else:
            image = ""

        # Add extracted info to infobox_data
        infobox_data["title"] = title
        infobox_data["image"] = image
        infobox_data["page_content"] = soup

        if not infobox_data:
            return ""

        # Create the enhanced infobox HTML
        gamedata_tab = self._create_gamedata_tab(infobox_data)
        names_tab = self._create_names_tab(infobox_data)

        # Determine header title based on content type
        header_title = "僵尸图鉴" if content_type == "zombies" else "植物图鉴"

        infobox_html = (
            """
        <div class="plant-infobox">
            <div class="infobox-header">
                <div class="header-title">"""
            + header_title
            + """</div>
                <div class="plant-name">"""
            + title
            + """</div>
            </div>
            <div class="plant-image-container">
                """
            + image
            + """
            </div>
            <div class="infobox-sections">
                <div class="info-section">
                    <div class="section-header">游戏数据</div>
                    <div class="section-content">
                        """
            + gamedata_tab
            + """
                    </div>
                </div>

                <div class="info-section">
                    <div class="section-header">名称一览</div>
                    <div class="section-content">
                        """
            + names_tab
            + """
                    </div>
                </div>
            </div>
        </div>
        """
        )

        return infobox_html

    def _extract_infobox_data(self, infobox):
        """Extract data from infobox, preserving tab structure if present."""
        data = {"fields": {}, "tabs": {}}

        # Extract individual data fields (for backward compatibility)
        for pi_data in infobox.find_all("div", class_=re.compile(r"pi-data")):
            label_elem = pi_data.find("h3", class_=re.compile(r"pi-data-label"))
            value_elem = pi_data.find("div", class_=re.compile(r"pi-data-value"))

            if label_elem and value_elem:
                label = label_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)
                data["fields"][label] = value

        # Check for tabbed structure
        tabber = infobox.find("section", class_=re.compile(r"wds-tabber"))
        if tabber:
            # Extract tab labels
            tab_labels = tabber.find_all(
                "div", class_=re.compile(r"wds-tabs__tab-label")
            )

            # Extract tab content
            tab_contents = tabber.find_all(
                "div", class_=re.compile(r"wds-tab__content")
            )

            # Pair labels with content
            for i, content in enumerate(tab_contents):
                if i < len(tab_labels):
                    tab_label = tab_labels[i].get_text(strip=True)
                    tab_data = {}

                    # Extract fields from this tab
                    for pi_data in content.find_all(
                        "div", class_=re.compile(r"pi-data")
                    ):
                        label_elem = pi_data.find(
                            "h3", class_=re.compile(r"pi-data-label")
                        )
                        value_elem = pi_data.find(
                            "div", class_=re.compile(r"pi-data-value")
                        )

                        if label_elem and value_elem:
                            label = label_elem.get_text(strip=True)
                            value = value_elem.get_text(strip=True)
                            tab_data[label] = value

                    data["tabs"][tab_label] = tab_data

        return data

    def _extract_page_title_fallback(self, soup):
        """Extract page title from alternative sources when infobox title fails"""
        # Try to find the main page title
        title_selectors = [
            ("h1", {"class": re.compile(r"page-header__title|firstHeading")}),
            ("h1", {"id": "firstHeading"}),
            ("h1", None),
        ]

        for tag, attrs in title_selectors:
            if attrs:
                title_elem = soup.find(tag, attrs)
            else:
                title_elem = soup.find(tag)

            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 1:
                    return title

        return ""  # Return empty instead of fallback

    def _find_names_tab(self, tabs):
        """Dynamically find the names tab by looking for tab labels that suggest names"""
        if not tabs:
            return None

        # First priority: exact matches for common name tab patterns
        for tab_label, tab_data in tabs.items():
            if "名称" in tab_label or "名字" in tab_label:
                return tab_label, tab_data

        # Second priority: tabs that contain mostly name-like fields
        for tab_label, tab_data in tabs.items():
            if not tab_data:
                continue
            # If most fields contain name-related characters, likely a names tab
            name_field_count = sum(
                1
                for field in tab_data.keys()
                if any(char in field for char in ["名", "英", "中", "文", "日"])
            )
            if name_field_count >= len(tab_data) * 0.5:  # At least 50% are name fields
                return tab_label, tab_data

        return None, None

    def _create_gamedata_tab(self, data):
        """Create the game data tab content with real data"""
        fields = data.get("fields", {})
        tabs = data.get("tabs", {})

        target_tab = None

        # Strategy: Use the 2nd tab (index 1) if there are multiple tabs
        if tabs and len(tabs) >= 2:
            tab_items = list(tabs.items())
            target_tab = tab_items[1][1]  # Get the second tab's data

        # Fallback: Look for tabs with numerical game data indicators
        if not target_tab:
            game_data_keywords = [
                "伤害",
                "生命",
                "血量",
                "HP",
                "攻击",
                "速度",
                "范围",
                "花费",
                "阳光",
            ]
            for tab_label, tab_data in tabs.items():
                # Look for tabs containing numerical game data fields
                if tab_data and any(
                    field
                    for field in tab_data.keys()
                    if any(keyword in field for keyword in game_data_keywords)
                ):
                    target_tab = tab_data
                    break

        # Another fallback: Find any non-names tab
        if not target_tab:
            # Find the names tab first so we can exclude it
            names_tab_label, names_tab_data = self._find_names_tab(tabs)
            names_tab_fields = set(names_tab_data.keys()) if names_tab_data else set()

            # Now find a tab that's not the names tab
            for tab_label, tab_data in tabs.items():
                if (
                    tab_data
                    and tab_label != names_tab_label
                    and not any(field in names_tab_fields for field in tab_data.keys())
                ):
                    target_tab = tab_data
                    break

        # Use flat fields for non-tabbed infoboxes
        if not target_tab:
            target_tab = fields

        # For flat fields, exclude any fields that appear to be from names tab
        if target_tab == fields and tabs:
            names_tab_label, names_tab_data = self._find_names_tab(tabs)
            if names_tab_data:
                names_fields = set(names_tab_data.keys())
                target_tab = {k: v for k, v in fields.items() if k not in names_fields}

        # Create field rows for display
        field_rows = []

        # Display all fields from the target tab
        for field_name, value in target_tab.items():
            field_rows.append(
                f'<div class="data-row">'
                f'<span class="data-label">{field_name}:</span>'
                f'<span class="data-value">{value}</span>'
                f"</div>"
            )

        return "\n".join(field_rows)

    def _create_names_tab(self, data):
        """Create the names tab content with real data"""
        fields = data.get("fields", {})
        tabs = data.get("tabs", {})
        title = data.get("title", "")

        # Extract names using dynamic tab detection
        names = self._extract_names_from_data(fields, title, tabs)

        name_rows = []

        # Display all name fields dynamically
        for field_name, value in names.items():
            if value:  # Only show fields with values
                name_rows.append(
                    f'<div class="name-row">'
                    f'<span class="name-label">{field_name}:</span>'
                    f'<span class="name-value">{value}</span>'
                    f"</div>"
                )

        return "\n".join(name_rows)

    def _extract_names_from_data(self, fields, title, tabs=None):
        """Extract name information from data, now supporting dynamic tab detection"""
        names = {}

        # Look for dedicated names tab first
        if tabs:
            names_tab_label, names_tab_data = self._find_names_tab(tabs)

            # If found names tab, use all its contents
            if names_tab_data:
                names.update(names_tab_data)
                return names

        # For non-tabbed infoboxes, just return empty dict
        # We won't try to guess which fields are names
        return names

    def _remove_svg_icons(self, soup):
        """Remove SVG icons from figure captions that cause spacing issues"""

        # Remove all SVG elements in figure captions
        for svg in soup.select("figure.thumb svg"):
            svg.decompose()

        # Remove info-icon elements
        for info_icon in soup.select("figure.thumb .info-icon"):
            info_icon.decompose()

        # Remove any a tags that only contained icons
        for link in soup.select("figure.thumb figcaption a"):
            if not link.get_text(strip=True):
                link.decompose()

    def _clean_toc_entries(self, soup):
        """Remove TOC entries for sections that have been removed and renumber"""
        removed_sections = ["衍生内容", "图库"]

        # Find the TOC
        toc = soup.find("div", {"id": "toc"})
        if not toc:
            return

        # Remove TOC entries for removed sections
        for section_title in removed_sections:
            for link in toc.find_all("a"):
                span = link.find("span", class_="toctext")
                if span and section_title in span.get_text(strip=True):
                    # Remove the entire li element containing this link
                    li_elem = link.find_parent("li")
                    if li_elem:
                        li_elem.decompose()

        # Renumber the remaining TOC entries
        self._renumber_toc(toc)

    def _renumber_toc(self, toc):
        """Renumber TOC entries to be sequential"""
        # Find all top-level TOC entries (toclevel-1)
        top_level_entries = toc.find_all("li", class_="toclevel-1")

        for i, li in enumerate(top_level_entries, 1):
            # Update the main section number
            tocnumber = li.find("span", class_="tocnumber")
            if tocnumber:
                tocnumber.string = str(i)

            # Find and renumber subsections (toclevel-2)
            subsections = li.find_all("li", class_="toclevel-2")
            for j, sub_li in enumerate(subsections, 1):
                sub_tocnumber = sub_li.find("span", class_="tocnumber")
                if sub_tocnumber:
                    sub_tocnumber.string = f"{i}.{j}"

    def _remove_mediawiki_comments(self, soup):
        """Remove MediaWiki performance and debug comments like NewPP limit report"""
        from bs4 import Comment

        # Find all HTML comments
        comments = soup.find_all(string=lambda text: isinstance(text, Comment))

        for comment in comments:
            comment_text = str(comment).strip()
            # Remove MediaWiki performance and debug comments
            if any(
                keyword in comment_text
                for keyword in [
                    "NewPP limit report",
                    "Transclusion expansion time report",
                    "Saved in parser cache",
                    "CPU time usage:",
                    "Real time usage:",
                    "Preprocessor visited node count:",
                    "Template argument size:",
                    "Lua time usage:",
                    "Lua memory usage:",
                ]
            ):
                comment.extract()
