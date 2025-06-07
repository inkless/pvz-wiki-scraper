#!/usr/bin/env python3
"""
Batch convert printable HTML files to PDF using Chrome headless and concatenate them.
"""

import subprocess
import yaml
from pathlib import Path
from pypdf import PdfWriter
import platform


def extract_filename_from_url(url):
    """Extract the filename from a wiki URL."""
    filename = url.split("/")[-1]

    # Handle special filename mappings
    filename_mappings = {"伴舞僵尸（新形象）": "伴舞僵尸新形象"}

    return filename_mappings.get(filename, filename)


def load_wiki_urls_order():
    """Load the wiki URLs and return ordered filenames."""
    with open("wiki_urls.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    ordered_filenames = []

    # Add plants first, then zombies (maintaining the order from YAML)
    for plant_url in data["content_types"]["plants"]:
        filename = extract_filename_from_url(plant_url) + ".html"
        ordered_filenames.append(filename)

    for zombie_url in data["content_types"]["zombies"]:
        filename = extract_filename_from_url(zombie_url) + ".html"
        ordered_filenames.append(filename)

    return ordered_filenames


def convert_html_to_pdf(html_path, pdf_path):
    """Convert HTML file to PDF using Chrome headless with cross-platform support."""

    try:
        # Determine Chrome executable path based on platform
        system = platform.system()
        if system == "Darwin":  # macOS
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        elif system == "Linux":
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
            ]
        elif system == "Windows":
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            ]
        else:
            return False, f"Unsupported platform: {system}"

        # Find available Chrome executable
        chrome_exe = None
        for path in chrome_paths:
            if Path(path).exists():
                chrome_exe = path
                break

        if not chrome_exe:
            return (
                False,
                "Chrome/Chromium not found. Please install Google Chrome or Chromium.",
            )

        # Use Chrome headless to convert HTML to PDF (no headers/footers)
        cmd = [
            chrome_exe,
            "--headless",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--no-pdf-header-footer",  # Remove date, URL, page numbers
            "--disable-pdf-tagging",  # Clean PDF structure
            "--virtual-time-budget=5000",  # Wait for content to load
            f"--print-to-pdf={pdf_path}",
            f"file://{html_path.absolute()}",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0:
            # Get file size for reporting
            if Path(pdf_path).exists():
                size = Path(pdf_path).stat().st_size
                return True, size
            else:
                return False, "PDF file not created"
        else:
            return False, result.stderr

    except Exception as e:
        return False, str(e)


def concatenate_pdfs(pdf_paths, output_path):
    """Concatenate multiple PDFs into a single PDF."""
    try:
        writer = PdfWriter()

        for pdf_path in pdf_paths:
            if pdf_path.exists():
                writer.append(str(pdf_path))
            else:
                print(f"⚠️  Warning: {pdf_path.name} not found, skipping...")

        with open(output_path, "wb") as output_file:
            writer.write(output_file)

        return True, output_path.stat().st_size

    except Exception as e:
        return False, str(e)


def main():
    """Convert all printable HTML files to PDF and concatenate them."""

    printable_dir = Path("docs/printable")
    pdf_dir = Path("docs/pdfs")

    # Create PDF output directory
    pdf_dir.mkdir(exist_ok=True)

    # Load the ordered filenames from wiki_urls.yaml
    try:
        ordered_filenames = load_wiki_urls_order()
        print(f"📋 Loaded order for {len(ordered_filenames)} files from wiki_urls.yaml")
    except Exception as e:
        print(f"❌ Error loading wiki_urls.yaml: {e}")
        return

    # Get all HTML files that exist and filter by ordered list
    available_files = {f.name: f for f in printable_dir.glob("*.html")}
    files_to_convert = []

    for filename in ordered_filenames:
        if filename in available_files:
            files_to_convert.append(available_files[filename])
        else:
            print(f"⚠️  Warning: {filename} not found in printable directory")

    if not files_to_convert:
        print("No HTML files found to convert")
        return

    print(f"Found {len(files_to_convert)} HTML files to convert (ordered)")
    print("-" * 50)

    successful = 0
    failed = 0
    total_size = 0
    converted_pdfs = []

    # Convert each HTML file to PDF in the specified order
    for html_file in files_to_convert:
        pdf_name = html_file.stem + ".pdf"
        pdf_path = pdf_dir / pdf_name

        print(f"Converting: {html_file.name}... ", end="", flush=True)

        success, result = convert_html_to_pdf(html_file, pdf_path)

        if success:
            successful += 1
            total_size += result
            converted_pdfs.append(pdf_path)
            print(f"✓ ({result:,} bytes)")
        else:
            failed += 1
            print(f"✗ ({result})")

    print("-" * 50)
    print(f"✅ Successfully converted: {successful} files")
    if failed > 0:
        print(f"❌ Failed: {failed} files")

    if successful > 0:
        avg_size = total_size / successful
        print(f"📊 Individual PDFs total size: {total_size:,} bytes")
        print(f"📊 Average size: {avg_size:,.0f} bytes")
        print(f"📁 Individual PDFs saved to: {pdf_dir}")

        # Concatenate all PDFs into one large PDF
        print("\n🔗 Concatenating PDFs...")
        combined_pdf_path = pdf_dir / "pvz-wiki-complete.pdf"

        concat_success, concat_result = concatenate_pdfs(
            converted_pdfs, combined_pdf_path
        )

        if concat_success:
            print(f"✅ Combined PDF created: {combined_pdf_path}")
            print(f"📊 Combined PDF size: {concat_result:,} bytes")
            print(f"📖 Contains {len(converted_pdfs)} pages/sections in wiki order")
        else:
            print(f"❌ Failed to create combined PDF: {concat_result}")

        # Show some sample files
        if successful <= 5:
            print("\n📄 First few generated PDFs:")
            for pdf_file in converted_pdfs[:5]:
                size = pdf_file.stat().st_size
                print(f"   {pdf_file.name} ({size:,} bytes)")


if __name__ == "__main__":
    main()
