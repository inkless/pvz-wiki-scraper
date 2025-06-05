"""
Chinese character conversion utility
Converts traditional Chinese to simplified Chinese using OpenCC
"""

import opencc


class ChineseTranslator:
    def __init__(self):
        """Initialize the traditional to simplified Chinese converter"""
        try:
            # Initialize OpenCC converter for traditional to simplified
            self.converter = opencc.OpenCC("t2s")  # traditional to simplified
            self.enabled = True
            print("🈲 Chinese translator initialized (T2S)")
        except Exception as e:
            print(f"⚠️  Failed to initialize Chinese translator: {e}")
            self.converter = None
            self.enabled = False

    def convert_text(self, text):
        """Convert traditional Chinese text to simplified Chinese"""
        if not self.enabled or not text:
            return text

        try:
            simplified = self.converter.convert(text)
            return simplified
        except Exception as e:
            print(f"⚠️  Error converting Chinese text: {e}")
            return text

    def convert_html(self, html_content):
        """Convert traditional Chinese in HTML content to simplified Chinese"""
        if not self.enabled or not html_content:
            return html_content

        try:
            # Convert the entire HTML content
            simplified_html = self.converter.convert(html_content)
            print("🈲 Converted traditional Chinese to simplified Chinese")
            return simplified_html
        except Exception as e:
            print(f"⚠️  Error converting Chinese HTML: {e}")
            return html_content
