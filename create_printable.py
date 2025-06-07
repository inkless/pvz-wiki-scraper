#!/usr/bin/env python3
"""
Create printable PDF versions of wiki pages.
Removes unwanted elements and reorganizes content for better print layout.
"""

from pathlib import Path
from bs4 import BeautifulSoup, NavigableString


def extract_gamedata_info(soup):
    """Extract game data from the sidebar infobox."""
    gamedata = {}

    infobox = soup.find(class_="plant-infobox") or soup.find(class_="zombie-infobox")
    if not infobox:
        return gamedata

    # Extract image
    image = infobox.find("img")
    if image:
        gamedata["_image_src"] = image.get("src")
        gamedata["_image_alt"] = image.get("alt", "")

    # Extract game data
    data_rows = infobox.find_all(class_="data-row")
    for row in data_rows:
        label = row.find(class_="data-label")
        value = row.find(class_="data-value")
        if label and value:
            gamedata[label.get_text(strip=True)] = value.get_text(strip=True)

    # Extract name data
    name_rows = infobox.find_all(class_="name-row")
    for row in name_rows:
        label = row.find(class_="name-label")
        value = row.find(class_="name-value")
        if label and value:
            gamedata[label.get_text(strip=True)] = value.get_text(strip=True)

    return gamedata


def create_synthetic_almanac(soup, gamedata, biao_xian_header, custom_intro=None):
    """Create a synthetic almanac section for pages that don't have one."""

    # Create section header
    almanac_title = soup.new_tag("h2")
    almanac_title_span = soup.new_tag(
        "span", **{"class": "mw-headline", "id": "图鉴"}, string="图鉴"
    )
    almanac_title.append(almanac_title_span)

    # Create new reorganized content
    new_content = soup.new_tag("div", **{"class": "reorganized-almanac"})

    # Create image section using extracted image from gamedata
    if "_image_src" in gamedata:
        image_section = soup.new_tag("div", **{"class": "almanac-image-section"})
        new_img = soup.new_tag(
            "img",
            **{
                "src": gamedata["_image_src"],
                "alt": gamedata.get("_image_alt", ""),
                "class": "almanac-main-image",
            },
        )
        image_section.append(new_img)
        new_content.append(image_section)
    else:
        # If no gamedata image, try to find an image from main content
        content_img = soup.find("img", src=lambda x: x and "./images/image_" in x)
        if content_img:
            image_section = soup.new_tag("div", **{"class": "almanac-image-section"})
            new_img = soup.new_tag(
                "img",
                **{
                    "src": content_img.get("src"),
                    "alt": content_img.get("alt", ""),
                    "class": "almanac-main-image",
                },
            )
            image_section.append(new_img)
            new_content.append(image_section)

    # Create three-column info section
    info_section = soup.new_tag("div", **{"class": "three-column-info"})

    # Column 1: 简介 (Introduction) - leave empty as requested, unless custom_intro provided
    intro_col = soup.new_tag("div", **{"class": "info-column intro-column"})
    intro_title = soup.new_tag("h3", string="简介")
    intro_col.append(intro_title)

    if custom_intro:
        intro_p = soup.new_tag("p", string=custom_intro)
        intro_col.append(intro_p)
    # Otherwise no content added to introduction as per user request

    # Column 2: 游戏数据 (Game Data) - use gamedata infobox content
    data_col = soup.new_tag("div", **{"class": "info-column data-column"})
    data_title = soup.new_tag("h3", string="游戏数据")
    data_col.append(data_title)

    # Add game data from infobox
    game_data_keys = [
        "强度:",
        "报纸强度:",
        "速度:",
        "特殊:",
        "伤害:",
        "首次出场:",
        "出场:",
    ]
    for key in game_data_keys:
        if key in gamedata:
            data_item = soup.new_tag("div", **{"class": "data-item"})
            label = soup.new_tag(
                "span", **{"class": "data-label"}, string=key.replace(":", "")
            )
            value = soup.new_tag(
                "span", **{"class": "data-value"}, string=gamedata[key]
            )
            data_item.append(label)
            data_item.append(NavigableString(": "))
            data_item.append(value)
            data_col.append(data_item)

    # Column 3: 名称一览 (Names) - use gamedata infobox content
    names_col = soup.new_tag("div", **{"class": "info-column names-column"})
    names_title = soup.new_tag("h3", string="名称一览")
    names_col.append(names_title)

    # Add name data from infobox
    name_keys = ["英文名称:", "中文名称:", "其他名称:"]
    for key in name_keys:
        if key in gamedata:
            name_item = soup.new_tag("div", **{"class": "name-item"})
            label = soup.new_tag(
                "span", **{"class": "name-label"}, string=key.replace(":", "")
            )
            value = soup.new_tag(
                "span", **{"class": "name-value"}, string=gamedata[key]
            )
            name_item.append(label)
            name_item.append(NavigableString(": "))
            name_item.append(value)
            names_col.append(name_item)

    info_section.append(intro_col)
    info_section.append(data_col)
    info_section.append(names_col)
    new_content.append(info_section)

    # Insert the new content before 表现 section, or after first paragraph if no 表现
    if biao_xian_header:
        biao_xian_header.insert_before(almanac_title)
        biao_xian_header.insert_before(new_content)
    else:
        # If no 表现 section, insert after the first paragraph
        first_p = soup.find("p")
        if first_p:
            first_p.insert_after(new_content)
            first_p.insert_after(almanac_title)
        else:
            # If no paragraphs, insert at beginning of main content
            main_content = soup.find(class_="mw-parser-output")
            if main_content:
                main_content.insert(0, new_content)
                main_content.insert(0, almanac_title)


