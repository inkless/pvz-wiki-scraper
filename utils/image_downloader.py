#!/usr/bin/env python3
"""
Image Downloader Module
Handles downloading and processing images from wiki pages
"""

import requests
from pathlib import Path
from urllib.parse import urljoin, urlparse, unquote
import hashlib
import time
from bs4 import BeautifulSoup
import re
import json
import os


class ImageDownloader:
    """Handles downloading and processing images from wiki content"""

    def __init__(self, session, output_dir, base_url=""):
        self.session = session
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.images_dir.mkdir(exist_ok=True)
        self.base_url = base_url
        self.downloaded_images = {}  # URL -> local_path mapping
        self.download_delay = 0.5  # Delay between downloads to be respectful

        # File to store persistent URL -> filename mapping
        self.url_mapping_file = self.images_dir / ".url_mapping.json"
        self.content_hash_file = self.images_dir / ".content_hashes.json"

        # Load existing mappings
        self._load_mappings()

    def _load_mappings(self):
        """Load existing URL mappings and content hashes from files"""
        # Load URL mappings
        if self.url_mapping_file.exists():
            try:
                with open(self.url_mapping_file, "r", encoding="utf-8") as f:
                    url_mappings = json.load(f)
                    # Convert to Path objects and verify files still exist
                    for url, filename in url_mappings.items():
                        file_path = self.images_dir / filename
                        if file_path.exists():
                            self.downloaded_images[url] = file_path
                print(f"Loaded {len(self.downloaded_images)} existing mappings")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load URL mappings: {e}")

        # Load content hashes
        self.content_hashes = {}
        if self.content_hash_file.exists():
            try:
                with open(self.content_hash_file, "r", encoding="utf-8") as f:
                    self.content_hashes = json.load(f)
                print(f"Loaded {len(self.content_hashes)} content hashes")
            except (json.JSONDecodeError, Exception) as e:
                print(f"Warning: Could not load content hashes: {e}")

    def _save_mappings(self):
        """Save URL mappings and content hashes to files"""
        # Save URL mappings
        try:
            url_mappings = {
                url: path.name for url, path in self.downloaded_images.items()
            }
            with open(self.url_mapping_file, "w", encoding="utf-8") as f:
                json.dump(url_mappings, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save URL mappings: {e}")

        # Save content hashes
        try:
            with open(self.content_hash_file, "w", encoding="utf-8") as f:
                json.dump(self.content_hashes, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save content hashes: {e}")

    def _calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception:
            return None

    def _find_existing_file_by_content(self, content_hash):
        """Find existing file with the same content hash"""
        for existing_hash, filename in self.content_hashes.items():
            if existing_hash == content_hash:
                file_path = self.images_dir / filename
                if file_path.exists():
                    return file_path
        return None

    def process_images_in_html(self, html_content, page_url=""):
        """Process all images in HTML content and download them"""
        if not html_content:
            return html_content

        soup = BeautifulSoup(html_content, "lxml")
        images = soup.find_all("img")

        if not images:
            return str(soup)

        print(f"Found {len(images)} images to process...")

        # Keep track of URL mappings for updating links later
        url_mappings = {}

        for img in images:
            src = img.get("src")
            data_src = img.get("data-src")

            # Prefer data-src (lazy loading) over src
            if data_src:
                src = data_src

            if not src:
                continue

            # Skip data URLs, SVGs, or already local images
            if (
                src.startswith("data:")
                or src.startswith("./images/")
                or src.endswith(".svg")
            ):
                continue

            # Convert relative URLs to absolute
            if src.startswith("//"):
                src = "https:" + src
            elif src.startswith("/"):
                if page_url:
                    base = self._get_base_url(page_url)
                    src = urljoin(base, src)
                elif self.base_url:
                    src = urljoin(self.base_url, src)

            # Download and update src
            local_path = self._download_image(src)
            if local_path:
                # Update src to relative path
                relative_path = f"./images/{local_path.name}"
                img["src"] = relative_path

                # Store mapping for link updates
                url_mappings[src] = relative_path

                print(f"  ✅ Updated: {src} -> {relative_path}")
            else:
                print(f"  ❌ Failed to download: {src}")

        # Update image links (a tags with href pointing to images)
        self._update_image_links(soup, url_mappings)

        return str(soup)

    def _update_image_links(self, soup, url_mappings):
        """Update href attributes in image links to point to local files"""
        # Find all links that might point to images
        links = soup.find_all("a", href=True)

        for link in links:
            href = link.get("href")
            if not href:
                continue

            # Check if this href matches any of our downloaded images
            for original_url, local_path in url_mappings.items():
                # Direct match
                if href == original_url:
                    link["href"] = local_path
                    break

                # Extract base URLs without query parameters and scaling
                href_base = self._get_image_base_url(href)
                original_base = self._get_image_base_url(original_url)

                if href_base == original_base:
                    link["href"] = local_path
                    break

    def _get_image_base_url(self, url):
        """Extract base image URL without scaling parameters and query string"""
        if not url:
            return url

        # Remove query parameters
        base_url = url.split("?")[0]

        # Remove scaling parameters like /scale-to-width-down/150
        import re

        base_url = re.sub(r"/scale-to-width-down/\d+", "", base_url)
        base_url = re.sub(r"/revision/latest.*", "/revision/latest", base_url)

        return base_url

    def _download_image(self, url):
        """Download a single image and return local path"""
        # Check if already downloaded by URL
        if url in self.downloaded_images:
            existing_path = self.downloaded_images[url]
            if existing_path.exists():
                print(f"  ♻️  Using cached: {url} -> {existing_path.name}")
                return existing_path
            else:
                # File was deleted, remove from cache
                del self.downloaded_images[url]

        try:
            # Add delay to be respectful
            time.sleep(self.download_delay)

            print(f"  📥 Downloading: {url}")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()

            # Download to temporary location first to check content hash
            temp_filename = f"temp_{int(time.time())}_{os.getpid()}"
            temp_path = self.images_dir / temp_filename

            # Download and save to temp file
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            # Calculate content hash
            content_hash = self._calculate_file_hash(temp_path)
            if content_hash:
                # Check if we already have this exact content
                existing_file = self._find_existing_file_by_content(content_hash)
                if existing_file:
                    # Remove temp file and use existing one
                    temp_path.unlink()
                    self.downloaded_images[url] = existing_file
                    self._save_mappings()
                    print(f"  🔗 Duplicate content found, using: {existing_file.name}")
                    return existing_file

            # Generate safe filename for the new file
            filename = self._generate_filename(url, response.headers)
            local_path = self.images_dir / filename

            # Avoid overwriting existing files by name
            counter = 1
            original_stem = local_path.stem
            while local_path.exists():
                local_path = self.images_dir / (
                    f"{original_stem}_{counter}{local_path.suffix}"
                )
                counter += 1

            # Move temp file to final location
            temp_path.rename(local_path)

            # Cache the result
            self.downloaded_images[url] = local_path

            # Store content hash
            if content_hash:
                self.content_hashes[content_hash] = local_path.name

            # Save mappings
            self._save_mappings()

            return local_path

        except Exception as e:
            print(f"  ⚠️  Error downloading {url}: {e}")
            # Clean up temp file if it exists
            if "temp_path" in locals() and temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return None

    def _generate_filename(self, url, headers=None):
        """Generate a safe filename for the image"""
        # Parse URL
        parsed = urlparse(url)
        path = unquote(parsed.path)

        # Extract filename from URL
        filename = Path(path).name

        # If no filename, generate one from URL hash
        if not filename or "." not in filename:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

            # Try to get extension from content-type
            extension = ".jpg"  # default
            if headers:
                content_type = headers.get("content-type", "").lower()
                if "png" in content_type:
                    extension = ".png"
                elif "gif" in content_type:
                    extension = ".gif"
                elif "webp" in content_type:
                    extension = ".webp"

            filename = f"image_{url_hash}{extension}"

        # Clean filename
        filename = self._sanitize_filename(filename)

        # Ensure we have a valid extension
        if not Path(filename).suffix:
            filename += ".jpg"

        return filename

    def _sanitize_filename(self, filename):
        """Sanitize filename for safe filesystem storage"""
        # Remove unsafe characters
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)

        # Remove multiple consecutive underscores/spaces
        filename = re.sub(r"[_\s]+", "_", filename)

        # Limit length
        if len(filename) > 100:
            stem = Path(filename).stem[:80]
            suffix = Path(filename).suffix
            filename = stem + suffix

        return filename

    def _get_base_url(self, url):
        """Extract base URL from a full URL"""
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def get_download_stats(self):
        """Return statistics about downloaded images"""
        return {
            "total_downloaded": len(self.downloaded_images),
            "images_dir": str(self.images_dir),
            "downloaded_files": [path.name for path in self.downloaded_images.values()],
        }
