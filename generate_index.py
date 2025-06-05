#!/usr/bin/env python3
"""
Generate index.html with dynamic plant list from docs directory
"""

import os
import glob
import json
from datetime import datetime
from string import Template


def get_plant_list(output_dir="docs"):
    """Get list of all plant HTML files"""
    html_files = glob.glob(os.path.join(output_dir, "*.html"))

    # Filter out test files and index.html, extract plant names
    plants = []
    for file_path in html_files:
        filename = os.path.basename(file_path)
        plant_name = filename.replace(".html", "")

        # Skip test files and index
        if plant_name.startswith("test_") or plant_name == "index":
            continue

        plants.append(plant_name)

    # Sort plants alphabetically
    plants.sort()
    return plants


def load_template(template_path="templates/index_template.html"):
    """Load HTML template from file"""
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(
            f"Template file not found: {template_path}. "
            "Please ensure the templates directory exists."
        )


def generate_index_html(plants, output_path="docs/index.html"):
    """Generate index.html with the plant list using template"""

    # Load template
    template_content = load_template()
    template = Template(template_content)

    # Prepare template variables
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
    plant_list_json = json.dumps(plants, ensure_ascii=False, indent=8)

    # Replace template placeholders using substitute
    html_content = template.substitute(
        plant_count=len(plants),
        plant_list_json=plant_list_json,
        last_updated=last_updated,
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated index.html with {len(plants)} plants")
    return output_path


if __name__ == "__main__":
    plants = get_plant_list()
    generate_index_html(plants)
