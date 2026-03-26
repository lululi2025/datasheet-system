"""Image processing utilities for datasheet generation."""
import io

from PIL import Image


def auto_trim(image_data: bytes, padding: int = 8) -> bytes:
    """Auto-crop whitespace/transparent borders from an image.

    Detects the bounding box of actual content and crops to it,
    keeping a small padding around the edges.

    Args:
        image_data: Raw image bytes (PNG/JPG).
        padding: Pixels of padding to keep around the content.

    Returns:
        Cropped image as PNG bytes.
    """
    img = Image.open(io.BytesIO(image_data))

    # Convert to RGBA to handle both white and transparent backgrounds
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    # Get bounding box of non-transparent content
    bbox = img.getbbox()

    if bbox is None:
        # Image is fully transparent or empty, return as-is
        return image_data

    # Check if trimming would actually help (>10% padding on any side)
    w, h = img.size
    content_w = bbox[2] - bbox[0]
    content_h = bbox[3] - bbox[1]

    # Only trim if content is less than 85% of the image
    if content_w * content_h > 0.85 * w * h:
        return image_data

    # Add padding (but don't exceed image bounds)
    x1 = max(0, bbox[0] - padding)
    y1 = max(0, bbox[1] - padding)
    x2 = min(w, bbox[2] + padding)
    y2 = min(h, bbox[3] + padding)

    cropped = img.crop((x1, y1, x2, y2))

    buf = io.BytesIO()
    cropped.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
