# utils/smart_compress.py
# Binary-search compression engine — finds highest quality under a target KB

import io
from PIL import Image


def compress_to_target_kb(
    pil_image: Image.Image,
    target_kb: int,
    output_format: str = "JPEG",
    max_iterations: int = 10,
) -> tuple[bytes, int, bool]:
    """
    Binary-search the highest Pillow quality that keeps file size under target_kb.

    Returns:
        (image_bytes, quality_used, success)
        success=False means even quality=1 exceeded the target.
    """
    target_bytes = target_kb * 1024

    # Work on a copy so we never mutate the caller's image
    img = pil_image.copy()

    # JPEG / WebP don't support alpha — flatten to white background
    if output_format in ("JPEG",) and img.mode in ("RGBA", "LA", "P"):
        bg = Image.new("RGB", img.size, (255, 255, 255))
        if img.mode == "P":
            img = img.convert("RGBA")
        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
        img = bg
    elif img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    low, high = 1, 95
    best_bytes = None
    best_quality = 1

    for _ in range(max_iterations):
        if low > high:
            break

        mid = (low + high) // 2
        buf = io.BytesIO()

        save_kwargs = {"format": output_format, "quality": mid, "optimize": True}
        if output_format == "JPEG":
            save_kwargs["progressive"] = True

        img.save(buf, **save_kwargs)
        size = buf.tell()

        if size <= target_bytes:
            best_bytes = buf.getvalue()
            best_quality = mid
            low = mid + 1          # try higher quality
        else:
            high = mid - 1         # too big, go lower

    if best_bytes is None:
        # Even quality=1 is too large — return it anyway so caller can warn
        buf = io.BytesIO()
        img.save(buf, format=output_format, quality=1, optimize=True)
        return buf.getvalue(), 1, False

    return best_bytes, best_quality, True


def suggest_resize_dimensions(
    pil_image: Image.Image,
    target_kb: int,
    output_format: str = "JPEG",
) -> tuple[int, int]:
    """
    Estimate width/height needed to fit under target_kb at quality=85.
    Uses area scaling: new_area = old_area * (target / current_size).
    """
    import math

    buf = io.BytesIO()
    img = pil_image.copy()
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img.save(buf, format=output_format, quality=85)
    current_bytes = buf.tell()

    target_bytes = target_kb * 1024
    ratio = math.sqrt(target_bytes / current_bytes)
    ratio = min(ratio, 1.0)   # never upscale

    new_w = max(1, int(pil_image.width * ratio))
    new_h = max(1, int(pil_image.height * ratio))
    return new_w, new_h