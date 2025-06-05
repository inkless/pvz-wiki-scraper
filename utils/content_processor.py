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

    def clean_content(self, content_soup):
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

        # Clean up links - convert internal wiki links to text
        for link in cleaned.find_all("a"):
            href = link.get("href", "")
            if href.startswith("/wiki/") or "fandom.com" in href:
                # Convert internal links to plain text or remove href
                if link.text.strip():
                    link.replace_with(link.text)
                else:
                    link.decompose()

        # Remove empty paragraphs and divs
        for tag in cleaned.find_all(["p", "div"]):
            if not tag.get_text(strip=True):
                tag.decompose()

        # Extract and process infobox data
        sidebar_content = self._create_enhanced_infobox(cleaned)

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
        """Clean the 参见 (See Also) section by removing .navbar divs"""
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

    def _create_enhanced_infobox(self, soup):
        """Create enhanced infobox with tabs matching the screenshot design"""

        # Extract data from existing infobox
        infobox_data = self._extract_infobox_data(soup)

        if not infobox_data:
            return ""

        # Create the enhanced infobox HTML
        title = infobox_data.get("title", "未知植物")
        image = infobox_data.get("image", "")
        description = self._get_plant_description(title)
        description_tab = self._create_description_tab(infobox_data)
        gamedata_tab = self._create_gamedata_tab(infobox_data)
        names_tab = self._create_names_tab(infobox_data)

        infobox_html = (
            """
        <div class="plant-infobox">
            <div class="infobox-header">
                <div class="header-title">植物图鉴</div>
                <div class="plant-name">"""
            + title
            + """</div>
            </div>
            
            <div class="plant-image-container">
                """
            + image
            + """
                <div class="plant-description">"""
            + description
            + """</div>
            </div>
            
            <div class="infobox-sections">
                <div class="info-section">
                    <div class="section-header">图鉴描述</div>
                    <div class="section-content">
                        """
            + description_tab
            + """
                    </div>
                </div>
                
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

    def _extract_infobox_data(self, soup):
        """Extract data from the existing wiki infobox"""
        data = {}

        # Find portable infobox (the actual structure used by the wiki)
        infobox = soup.find("aside", class_=re.compile(r"portable-infobox"))

        # Fallback to older infobox patterns if portable infobox not found
        if not infobox:
            infobox = soup.find(["div", "table"], class_=re.compile(r"infobox|pi-item"))

        if not infobox:
            return None

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
                data["title"] = title_text
            else:
                # Extract from page URL or try to find page title elsewhere
                data["title"] = self._extract_page_title_fallback(soup)
        else:
            data["title"] = self._extract_page_title_fallback(soup)

        # Extract main image from portable infobox
        img_elem = infobox.find("img")
        if img_elem:
            src = img_elem.get("data-src") or img_elem.get("src", "")
            alt = data.get("title", "")
            if src:
                data["image"] = f'<img src="{src}" alt="{alt}" class="plant-image">'
            else:
                data["image"] = ""
        else:
            data["image"] = ""

        # Extract data fields from portable infobox structure
        data_fields = {}

        # Look for pi-data sections (portable infobox data)
        for data_elem in infobox.find_all("div", class_=re.compile(r"pi-data")):
            label_elem = data_elem.find("h3", class_=re.compile(r"pi-data-label"))
            value_elem = data_elem.find("div", class_=re.compile(r"pi-data-value"))

            if label_elem and value_elem:
                label = label_elem.get_text(strip=True)
                value = value_elem.get_text(strip=True)

                if label and value:
                    data_fields[label] = value

        # Also check for traditional infobox data structure as fallback
        if not data_fields:
            for data_elem in infobox.find_all(
                ["div", "tr"], class_=re.compile(r"pi-data|infobox-data")
            ):
                label_elem = data_elem.find(
                    ["div", "td", "h3"],
                    class_=re.compile(r"pi-data-label|infobox-label"),
                )
                value_elem = data_elem.find(
                    ["div", "td"], class_=re.compile(r"pi-data-value|infobox-value")
                )

                if label_elem and value_elem:
                    label = label_elem.get_text(strip=True)
                    value = value_elem.get_text(strip=True)
                    if label and value:
                        data_fields[label] = value

        data["fields"] = data_fields

        # Extract character navigation images
        nav_elem = infobox.find("div", class_=re.compile(r"pi-charanav|character-nav"))
        nav_images = []
        if nav_elem:
            for img in nav_elem.find_all("img"):
                nav_images.append(
                    {
                        "src": img.get("data-src") or img.get("src", ""),
                        "alt": img.get("alt", ""),
                    }
                )
        data["navigation"] = nav_images

        # Extract additional content from page for descriptions
        data["page_content"] = soup

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

        return "未知植物"  # Fallback

    def _create_description_tab(self, data):
        """Create the description tab content with real plant data"""
        # Try to extract description from wiki data first
        description = self._extract_description_from_page(data)

        # If no description found, use hardcoded as fallback
        if not description:
            description = "这是一个植物，具有独特的能力来对抗僵尸。"

        description_html = '<div class="desc-field">' + description + "</div>"
        return description_html

    def _get_plant_description(self, plant_name, extracted_description=None):
        """Get short description for plant image container"""
        # Use extracted description if available
        if extracted_description:
            # Extract first sentence or first 50 characters as short description
            first_sentence = extracted_description.split("。")[0] + "。"
            if len(first_sentence) > 80:
                return extracted_description[:50] + "..."
            return first_sentence

        # Fallback to hardcoded descriptions
        descriptions = {
            "豌豆射手": "向僵尸发射豌豆",
            "向日葵": "产生阳光",
            "樱桃炸弹": "爆炸攻击范围内僵尸",
            "坚果墙": "阻挡僵尸前进",
            "雪花豌豆": "发射减速豌豆",
            "连发豌豆": "连续发射两颗豌豆",
        }
        return descriptions.get(plant_name, "植物防御专家")

    def _extract_description_from_page(self, data):
        """Extract plant description from page content"""
        page_content = data.get("page_content")
        if not page_content:
            return None

        # Look for meaningful paragraphs in the main content
        paragraphs = page_content.find_all("p")

        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)
            # Skip very short paragraphs or those that seem to be navigation
            if len(text) < 50:
                continue
            # Skip paragraphs that look like infobox data
            if any(keyword in text for keyword in ["阳光花费", "恢复时间", "伤害"]):
                continue
            # Look for paragraphs that actually describe the plant
            if any(
                keyword in text for keyword in ["植物", "射手", "豌豆", "发射", "攻击"]
            ):
                return text

        return None

    def _get_plant_descriptions(self):
        """Get detailed descriptions for plants (fallback when no real data)"""
        return {
            "豌豆射手": "这是一个植物，具有独特的能力来对抗僵尸。",
        }

    def _create_gamedata_tab(self, data):
        """Create the game data tab content using real extracted data"""
        fields = data.get("fields", {})
        title = data.get("title", "")

        # Use real extracted data first, fallback to hardcoded data
        if fields:
            game_data_html = []
            for label, value in fields.items():
                # Skip name fields - they will be moved to the names section
                if "英文名称" in label or "中文名称" in label:
                    continue
                row_html = (
                    '<div class="game-data-row">'
                    '<div class="data-label">' + label + "</div>"
                    '<div class="data-value">' + value + "</div>"
                    "</div>"
                )
                game_data_html.append(row_html)
            return "".join(game_data_html)
        else:
            # Fallback to hardcoded data if no real data found
            plant_data = self._get_plant_specific_data(title)
            game_data_html = []
            for label, value in plant_data.items():
                row_html = (
                    '<div class="game-data-row">'
                    '<div class="data-label">' + label + "</div>"
                    '<div class="data-value">' + value + "</div>"
                    "</div>"
                )
                game_data_html.append(row_html)
            return "".join(game_data_html)

    def _get_plant_specific_data(self, plant_name):
        """Get specific game data for different plants (fallback for when no real data)"""
        # Simple fallback data - real data is extracted in _extract_infobox_data
        fallback_data = {
            "阳光花费": "100",
            "恢复时间": "7.5秒",
            "伤害": "20",
            "强度": "300",
        }
        return fallback_data

    def _create_names_tab(self, data):
        """Create the names tab content using real extracted names"""
        fields = data.get("fields", {})
        title = data.get("title", "")

        # Extract real names from the data
        names = self._extract_names_from_data(fields, title)

        names_html = (
            '<div class="names-list">'
            '<div class="name-row">'
            '<div class="name-label">中文名称:</div>'
            '<div class="name-value">' + names["chinese"] + "</div>"
            "</div>"
            '<div class="name-row">'
            '<div class="name-label">英文名称:</div>'
            '<div class="name-value">' + names["english"] + "</div>"
            "</div>"
        )

        # Add Japanese name if available
        if names.get("japanese"):
            names_html += (
                '<div class="name-row">'
                '<div class="name-label">日文:</div>'
                '<div class="name-value">' + names["japanese"] + "</div>"
                "</div>"
            )

        names_html += "</div>"
        return names_html

    def _extract_names_from_data(self, fields, title):
        """Extract real plant names from extracted data"""
        names = {"chinese": title or "未知植物", "english": "", "japanese": ""}

        # Look for names in the extracted fields
        for label, value in fields.items():
            if "英文名称" in label or "英文" in label:
                names["english"] = value
            elif "中文名称" in label or "中文" in label:
                names["chinese"] = value
            elif "日文名称" in label or "日文" in label:
                names["japanese"] = value

        # Fallback to hardcoded names if no real names found
        if not names["english"]:
            hardcoded_names = self._get_plant_names()
            if title in hardcoded_names:
                fallback = hardcoded_names[title]
                names["english"] = fallback.get("english", "Unknown")
                if not names["japanese"]:
                    names["japanese"] = fallback.get("japanese", "")

        return names

    def _get_plant_names(self):
        """Get plant names in different languages"""
        return {
            "豌豆射手": {
                "chinese": "豌豆射手",
                "english": "Peashooter",
            },
        }

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