def merge_almanac_sections(soup, gamedata):
    """Merge the 图鉴 and infobox sections and reorganize into three columns.
    If no 图鉴 section exists, create a synthetic one using gamedata."""

    # Find the 图鉴 section
    zhi_jian_header = None
    for h2 in soup.find_all("h2"):
        if "图鉴" in h2.get_text():
            zhi_jian_header = h2
            break

    # Find the 表现 section to insert before it
    biao_xian_header = None
    for h2 in soup.find_all("h2"):
        if "表现" in h2.get_text():
            biao_xian_header = h2
            break

    # Find the almanac content (for existing almanac sections)
    almanac_div = soup.find(class_="almanac-plant") or soup.find(
        class_="almanac-zombie"
    )

    # If no almanac section exists, create a synthetic one
    if not zhi_jian_header and not almanac_div:
        create_synthetic_almanac(soup, gamedata, biao_xian_header)
        return

    # If almanac section exists but no content div, this might be a weird almanac like 豌豆射手僵尸
    if not almanac_div:
        # Check if this is a case like 豌豆射手僵尸 where 图鉴 section has plain text
        if zhi_jian_header:
            # Get all content between 图鉴 h2 and the next h2
            weird_almanac_content = []
            current = zhi_jian_header.next_sibling
            while current:
                if hasattr(current, "name") and current.name == "h2":
                    break
                if hasattr(current, "get_text") and current.get_text(strip=True):
                    weird_almanac_content.append(current.get_text(strip=True))
                current = current.next_sibling

            # If we found content, treat this as a weird almanac and create synthetic one
            if weird_almanac_content:
                # Remove all content between 图鉴 h2 and next h2
                current = zhi_jian_header.next_sibling
                while current:
                    next_sibling = current.next_sibling
                    if hasattr(current, "name") and current.name == "h2":
                        break
                    if hasattr(current, "decompose"):
                        current.decompose()
                    elif hasattr(current, "extract"):
                        current.extract()
                    current = next_sibling

                # Remove the old 图鉴 header
                zhi_jian_header.decompose()

                # Use the weird almanac content as introduction
                intro_text = " ".join(weird_almanac_content)
                create_synthetic_almanac(
                    soup, gamedata, biao_xian_header, custom_intro=intro_text
                )
                return
        return

    # Extract almanac image (check both plant and zombie image classes)
    almanac_image = almanac_div.find(class_="almanac-plant-image") or almanac_div.find(
        class_="almanac-zombie-image"
    )

    # Check if image exists and has a valid src (not just a placeholder like [[File:name.png|]])
    almanac_img_tag = None
    if almanac_image:
        almanac_img_tag = almanac_image.find("img")
        if almanac_img_tag and (
            not almanac_img_tag.get("src") or "[[File:" in str(almanac_image)
        ):
            almanac_img_tag = None  # Invalid or placeholder image

    # If no valid image in almanac, try to get image from gamedata infobox or main content
    if not almanac_img_tag:
        infobox = soup.find(class_="plant-infobox") or soup.find(
            class_="zombie-infobox"
        )
        potential_image = None
        if infobox:
            potential_image = infobox.find("img")

        # If no infobox image, try to find an image from main content
        if not potential_image:
            potential_image = soup.find(
                "img", src=lambda x: x and "./images/image_" in x
            )

        if potential_image:
            # Create a fake almanac image structure with the found image
            almanac_image = soup.new_tag("div", **{"class": "almanac-plant-image"})
            almanac_image.append(potential_image.copy())
            almanac_img_tag = potential_image

    # Extract almanac description parts (check both plant and zombie description classes)
    description_div = almanac_div.find(
        class_="almanac-plant-description"
    ) or almanac_div.find(class_="almanac-zombie-description")
    introduction = ""
    flavor_text = ""

    if description_div:
        # Get introduction (first paragraph)
        header_p = description_div.find(class_="almanac-description-header")
        if header_p:
            introduction = header_p.get_text(strip=True)

        # Get flavor text
        flavor_p = description_div.find(class_="almanac-description-flavor")
        if flavor_p:
            flavor_text = flavor_p.get_text(strip=True)

    # Create new reorganized content
    new_content = soup.new_tag("div", **{"class": "reorganized-almanac"})

    # Create section header
    almanac_title = soup.new_tag("h2")
    almanac_title_span = soup.new_tag(
        "span", **{"class": "mw-headline", "id": "图鉴"}, string="图鉴"
    )
    almanac_title.append(almanac_title_span)

    # Create image section
    if almanac_img_tag:
        image_section = soup.new_tag("div", **{"class": "almanac-image-section"})
        new_img = soup.new_tag(
            "img",
            **{
                "src": almanac_img_tag.get("src"),
                "alt": almanac_img_tag.get("alt", ""),
                "class": "almanac-main-image",
            },
        )
        image_section.append(new_img)
        new_content.append(image_section)
    elif "_image_src" in gamedata:
        # Use gamedata image if no valid almanac image
        image_section = soup.new_tag("div", **{"class": "almanac-image-section"})
        new_img = soup.new_tag(
            "img",
            **{
                "src": gamedata["_image_src"],
                "alt": gamedata.get("_image_alt", ""),
                "class": "almanac-main-image",
            },
        )
        image_section.append(new_img)
        new_content.append(image_section)

    # Create three-column info section
    info_section = soup.new_tag("div", **{"class": "three-column-info"})

    # Column 1: 简介 (Introduction)
    intro_col = soup.new_tag("div", **{"class": "info-column intro-column"})
    intro_title = soup.new_tag("h3", string="简介")
    intro_col.append(intro_title)
    if introduction:
        intro_p = soup.new_tag("p", string=introduction)
        intro_col.append(intro_p)
    if flavor_text:
        flavor_p = soup.new_tag("p", string=flavor_text)
        flavor_p["class"] = "flavor-text"
        intro_col.append(flavor_p)

    # Column 2: 游戏数据 (Game Data)
    data_col = soup.new_tag("div", **{"class": "info-column data-column"})
    data_title = soup.new_tag("h3", string="游戏数据")
    data_col.append(data_title)

    # Add game data from infobox
    game_data_keys = ["阳光花费:", "恢复时间:", "伤害:", "强度:", "射速:", "解锁方式:"]
    for key in game_data_keys:
        if key in gamedata:
            data_item = soup.new_tag("div", **{"class": "data-item"})
            label = soup.new_tag(
                "span", **{"class": "data-label"}, string=key.replace(":", "")
            )
            value = soup.new_tag(
                "span", **{"class": "data-value"}, string=gamedata[key]
            )
            data_item.append(label)
            data_item.append(NavigableString(": "))
            data_item.append(value)
            data_col.append(data_item)

    # Column 3: 名称一览 (Names)
    names_col = soup.new_tag("div", **{"class": "info-column names-column"})
    names_title = soup.new_tag("h3", string="名称一览")
    names_col.append(names_title)

    # Add name data from infobox
    name_keys = ["英文名称:", "中文名称:", "其他名称:"]
    for key in name_keys:
        if key in gamedata:
            name_item = soup.new_tag("div", **{"class": "name-item"})
            label = soup.new_tag(
                "span", **{"class": "name-label"}, string=key.replace(":", "")
            )
            value = soup.new_tag(
                "span", **{"class": "name-value"}, string=gamedata[key]
            )
            name_item.append(label)
            name_item.append(NavigableString(": "))
            name_item.append(value)
            names_col.append(name_item)

    info_section.append(intro_col)
    info_section.append(data_col)
    info_section.append(names_col)
    new_content.append(info_section)

    # Remove the old 图鉴 header and almanac div
    if zhi_jian_header:
        zhi_jian_header.decompose()
    if almanac_div:
        almanac_div.decompose()

    # Insert the new content before 表现 section, or at the beginning if 表现 not found
    if biao_xian_header:
        biao_xian_header.insert_before(almanac_title)
        biao_xian_header.insert_before(new_content)
    else:
        # If no 表现 section, insert after the first paragraph
        first_p = soup.find("p")
        if first_p:
            first_p.insert_after(new_content)
            first_p.insert_after(almanac_title)


