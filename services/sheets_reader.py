"""Read product data from Google Sheets CSV export.

Reads from two tabs per product line:
- Detail Specs tab: technical specifications (vertical layout, models as columns)
- Web Overview tab: model description, overview text, feature lists

Supports multiple product lines (Camera, AP, Switch), each with its own Google Sheet.
"""
import csv
import io
import requests

from config import PRODUCT_LINES
from models import CameraProduct, SpecSection, SpecItem, HardwareLabel
from models.base import ProductBase

# Known spec category headers — rows with empty values act as section dividers
SPEC_CATEGORIES = {
    "Optics", "Video", "Audio", "Advanced AI Analytics",
    "Storage", "System", "Mechanical", "Management Software",
    "General", "Physical", "Interface", "Networking", "Network",
    "Wireless", "Radio", "Performance", "Power", "Environment",
    "Environmental", "Software", "Security", "Layer 2 Features",
    "Layer 3 Features", "Management", "Standards", "Certifications",
    "PoE", "Switching", "Ports", "Port", "LED",
}

# Hardware labels per model (not in sheet, define here for now)
HARDWARE_LABELS_MAP = {
    "ECC100": [
        HardwareLabel(text="Reset Button"), HardwareLabel(text="Lens"),
        HardwareLabel(text="Microphone"), HardwareLabel(text="Light Sensor"),
        HardwareLabel(text="IR LEDs"), HardwareLabel(text="PoE In"),
        HardwareLabel(text="LED Indicator"),
    ],
    "ECC100Z": [
        HardwareLabel(text="Reset Button"), HardwareLabel(text="Lens"),
        HardwareLabel(text="Microphone"), HardwareLabel(text="Light Sensor"),
        HardwareLabel(text="IR LEDs"), HardwareLabel(text="PoE In"),
        HardwareLabel(text="LED Indicator"),
    ],
}


