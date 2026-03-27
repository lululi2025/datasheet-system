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

# Google Sheets — each product line has its own spreadsheet
PRODUCT_LINES = {
    "Cloud Camera": {
        "sheet_id": "1jQUW9vvqzWEx-pMfPtSxUhf-Ov81cQzzSx16-YX1wqU",
        "overview_gid": "2086236498",
        "detail_specs_gid": "180970413",
        "category": "Cameras",
        "product_line_label": "AI Cloud Cameras",
    },
    "Cloud AP": {
        "sheet_id": "1WFQHS8LnjzIrAJa-Fih3qWCFICagbCQE9jML-ziwUwM",
        "overview_gid": "1507745148",
        "detail_specs_gid": "822333768",
        "category": "APs",
        "product_line_label": "Cloud Access Points",
    },
    "Cloud Switch": {
        "sheet_id": "1FkKUH-heE2VwlBsHo1XdPqW1MsQCT27JmFWlVV-Mwjk",
        "overview_gid": "0",
        "detail_specs_gid": "319325917",
        "category": "Switches",
        "product_line_label": "Cloud Managed Switches",
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
