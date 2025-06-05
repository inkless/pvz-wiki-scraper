#!/usr/bin/env python3
"""
Generate index.html with dynamic plant list from docs directory
"""

import os
import json
from datetime import datetime
from string import Template


def get_all_content_with_types(output_dir="docs"):
    """Get list of all content (plants and zombies) with content type information"""
    metadata_file = os.path.join(output_dir, "content_metadata.json")

    if not os.path.exists(metadata_file):
        raise FileNotFoundError(f"Metadata file not found: {metadata_file}")

    try:
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        # Convert all metadata to list format with content type
        content_items = []
        for item_name, item_data in metadata.items():
            content_items.append(
                {
                    "name": item_name,
                    "image": item_data.get("image"),
                    "content_type": item_data.get("content_type", "plants"),
                }
            )

        print(f"Loaded {len(content_items)} total content items from metadata file")
        return content_items

    except (json.JSONDecodeError, IOError) as e:
        raise RuntimeError(f"Could not load metadata file: {e}")


def load_template(template_path="templates/index_template.html"):
    """Load HTML template from file"""
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"Template file not found: {template_path}. "
            "Please ensure the templates directory exists."
        )

    with open(template_path, "r", encoding="utf-8") as f:
        return f.read()


def generate_index_html(content_data, output_path="docs/index.html"):
    """Generate index.html with the content list using template"""

    # Load template
    template_content = load_template()
    template = Template(template_content)

    # Prepare template variables
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Count plants and zombies from content data
    plant_count = 0
    zombie_count = 0

    # Prepare data for JavaScript (remove content_type for frontend)
    js_content_data = []

    for item in content_data:
        # Count by content type
        content_type = item.get("content_type", "plants")
        if content_type == "plants":
            plant_count += 1
        elif content_type == "zombies":
            zombie_count += 1

        # Prepare data for JavaScript (include content_type for better grouping)
        js_item = {
            "name": item["name"],
            "image": item.get("image"),
            "content_type": content_type,
        }
        js_content_data.append(js_item)

    plant_list_json = json.dumps(js_content_data, ensure_ascii=False, indent=8)

    # Generate appropriate stats text based on content
    if zombie_count > 0 and plant_count > 0:
        # Combined index
        stats_text = (
            f'<p>共收录 <span class="content-type-count">{plant_count}</span> 种植物和 '
            f'<span class="content-type-count">{zombie_count}</span> 种僵尸</p>'
        )
    elif zombie_count > 0:
        # Zombies only
        stats_text = f'<p>共收录 <span class="content-type-count">{zombie_count}</span> 种僵尸</p>'
    else:
        # Plants only (or legacy)
        stats_text = f'<p>共收录 <span class="content-type-count">{plant_count}</span> 种植物</p>'

    # Replace template placeholders using substitute
    html_content = template.substitute(
        plant_count=plant_count,
        zombie_count=zombie_count,
        stats_text=stats_text,
        plant_list_json=plant_list_json,
        last_updated=last_updated,
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    if zombie_count > 0:
        print(
            f"Generated index.html with {plant_count} plants and {zombie_count} zombies"
        )
    else:
        print(f"Generated index.html with {plant_count} plants")
    return output_path


def generate_combined_index_html(output_dir="docs", output_path="docs/index.html"):
    """Generate combined index.html with both plants and zombies"""

    # Get all content with content type information
    all_content = get_all_content_with_types(output_dir)

    # Generate index with automatic counting
    return generate_index_html(all_content, output_path)


if __name__ == "__main__":
    generate_combined_index_html()
