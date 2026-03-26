"""Base Pydantic models shared across product lines."""
from pydantic import BaseModel


class SpecItem(BaseModel):
    """A single spec row: label + value."""
    label: str
    value: str


class SpecSection(BaseModel):
    """A group of specs under a category header (e.g., Optics, Video)."""
    category: str
    items: list[SpecItem]


class HardwareLabel(BaseModel):
    """A label pointing to a part on the hardware overview image."""
    text: str
    position: str = ""  # e.g., "top-left", "right" (used for CSS positioning)


class ProductBase(BaseModel):
    """Base product model. All product lines extend this."""
    model_name: str  # e.g., "ECC100"
    product_line: str  # e.g., "AI Cloud Cameras"
    category: str  # e.g., "Cameras"
    subtitle: str  # e.g., "Cam5MP Dome IP67"
    full_name: str  # e.g., "Cloud Managed AI Outdoor Dome with 256GB Storage"
    overview: str  # Product description paragraph
    features: list[str]  # Bullet point features
    spec_sections: list[SpecSection]  # Technical specifications
    hardware_labels: list[HardwareLabel] = []  # Hardware overview annotations

    # Image references (Google Drive file IDs or local paths)
    product_image: str = ""
    hardware_image: str = ""
