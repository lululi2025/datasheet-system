"""Render datasheet HTML for preview and browser-based PDF export."""
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from config import BASE_DIR, TEMPLATE_DIR
from models import ProductBase
from services.drive_images import get_image_urls

# Height estimates (in pt) for page layout calculation
_PAGE_HEIGHT = 792
_TOP_BAR_HEIGHT = 21
_SPEC_TITLE_HEIGHT = 42  # title + margin
_BOTTOM_MARGIN = 40  # page number + safety margin
_AVAILABLE_HEIGHT = _PAGE_HEIGHT - _TOP_BAR_HEIGHT - _SPEC_TITLE_HEIGHT - _BOTTOM_MARGIN

# Per-item height estimates (tight layout matching reference PDF)
_CATEGORY_HEADER_HEIGHT = 18  # header + margins
_SPEC_ROW_HEIGHT = 18  # label + value + padding


def _estimate_section_height(section) -> float:
    """Estimate the rendered height of a spec section (header + rows)."""
    return _CATEGORY_HEADER_HEIGHT + len(section.items) * _SPEC_ROW_HEIGHT


def _split_into_pages(sections: list) -> list[dict]:
    """Split spec sections into multiple pages, each with left/right columns.

    Returns a list of pages, each page is:
        {"left": [sections], "right": [sections]}
    """
    if not sections:
        return [{"left": [], "right": []}]

    # First, split all sections into page-sized groups.
    # Each page has two columns, so each column has _AVAILABLE_HEIGHT.
    pages = []
    remaining = list(sections)

    while remaining:
        # Greedily fill left column, then right column
        left = []
        right = []
        left_h = 0
        right_h = 0

        i = 0
        # Fill left column
        while i < len(remaining):
            sh = _estimate_section_height(remaining[i])
            if left_h + sh <= _AVAILABLE_HEIGHT or not left:
                # Always add at least one section to left
                left.append(remaining[i])
                left_h += sh
                i += 1
            else:
                break

        # Fill right column
        while i < len(remaining):
            sh = _estimate_section_height(remaining[i])
            if right_h + sh <= _AVAILABLE_HEIGHT or not right:
                right.append(remaining[i])
                right_h += sh
                i += 1
            else:
                break

        pages.append({"left": left, "right": right})
        remaining = remaining[i:]

    # If only one page, try to balance left/right columns evenly
    if len(pages) == 1:
        pages = [_balance_columns(sections)]

    return pages


def _balance_columns(sections: list) -> dict:
    """Balance sections into left/right columns for a single page."""
    total_items = sum(len(s.items) for s in sections)
    target = total_items / 2

    left = []
    right = []
    count = 0
    split_done = False

    for section in sections:
        if not split_done and count + len(section.items) <= target + 2:
            left.append(section)
            count += len(section.items)
        else:
            split_done = True
            right.append(section)

    return {"left": left, "right": right}


def render_html(product: ProductBase, version: str, template_name: str = None) -> str:
    """Render product data into HTML string with URL-based image paths."""
    if template_name is None:
        # Map category to template file; fall back to cameras.html (generic layout)
        category_templates = {
            "cameras": "cameras.html",
        }
        template_name = category_templates.get(product.category.lower(), "cameras.html")

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)

    spec_pages = _split_into_pages(product.spec_sections)

    # Use URL paths for images
    logo_path = "/static/logo/engenius_cloud_icon.png"

    # Try Google Drive first, fall back to local static files
    drive_urls = get_image_urls(product.model_name)
    product_image = drive_urls["product_image"]
    hardware_image = drive_urls["hardware_image"]

    # Auto-trim whitespace for product images from Drive
    if product_image and product_image.startswith("/drive-image/"):
        product_image += "?trim=1"

    # Fallback to local static files if Drive URLs not available
    if not product_image and product.product_image:
        img_name = os.path.basename(product.product_image)
        product_image = f"/static/images/{img_name}"
    if not hardware_image and product.hardware_image:
        img_name = os.path.basename(product.hardware_image)
        hardware_image = f"/static/images/{img_name}"

    product_dict = product.model_dump()
    product_dict["product_image"] = product_image
    product_dict["hardware_image"] = hardware_image

    # QR code pointing to EnGenius product page
    product_url = f"https://www.engeniustech.com/engenius-cloud/{product.model_name.lower()}"
    qr_code_url = (
        f"https://api.qrserver.com/v1/create-qr-code/"
        f"?size=150x150&data={product_url}"
    )

    html = template.render(
        product=type(product)(**product_dict),
        logo_path=logo_path,
        spec_pages=spec_pages,
        # Keep backward compatibility
        left_sections=spec_pages[0]["left"] if spec_pages else [],
        right_sections=spec_pages[0]["right"] if spec_pages else [],
        qr_code_url=qr_code_url,
        version=version,
        date=datetime.now().strftime("%m/%d/%Y"),
    )
    return html
