#!/usr/bin/env python3
"""
Generate index.html with dynamic plant list from docs directory
"""

import os
import glob
import json
from datetime import datetime
from string import Template


def get_plant_list_with_images(output_dir="docs"):
    """Get list of all plant data from metadata file or fallback to HTML parsing"""
    metadata_file = os.path.join(output_dir, "plant_metadata.json")

    # Try to load from metadata file first
    if os.path.exists(metadata_file):
        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            # Convert metadata dict to list format
            plants = []
            for plant_name, plant_data in metadata.items():
                plants.append({"name": plant_name, "image": plant_data.get("image")})

            # Sort plants alphabetically by name
            plants.sort(key=lambda x: x["name"])
            print(f"Loaded {len(plants)} plants from metadata file")
            return plants

        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load metadata file: {e}")
            print("Falling back to HTML parsing...")

    # Fallback to HTML parsing if metadata file doesn't exist or is invalid
    return get_plant_list_from_html(output_dir)


def get_plant_list_from_html(output_dir="docs"):
    """Fallback method: Get list of all plant HTML files with their main images"""
    try:
        from bs4 import BeautifulSoup  # noqa: F401
    except ImportError:
        print("Warning: BeautifulSoup not available, returning plants without images")
        return get_plant_list_names_only(output_dir)

    html_files = glob.glob(os.path.join(output_dir, "*.html"))

    # Filter out test files and index.html, extract plant names and images
    plants = []
    for file_path in html_files:
        filename = os.path.basename(file_path)
        plant_name = filename.replace(".html", "")

        # Skip test files and index
        if plant_name.startswith("test_") or plant_name == "index":
            continue

        # Extract main plant image from the HTML file
        image_path = extract_plant_image(file_path)

        plants.append({"name": plant_name, "image": image_path})

    # Sort plants alphabetically by name
    plants.sort(key=lambda x: x["name"])
    print(f"Loaded {len(plants)} plants from HTML parsing")
    return plants


def get_plant_list_names_only(output_dir="docs"):
    """Minimal fallback: Get plant names only without images"""
    html_files = glob.glob(os.path.join(output_dir, "*.html"))

    plants = []
    for file_path in html_files:
        filename = os.path.basename(file_path)
        plant_name = filename.replace(".html", "")

        # Skip test files and index
        if plant_name.startswith("test_") or plant_name == "index":
            continue

        plants.append({"name": plant_name, "image": None})

    # Sort plants alphabetically by name
    plants.sort(key=lambda x: x["name"])
    print(f"Loaded {len(plants)} plants (names only)")
    return plants


def extract_plant_image(html_file_path):
    """Extract the main plant image from an HTML file"""
    try:
        from bs4 import BeautifulSoup

        with open(html_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        soup = BeautifulSoup(content, "html.parser")

        # Look for the plant image in the infobox
        plant_image = soup.find("img", class_="plant-image")
        if plant_image and plant_image.get("src"):
            # Remove the './' prefix if present
            image_src = plant_image["src"]
            if image_src.startswith("./"):
                image_src = image_src[2:]
            return image_src

        # Fallback: look for any image in the images directory
        images = soup.find_all("img")
        for img in images:
            src = img.get("src", "")
            if "images/" in src and not src.endswith(
                ".jpg"
            ):  # Prefer PNG icons over JPG photos
                if src.startswith("./"):
                    src = src[2:]
                return src

        return None

    except Exception as e:
        print(f"Error extracting image from {html_file_path}: {e}")
        return None


def get_plant_list(output_dir="docs"):
    """Legacy function for backwards compatibility"""
    plants_with_images = get_plant_list_with_images(output_dir)
    return [plant["name"] for plant in plants_with_images]


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


def generate_index_html(plants_data, output_path="docs/index.html"):
    """Generate index.html with the plant list using template"""

    # Load template
    template_content = load_template()
    template = Template(template_content)

    # Prepare template variables
    last_updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

    # Convert plants data to format expected by JavaScript
    if isinstance(plants_data[0], dict):
        # New format with images
        plant_count = len(plants_data)
        plant_list_json = json.dumps(plants_data, ensure_ascii=False, indent=8)
    else:
        # Legacy format (just names)
        plant_count = len(plants_data)
        plants_data = [{"name": name, "image": None} for name in plants_data]
        plant_list_json = json.dumps(plants_data, ensure_ascii=False, indent=8)

    # Replace template placeholders using substitute
    html_content = template.substitute(
        plant_count=plant_count,
        plant_list_json=plant_list_json,
        last_updated=last_updated,
    )

    # Ensure the directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write the file
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated index.html with {plant_count} plants")
    return output_path


if __name__ == "__main__":
    plants = get_plant_list_with_images()
    generate_index_html(plants)
