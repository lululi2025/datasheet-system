"""Load product data from local JSON or Google Sheets."""
import json
import os

from config import BASE_DIR
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


def list_available_products() -> list[str]:
    """List all products from local JSON and Google Sheets (deduplicated)."""
    # Local JSON files
    data_dir = os.path.join(BASE_DIR, "data")
    local = set()
    if os.path.exists(data_dir):
        local = {
            f.replace(".json", "")
            for f in os.listdir(data_dir)
            if f.endswith(".json")
        }

    # Google Sheets models
    sheets = set()
    try:
        from services.sheets_reader import list_models_from_sheets
        for m in list_models_from_sheets():
            sheets.add(m["model_number"])
    except Exception:
        pass

    return sorted(local | sheets)
