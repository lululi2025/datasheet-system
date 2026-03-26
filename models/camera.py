"""Camera product model."""
from .base import ProductBase


class CameraProduct(ProductBase):
    """Camera-specific product model. Extends base with camera fields."""
    category: str = "Cameras"
