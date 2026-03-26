"""System configuration."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Directories
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates", "datasheet")
WEB_TEMPLATE_DIR = os.path.join(BASE_DIR, "templates", "web")
STATIC_DIR = os.path.join(BASE_DIR, "static")
CACHE_DIR = os.path.join(BASE_DIR, "cache", "images")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
VERSIONS_FILE = os.path.join(OUTPUT_DIR, "versions.json")

# Google Sheets (to be configured later)
GOOGLE_SHEETS = {
    "Cameras": {
        "sheet_id": "",  # Fill in when ready
        "gid": "0",
    },
}

# Fonts
FONT_FAMILY = "Roboto"

# Brand colors (extracted from PDF templates)
COLORS = {
    "primary_blue": "#03a9f4",
    "dark_text": "#231f20",
    "gray_text": "#6f6f6f",
    "light_gray": "#6f7073",
    "table_line": "#bcbec0",
    "white": "#ffffff",
}
