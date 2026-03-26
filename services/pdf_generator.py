"""Render datasheet HTML for preview and browser-based PDF export."""
import os
from datetime import datetime

from jinja2 import Environment, FileSystemLoader

from config import BASE_DIR, TEMPLATE_DIR
from models import ProductBase


def _split_spec_sections(sections: list) -> tuple[list, list]:
    """Split spec sections into left and right columns for the spec page."""
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

    return left, right


def render_html(product: ProductBase, version: str, template_name: str = None) -> str:
    """Render product data into HTML string with URL-based image paths."""
    if template_name is None:
        template_name = f"{product.category.lower()}.html"

    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    template = env.get_template(template_name)

    left_sections, right_sections = _split_spec_sections(product.spec_sections)

    # Use URL paths for images (served via Flask static)
    logo_path = "/static/logo/engenius_cloud_icon.png"
    product_image = ""
    if product.product_image:
        # Convert "cache/images/X.png" or absolute path to "/static/images/X.png"
        img_name = os.path.basename(product.product_image)
        product_image = f"/static/images/{img_name}"
    hardware_image = ""
    if product.hardware_image:
        img_name = os.path.basename(product.hardware_image)
        hardware_image = f"/static/images/{img_name}"

    product_dict = product.model_dump()
    product_dict["product_image"] = product_image
    product_dict["hardware_image"] = hardware_image

    html = template.render(
        product=type(product)(**product_dict),
        logo_path=logo_path,
        left_sections=left_sections,
        right_sections=right_sections,
        version=version,
        date=datetime.now().strftime("%m/%d/%Y"),
    )
    return html
