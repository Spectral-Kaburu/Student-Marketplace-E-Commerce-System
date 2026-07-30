import io
import logging
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

logger = logging.getLogger(__name__)

# Max bounding box dimensions. Images smaller than this won't be stretched up;
# images larger will be scaled down proportionally (no cropping, no letterboxing).
MAX_DIMENSION = (1200, 1200)
JPEG_QUALITY = 80


def process_image(image_field_file, max_size=MAX_DIMENSION, quality=JPEG_QUALITY, background_color=(255, 255, 255)):
    """
    Downscales an image to fit within `max_size` while maintaining its exact original
    aspect ratio (no canvas padding/letterboxing, no cropping). Compresses the output to JPEG.

    Returns a ContentFile ready to be saved in Django.
    """
    if not image_field_file:
        return None

    try:
        image_field_file.seek(0)
        img = Image.open(image_field_file)
        img.load()
    except (UnidentifiedImageError, OSError) as exc:
        logger.warning("Failed to decode uploaded image: %s", exc)
        raise ValidationError("Uploaded file is not a valid image.") from exc

    # 1. Correct EXIF rotation (phone cameras)
    img = ImageOps.exif_transpose(img)

    # 2. Convert color modes for JPEG compatibility (handle transparent PNGs)
    if img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", img.size, background_color)
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode == "P":
        img = img.convert("RGBA")
        background = Image.new("RGB", img.size, background_color)
        background.paste(img, mask=img.split()[-1])
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # 3. Downscale proportionally to fit within max bounds (only shrinks, never stretches up)
    img.thumbnail(max_size, Image.LANCZOS)

    # 4. Save optimized JPEG buffer
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=quality, optimize=True)
    buffer.seek(0)

    return ContentFile(buffer.read())


def processed_filename(original_name):
    """Ensures file extension is .jpg to match output format."""
    stem = Path(original_name).stem or "image"
    return f"{stem}.jpg"