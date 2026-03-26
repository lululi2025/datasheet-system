"""Read product data from Google Sheets CSV export.

Reads from two tabs:
- Detail Specs tab: technical specifications (vertical layout, models as columns)
- Web Overview tab: model description, overview text, feature lists
"""
import csv
import io
import requests

from models import CameraProduct, SpecSection, SpecItem, HardwareLabel

# Google Sheets config
SHEET_ID = "1jQUW9vvqzWEx-pMfPtSxUhf-Ov81cQzzSx16-YX1wqU"
DETAIL_SPECS_GID = "180970413"
WEB_OVERVIEW_GID = "2086236498"

# Known spec category headers — rows with empty values act as section dividers
SPEC_CATEGORIES = {
    "Optics", "Video", "Audio", "Advanced AI Analytics",
    "Storage", "System", "Mechanical", "Management Software",
}

# Product line config (not in the sheet, set here)
PRODUCT_LINE_MAP = {
    "Cameras": "AI Cloud Cameras",
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


def _fetch_csv(gid: str) -> list[list[str]]:
    """Fetch a Google Sheets tab as CSV and return as list of rows."""
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    reader = csv.reader(io.StringIO(resp.text))
    return list(reader)


def _find_model_column(rows: list[list[str]], model_number: str) -> int | None:
    """Find the column index for a given model number (e.g., 'ECC100')."""
    for row in rows[:5]:  # Model # is in the first few rows
        for col_idx, cell in enumerate(row):
            if cell.strip() == model_number:
                return col_idx
    return None


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

        # Empty label = skip
        if not label:
            continue

        # Check if this is a category header
        if label in SPEC_CATEGORIES:
            # Save previous section
            if current_category and current_items:
                sections.append(SpecSection(category=current_category, items=current_items))
            current_category = label
            current_items = []
            continue

        # Skip rows where value is empty or "-"
        if not value or value == "-":
            continue

        # This is a spec item
        if current_category:
            current_items.append(SpecItem(label=label, value=value))

    # Save last section
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
    # Fallback to PM overview
    if not data["overview"]:
        for row in rows:
            label = row[0].strip() if row else ""
            if "Overview" in label and "Single" not in label:
                val = _get_cell(row, col_idx)
                if val:
                    data["overview"] = val
                    break

    # Features — may be in a single cell with newline-separated "* " entries,
    # or spread across multiple rows
    for row in rows:
        label = row[0].strip() if row else ""
        if "Key Feature Lists" in label or "Key Feature" in label:
            cell_value = _get_cell(row, col_idx)
            if cell_value:
                # Single cell with newline-separated features
                for line in cell_value.split("\n"):
                    line = line.strip()
                    if line.startswith("*"):
                        feature_text = line.lstrip("* ").strip()
                        if feature_text:
                            data["features"].append(feature_text)
            if data["features"]:
                break

    # Fallback: features spread across multiple rows after the header
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


def load_from_sheets(model_number: str) -> CameraProduct:
    """Load complete product data from Google Sheets for a given model number.

    Combines data from Detail Specs tab and Web Overview tab.
    """
    # Fetch both tabs
    detail_rows = _fetch_csv(DETAIL_SPECS_GID)
    overview_rows = _fetch_csv(WEB_OVERVIEW_GID)

    # Find model column in each tab
    detail_col = _find_model_column(detail_rows, model_number)
    if detail_col is None:
        raise ValueError(f"Model '{model_number}' not found in Detail Specs tab")

    overview_col = _find_model_column(overview_rows, model_number)

    # Parse model name from Detail Specs
    model_name_row = detail_rows[1] if len(detail_rows) > 1 else []
    subtitle = _get_cell(model_name_row, detail_col)  # e.g., "Cam5MP Dome IP67 256GB"

    # Parse specs
    spec_sections = _parse_spec_sections(detail_rows, detail_col)

    # Parse overview data
    overview_data = {"model_description": "", "overview": "", "features": []}
    if overview_col is not None:
        overview_data = _parse_overview_data(overview_rows, overview_col)

    full_name = overview_data["model_description"] or f"{subtitle}"

    # Build product
    product = CameraProduct(
        model_name=model_number,
        product_line=PRODUCT_LINE_MAP.get("Cameras", "AI Cloud Cameras"),
        category="Cameras",
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
    """List all EnGenius models available in the Detail Specs tab."""
    detail_rows = _fetch_csv(DETAIL_SPECS_GID)

    models = []
    if len(detail_rows) < 3:
        return models

    model_name_row = detail_rows[1]  # Model Name row
    model_num_row = detail_rows[2]   # Model # row
    type_row = detail_rows[0]        # Type row

    for col_idx in range(1, len(model_num_row)):
        model_num = model_num_row[col_idx].strip()
        model_name = _get_cell(model_name_row, col_idx)
        model_type = _get_cell(type_row, col_idx)

        # Skip empty columns and non-EnGenius models (Vivotek etc.)
        if not model_num or "Vivotek" in model_name:
            continue

        models.append({
            "model_number": model_num,
            "model_name": model_name,
            "type": model_type,
        })

    return models