def _fetch_csv(sheet_id: str, gid: str) -> list[list[str]]:
    """Fetch a Google Sheets tab as CSV and return as list of rows."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    text = resp.content.decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


def _find_model_column(rows: list[list[str]], model_number: str) -> int | None:
    """Find the column index for a given model number (e.g., 'ECC100')."""
    for row in rows[:5]:
        for col_idx, cell in enumerate(row):
            if cell.strip() == model_number:
                return col_idx
    return None


def _find_row_by_label(rows: list[list[str]], label: str) -> int | None:
    """Find the row index where column A matches the given label."""
    for i, row in enumerate(rows):
        if row and row[0].strip() == label:
            return i
    return None


def _get_model_num_row(rows: list[list[str]]) -> int:
    """Find which row contains 'Model #' in column A."""
    idx = _find_row_by_label(rows, "Model #")
    return idx if idx is not None else 2  # fallback to row 2


def _get_model_name_row(rows: list[list[str]]) -> int:
    """Find which row contains 'Model Name' in column A."""
    idx = _find_row_by_label(rows, "Model Name")
    return idx if idx is not None else 0  # fallback to row 0


def _get_cell(row: list[str], col_idx: int) -> str:
    """Safely get a cell value."""
    if col_idx < len(row):
        return row[col_idx].strip()
    return ""


def _parse_spec_sections(rows: list[list[str]], col_idx: int) -> list[SpecSection]:
    """Parse technical specification sections from the Detail Specs tab."""
    sections = []
    current_category = None
    current_items = []

    # Find where "Technical Specifications" starts
    start_row = 0
    for i, row in enumerate(rows):
        if row and row[0].strip() == "Technical Specifications":
            start_row = i + 1
            break

    for row in rows[start_row:]:
        label = row[0].strip() if row else ""
        value = _get_cell(row, col_idx)

        if not label:
            continue

        # Check if this is a category header
        if label in SPEC_CATEGORIES:
            if current_category and current_items:
                sections.append(SpecSection(category=current_category, items=current_items))
            current_category = label
            current_items = []
            continue

        # Skip rows where value is empty or "-"
        if not value or value == "-":
            continue

        if current_category:
            current_items.append(SpecItem(label=label, value=value))

    if current_category and current_items:
        sections.append(SpecSection(category=current_category, items=current_items))

    return sections


def _parse_overview_data(rows: list[list[str]], col_idx: int) -> dict:
    """Parse model description, overview, and features from the Web Overview tab."""
    data = {
        "model_description": "",
        "overview": "",
        "features": [],
    }

    row_map = {}
    for i, row in enumerate(rows):
        label = row[0].strip() if row else ""
        row_map[label] = i

    # Model Description
    for label in ["Model Description"]:
        if label in row_map:
            data["model_description"] = _get_cell(rows[row_map[label]], col_idx)

    # Overview — use "Single Overview" (MKT rewrite) if available
    for row in rows:
        label = row[0].strip() if row else ""
        if "Single Overview" in label:
            val = _get_cell(row, col_idx)
            if val:
                data["overview"] = val
                break
    if not data["overview"]:
        for row in rows:
            label = row[0].strip() if row else ""
            if "Overview" in label and "Single" not in label:
                val = _get_cell(row, col_idx)
                if val:
                    data["overview"] = val
                    break

    # Features — may be in a single cell with newline-separated "* " entries
    for row in rows:
        label = row[0].strip() if row else ""
        if "Key Feature Lists" in label or "Key Feature" in label:
            cell_value = _get_cell(row, col_idx)
            if cell_value:
                for line in cell_value.split("\n"):
                    line = line.strip()
                    if line.startswith("*"):
                        feature_text = line.lstrip("* ").strip()
                        if feature_text:
                            data["features"].append(feature_text)
            if data["features"]:
                break

    # Fallback: features spread across multiple rows
    if not data["features"]:
        in_features = False
        for row in rows:
            label = row[0].strip() if row else ""
            if "Key Feature Lists" in label:
                in_features = True
                continue
            if in_features:
                if label.startswith("*"):
                    feature_text = _get_cell(row, col_idx)
                    if not feature_text:
                        feature_text = label
                    feature_text = feature_text.lstrip("* ").strip()
                    if feature_text:
                        data["features"].append(feature_text)
                elif label and not label.startswith("*"):
                    in_features = False

    return data


def _find_product_line(model_number: str) -> dict | None:
    """Find which product line a model belongs to by searching all sheets."""
    for line_name, line_config in PRODUCT_LINES.items():
        try:
            detail_rows = _fetch_csv(line_config["sheet_id"], line_config["detail_specs_gid"])
            col = _find_model_column(detail_rows, model_number)
            if col is not None:
                return {"line_name": line_name, **line_config}
        except Exception:
            continue
    return None


def load_from_sheets(model_number: str, product_line: str = None) -> ProductBase:
    """Load complete product data from Google Sheets for a given model number.

    If product_line is specified, only searches that line's sheet.
    Otherwise searches all sheets to find the model.
    """
    if product_line and product_line in PRODUCT_LINES:
        line_config = PRODUCT_LINES[product_line]
    else:
        line_config = _find_product_line(model_number)
        if line_config is None:
            raise ValueError(f"Model '{model_number}' not found in any product line sheet")
        product_line = line_config.get("line_name", "")

    sheet_id = line_config["sheet_id"]

    # Fetch both tabs
    detail_rows = _fetch_csv(sheet_id, line_config["detail_specs_gid"])
    overview_rows = _fetch_csv(sheet_id, line_config["overview_gid"])

    # Find model column
    detail_col = _find_model_column(detail_rows, model_number)
    if detail_col is None:
        raise ValueError(f"Model '{model_number}' not found in Detail Specs tab")

    overview_col = _find_model_column(overview_rows, model_number)

    # Parse model name from Detail Specs (row position varies by sheet)
    name_row_idx = _get_model_name_row(detail_rows)
    model_name_row = detail_rows[name_row_idx] if name_row_idx < len(detail_rows) else []
    subtitle = _get_cell(model_name_row, detail_col)

    # Parse specs
    spec_sections = _parse_spec_sections(detail_rows, detail_col)

    # Parse overview data
    overview_data = {"model_description": "", "overview": "", "features": []}
    if overview_col is not None:
        overview_data = _parse_overview_data(overview_rows, overview_col)

    full_name = overview_data["model_description"] or subtitle

    category = line_config.get("category", "Cameras")
    product_line_label = line_config.get("product_line_label", product_line)

    product = ProductBase(
        model_name=model_number,
        product_line=product_line_label,
        category=category,
        subtitle=subtitle,
        full_name=full_name,
        overview=overview_data["overview"],
        features=overview_data["features"],
        spec_sections=spec_sections,
        hardware_labels=HARDWARE_LABELS_MAP.get(model_number, []),
        product_image=f"cache/images/{model_number}_product.png",
        hardware_image=f"cache/images/{model_number}_hardware.png",
    )

    return product


def list_models_from_sheets() -> list[dict]:
    """List all models from ALL product line sheets."""
    all_models = []

    for line_name, line_config in PRODUCT_LINES.items():
        try:
            detail_rows = _fetch_csv(line_config["sheet_id"], line_config["detail_specs_gid"])
        except Exception:
            continue

        if len(detail_rows) < 2:
            continue

        # Find row positions dynamically (varies by sheet)
        num_row_idx = _get_model_num_row(detail_rows)
        name_row_idx = _get_model_name_row(detail_rows)
        model_num_row = detail_rows[num_row_idx] if num_row_idx < len(detail_rows) else []

        for col_idx in range(1, len(model_num_row)):
            model_num = model_num_row[col_idx].strip()
            model_name = _get_cell(detail_rows[name_row_idx], col_idx) if name_row_idx < len(detail_rows) else ""

            if not model_num or "Vivotek" in model_name:
                continue

            all_models.append({
                "model_number": model_num,
                "model_name": model_name,
                "type": "",
                "product_line": line_name,
                "category": line_config["category"],
                "product_line_label": line_config["product_line_label"],
            })

    return all_models
