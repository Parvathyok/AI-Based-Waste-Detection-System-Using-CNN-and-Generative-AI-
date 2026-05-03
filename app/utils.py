"""
utils.py — Image preprocessing helpers for WasteWise AI
"""

import io
import os
import uuid
import logging
from PIL import Image

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif", "bmp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB


def allowed_file(filename: str) -> bool:
    """Check if the file extension is permitted."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def load_image_from_bytes(data: bytes) -> Image.Image:
    """
    Load a PIL Image from raw bytes.
    Raises ValueError for invalid image data.
    """
    try:
        img = Image.open(io.BytesIO(data))
        img.load()  # Force decode to catch corrupt files
        return img
    except Exception as exc:
        raise ValueError(f"Cannot decode image: {exc}") from exc


def save_upload(image: Image.Image, upload_dir: str) -> str:
    """
    Save an uploaded image to disk with a UUID filename.
    Returns the saved file path.
    """
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"{uuid.uuid4().hex}.jpg"
    path = os.path.join(upload_dir, filename)
    image.convert("RGB").save(path, "JPEG", quality=85)
    return path


def format_confidence(confidence: float) -> str:
    """Format confidence as a percentage string."""
    return f"{confidence * 100:.1f}%"
