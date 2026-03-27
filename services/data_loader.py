"""Load product data from local JSON or Google Sheets."""
import json
import os

from config import BASE_DIR, PRODUCT_LINES
from models import CameraProduct
from models.base import ProductBase


# Map category names to their Pydantic model classes
PRODUCT_MODELS = {
    "Cameras": CameraProduct,
}


def load_from_json(model_name: str) -> ProductBase:
    """Load product data from a local JSON file."""
    json_path = os.path.join(BASE_DIR, "data", f"{model_name}.json")
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    category = data.get("category", "Cameras")
    model_class = PRODUCT_MODELS.get(category, ProductBase)
    return model_class(**data)


def load_product(model_name: str, source: str = "auto") -> ProductBase:
    """Load product data from the best available source.

    source: "json", "sheets", or "auto" (try JSON first, then Sheets)
    """
    if source == "json":
        return load_from_json(model_name)

    if source == "sheets":
        from services.sheets_reader import load_from_sheets
        return load_from_sheets(model_name)

    # auto: try JSON first, fall back to Sheets
    try:
        return load_from_json(model_name)
    except FileNotFoundError:
        from services.sheets_reader import load_from_sheets
        return load_from_sheets(model_name)


def list_available_products() -> list[dict]:
    """List all products grouped by product line.

    Returns list of dicts with model info and product_line.
    """
    # Local JSON files
    data_dir = os.path.join(BASE_DIR, "data")
    local_models = set()
    if os.path.exists(data_dir):
        local_models = {
            f.replace(".json", "")
            for f in os.listdir(data_dir)
            if f.endswith(".json")
        }

    # Google Sheets models (all product lines)
    all_products = []
    seen = set()
    try:
        from services.sheets_reader import list_models_from_sheets
        for m in list_models_from_sheets():
            model_num = m["model_number"]
            if model_num not in seen:
                seen.add(model_num)
                all_products.append(m)
    except Exception:
        pass

    # Add local-only models (not in any sheet)
    for model_name in local_models:
        if model_name not in seen:
            try:
                p = load_from_json(model_name)
                all_products.append({
                    "model_number": model_name,
                    "model_name": p.subtitle or model_name,
                    "type": "",
                    "product_line": "Local",
                    "category": p.category,
                    "product_line_label": p.product_line,
                })
            except Exception:
                all_products.append({
                    "model_number": model_name,
                    "model_name": model_name,
                    "type": "",
                    "product_line": "Local",
                    "category": "Unknown",
                    "product_line_label": "Local Data",
                })

    return all_products


def get_product_lines() -> list[str]:
    """Return list of all configured product line names."""
    return list(PRODUCT_LINES.keys())