def remove_unwanted_elements(soup):
    """Remove elements that shouldn't appear in printable version."""

    # Remove table of contents
    toc_elements = soup.find_all(class_="toc")
    for element in toc_elements:
        element.decompose()

    # Remove back button container
    back_button_elements = soup.find_all(class_="back-button-container")
    for element in back_button_elements:
        element.decompose()

    # Remove the redundant almanac-plant-title (since we have main title)
    almanac_title = soup.find(class_="almanac-plant-title")
    if almanac_title:
        almanac_title.decompose()

    # Remove the entire sidebar (since we're merging its content)
    sidebar = soup.find(class_="sidebar")
    if sidebar:
        sidebar.decompose()

    # List of sections to remove completely
    sections_to_remove = ["参见", "花絮", "参考", "参考资料", "衍生内容", "其它版本"]

    # Find and remove all unwanted sections
    h2_elements = soup.find_all("h2")

    for h2 in h2_elements:
        h2_text = h2.get_text().strip()

        # Check if this h2 contains any of the unwanted section names
        for section_name in sections_to_remove:
            if section_name in h2_text:
                # Remove this h2 and everything after it until the next h2 or end
                current = h2
                while current:
                    next_sibling = current.next_sibling

                    # Stop if we hit another h2
                    if (
                        hasattr(current, "name")
                        and current.name == "h2"
                        and current != h2
                    ):
                        break

                    # Remove the current element
                    if hasattr(current, "decompose"):
                        current.decompose()
                    else:
                        current.extract()

                    current = next_sibling
                break  # Found a match, no need to check other section names


