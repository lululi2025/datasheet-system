"""Fetch product images from Google Drive using Service Account."""
import io
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config import BASE_DIR

# Service Account key file path
_KEY_FILE = os.path.join(BASE_DIR, "service-account-key.json")

# For Vercel: support JSON key from environment variable
_KEY_ENV = "GOOGLE_SERVICE_ACCOUNT_JSON"

# Parent folder IDs for each model (add new models here)
MODEL_FOLDER_IDS = {
    "ECC100": "1Qje0iighD8jaGRkv6Qe4iAEIiwY1nNp4",
    "ECC120": "1SWB05G3btQ6TtHqxhCAb11ow-9RxmqWq",
}

_drive_service = None


def _get_drive_service():
    """Build and return a cached Google Drive API service."""
    global _drive_service
    if _drive_service:
        return _drive_service

    # Try env var first (for Vercel), then local file
    import json
    key_json = os.environ.get(_KEY_ENV)
    if key_json:
        info = json.loads(key_json)
        creds = service_account.Credentials.from_service_account_info(
            info,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
    elif os.path.exists(_KEY_FILE):
        creds = service_account.Credentials.from_service_account_file(
            _KEY_FILE,
            scopes=["https://www.googleapis.com/auth/drive.readonly"],
        )
    else:
        return None

    _drive_service = build("drive", "v3", credentials=creds)
    return _drive_service


def get_image_urls(model_number: str) -> dict[str, str]:
    """Get proxied image URLs for a model.

    Returns Flask route URLs like /drive-image/ECC100/product
    that will stream the image through our server (with auth).
    """
    folder_id = MODEL_FOLDER_IDS.get(model_number)
    if not folder_id:
        return {"product_image": "", "hardware_image": ""}

    drive = _get_drive_service()
    if not drive:
        return {"product_image": "", "hardware_image": ""}

    results = drive.files().list(
        q=f"'{folder_id}' in parents and mimeType contains 'image/'",
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True,
    ).execute()

    files = {f["name"]: f["id"] for f in results.get("files", [])}

    product_name = f"{model_number}_product.png"
    hardware_name = f"{model_number}_hardware.png"

    product_id = files.get(product_name)
    hardware_id = files.get(hardware_name)

    return {
        "product_image": f"/drive-image/{product_id}" if product_id else "",
        "hardware_image": f"/drive-image/{hardware_id}" if hardware_id else "",
    }


def download_file(file_id: str) -> tuple[bytes, str]:
    """Download a file from Google Drive by file ID.

    Returns (file_bytes, mime_type).
    """
    drive = _get_drive_service()
    if not drive:
        raise FileNotFoundError("Google Drive service not available")

    # Get mime type
    meta = drive.files().get(
        fileId=file_id,
        fields="mimeType",
        supportsAllDrives=True,
    ).execute()

    # Download content
    request = drive.files().get_media(
        fileId=file_id,
        supportsAllDrives=True,
    )
    buffer = io.BytesIO()
    from googleapiclient.http import MediaIoBaseDownload
    downloader = MediaIoBaseDownload(buffer, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    return buffer.getvalue(), meta["mimeType"]
