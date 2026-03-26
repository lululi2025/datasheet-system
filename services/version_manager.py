"""Version management for generated datasheets."""
import json
import os
from datetime import datetime

from config import VERSIONS_FILE, OUTPUT_DIR


def _load_versions() -> dict:
    if os.path.exists(VERSIONS_FILE):
        with open(VERSIONS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_versions(data: dict):
    os.makedirs(os.path.dirname(VERSIONS_FILE), exist_ok=True)
    with open(VERSIONS_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_current_version(model_name: str) -> str | None:
    versions = _load_versions()
    entry = versions.get(model_name)
    if entry:
        return entry["current_version"]
    return None


def get_history(model_name: str) -> list[dict]:
    versions = _load_versions()
    entry = versions.get(model_name)
    if entry:
        return entry.get("history", [])
    return []


def get_all_products() -> dict:
    return _load_versions()


def bump_version(model_name: str, changes: str = "", major: bool = False) -> str:
    """Increment version and record history. Returns new version string."""
    versions = _load_versions()
    entry = versions.get(model_name)

    if entry is None:
        new_version = "1.0"
    else:
        current = entry["current_version"]
        major_v, minor_v = current.split(".")
        if major:
            new_version = f"{int(major_v) + 1}.0"
        else:
            new_version = f"{major_v}.{int(minor_v) + 1}"

    # Build output path
    model_dir = os.path.join(OUTPUT_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    pdf_filename = f"DS_{model_name}_v{new_version}.pdf"
    pdf_path = os.path.join(model_dir, pdf_filename)

    # Record history
    history_entry = {
        "version": new_version,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "changes": changes or ("Initial release" if new_version == "1.0" else "Updated"),
        "file": pdf_path,
    }

    if model_name not in versions:
        versions[model_name] = {"current_version": new_version, "history": []}

    versions[model_name]["current_version"] = new_version
    versions[model_name]["history"].append(history_entry)
    _save_versions(versions)

    return new_version


def get_output_path(model_name: str, version: str) -> str:
    model_dir = os.path.join(OUTPUT_DIR, model_name)
    os.makedirs(model_dir, exist_ok=True)
    return os.path.join(model_dir, f"DS_{model_name}_v{version}.pdf")