def create_print_css():
    """Create improved print-optimized CSS."""
    css_content = """
/* Improved Print-optimized CSS */
@media print {
    * {
        -webkit-print-color-adjust: exact !important;
        color-adjust: exact !important;
    }
    
    @page {
        margin: 1.5cm;
        size: A4;
    }
}

* {
    box-sizing: border-box;
}

body {
    font-family: "Times New Roman", "SimSun", serif;
    line-height: 1.4;
    margin: 0;
    padding: 15px;
    color: #000;
    background: #fff;
    font-size: 13pt;
}

.container {
    max-width: 100%;
    margin: 0;
    padding: 0;
}

.content-title {
    color: #000;
    margin: 0 0 1em 0;
    padding: 8px 0;
    font-size: 26pt;
    font-weight: bold;
    text-align: center;
    border-bottom: 2px solid #000;
    page-break-after: avoid;
}

.content {
    display: block;
}

.main-content {
    background: #fff;
    padding: 0;
    border: none;
    box-shadow: none;
    width: 100%;
}

h2, h3, h4, h5, h6 {
    color: #000;
    margin-top: 1.2em;
    margin-bottom: 0.4em;
    font-weight: bold;
    page-break-after: avoid;
}

h2 {
    font-size: 18pt;
    border-bottom: 1px solid #000;
    padding-bottom: 0.2em;
}

h3 {
    font-size: 15pt;
    margin-top: 1em;
    margin-bottom: 0.3em;
}

p {
    margin-bottom: 0.8em;
    color: #000;
    text-align: justify;
    orphans: 2;
    widows: 2;
}

a {
    color: #000;
    text-decoration: underline;
}

/* Reorganized almanac styles */
.reorganized-almanac {
    border: 2px solid #000;
    background: #f9f9f9;
    margin: 1em 0;
    padding: 15px;
    page-break-inside: avoid;
}

.almanac-image-section {
    text-align: center;
    margin-bottom: 15px;
    padding-bottom: 15px;
    border-bottom: 1px solid #ccc;
}

.almanac-main-image {
    max-width: 200px;
    max-height: 150px;
    border: 1px solid #000;
}

.three-column-info {
    display: flex;
    gap: 20px;
    margin-top: 10px;
}

.info-column {
    flex: 1;
    background: #fff;
    padding: 10px;
    border: 1px solid #ccc;
}

.info-column h3 {
    margin-top: 0;
    margin-bottom: 10px;
    font-size: 14pt;
    background: #f0f0f0;
    padding: 5px;
    border-bottom: 1px solid #ccc;
}

.data-item, .name-item {
    margin-bottom: 5px;
    font-size: 12pt;
}

.data-label, .name-label {
    font-weight: bold;
}

.flavor-text {
    font-style: italic;
    color: #333;
    font-size: 12pt;
    margin-top: 10px;
}

/* Regular content styles */
figure {
    margin: 1em 0;
    page-break-inside: avoid;
}

figcaption {
    text-align: center;
    font-style: italic;
    margin-top: 5px;
}

img {
    max-width: 100%;
    height: auto;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 1em 0;
    background: #fff;
    border: 1px solid #000;
    page-break-inside: avoid;
    font-size: 12pt;
}

th, td {
    border: 1px solid #000;
    padding: 6px;
    text-align: left;
}

th {
    background: #f0f0f0;
    color: #000;
    font-weight: bold;
}

ul, ol {
    margin: 0.8em 0;
    padding-left: 2em;
}

li {
    margin-bottom: 0.3em;
}

/* Hide unwanted elements */
.navbox, .navbox-div,
.back-button-container,
.toc,
.sidebar {
    display: none !important;
}

/* Print optimizations */
@media print {
    .three-column-info {
        display: flex !important;
    }
    
    .info-column {
        break-inside: avoid;
    }
    
    .reorganized-almanac {
        break-inside: avoid;
    }
}
"""
    return css_content


def process_html_file(input_path, output_path):
    """Process a single HTML file to create printable version."""

    with open(input_path, "r", encoding="utf-8") as f:
        content = f.read()

    soup = BeautifulSoup(content, "html.parser")

    # Extract game data before removing sidebar
    gamedata = extract_gamedata_info(soup)

    # Remove unwanted elements
    remove_unwanted_elements(soup)

    # Merge and reorganize almanac sections
    merge_almanac_sections(soup, gamedata)

    # Update CSS link
    css_link = soup.find("link", rel="stylesheet")
    if css_link:
        css_link["href"] = "./styles/print.css"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(str(soup))


def main():
    """Process all HTML files and create printable versions."""

    docs_dir = Path("docs")
    output_dir = Path("docs/printable")

    # Create output directory
    output_dir.mkdir(exist_ok=True)
    styles_dir = output_dir / "styles"
    styles_dir.mkdir(exist_ok=True)

    # Create improved print CSS
    css_content = create_print_css()
    with open(styles_dir / "print.css", "w", encoding="utf-8") as f:
        f.write(css_content)

    # Copy images directory
    images_src = docs_dir / "images"
    images_dst = output_dir / "images"
    if images_src.exists():
        import shutil

        if images_dst.exists():
            shutil.rmtree(images_dst)
        shutil.copytree(images_src, images_dst)

    # Process all HTML files
    html_files = list(docs_dir.glob("*.html"))
    processed_count = 0

    for html_file in html_files:
        if html_file.name == "index.html":
            continue  # Skip index

        output_file = output_dir / html_file.name
        try:
            process_html_file(html_file, output_file)
            processed_count += 1
            print(f"✓ Processed: {html_file.name}")
        except Exception as e:
            print(f"✗ Error processing {html_file.name}: {e}")

    print(f"\n✅ Successfully processed {processed_count} files")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎨 Updated CSS: {styles_dir / 'print.css'}")
    print("\nPrintable versions created with improved layout!")


if __name__ == "__main__":
    main()
