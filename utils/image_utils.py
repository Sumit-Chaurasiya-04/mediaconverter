# utils/image_utils.py
# All image processing functions go here
# Pillow (PIL) is the main library we use for images

import os
import io
import logging
from pathlib import Path
from typing import Optional, Tuple, List
import numpy as np

# Pillow is the main image processing library
from PIL import Image, ImageFilter, ImageEnhance, ImageDraw, ImageFont, ImageOps

# OpenCV for advanced operations
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    logging.warning("OpenCV not available. Some features will be limited.")

# Background remover (requires rembg package)
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False
    logging.warning("rembg not available. Background removal disabled.")

# img2pdf for image to PDF conversion
try:
    import img2pdf
    IMG2PDF_AVAILABLE = True
except ImportError:
    IMG2PDF_AVAILABLE = False

from utils.file_utils import generate_output_path

logger = logging.getLogger(__name__)


# ============================================================
# FORMAT CONVERSION
# ============================================================

def convert_image_format(
    input_path: str,
    output_format: str,
    quality: int = 85
) -> Optional[str]:
    """
    Convert an image from one format to another.
    
    Parameters:
        input_path: Path to the original image
        output_format: Target format like "png", "jpg", "webp"
        quality: Image quality 1-100 (higher = better quality, larger file)
    
    Returns:
        Path to the converted image, or None if failed
    
    Example:
        output = convert_image_format("/tmp/photo.jpg", "png")
        # Converts photo.jpg to photo.png
    """
    try:
        # Open the image using Pillow
        img = Image.open(input_path)
        
        # IMPORTANT: Convert to RGB if saving as JPEG
        # JPEG doesn't support transparency (alpha channel)
        # PNG, WEBP do support transparency
        if output_format.lower() in ["jpg", "jpeg"]:
            # If image has transparency, add white background
            if img.mode in ("RGBA", "LA", "P"):
                background = Image.new("RGB", img.size, (255, 255, 255))
                if img.mode == "P":
                    img = img.convert("RGBA")
                background.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                img = background
            else:
                img = img.convert("RGB")
        
        # For ICO format, resize to standard icon size
        if output_format.lower() == "ico":
            img = img.resize((256, 256), Image.LANCZOS)
        
        # Generate output file path
        output_path = generate_output_path(input_path, output_format)
        
        # Save the image in the new format
        save_kwargs = {}
        if output_format.lower() in ["jpg", "jpeg", "webp"]:
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = True
        elif output_format.lower() == "png":
            # PNG compression level 0-9 (9 = smallest file, slowest)
            save_kwargs["optimize"] = True
        elif output_format.lower() == "tiff":
            save_kwargs["compression"] = "lzw"
        
        img.save(output_path, format=output_format.upper(), **save_kwargs)
        
        logger.info(f"Image converted: {input_path} -> {output_path}")
        return output_path
        
    except Exception as e:
        logger.error(f"Image conversion error: {e}")
        return None


# ============================================================
# IMAGE COMPRESSION
# ============================================================

def compress_image(
    input_path: str,
    quality: int = 60,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None
) -> Optional[str]:
    """
    Compress an image to reduce file size.
    
    Parameters:
        input_path: Path to original image
        quality: Quality level 1-100 (lower = smaller file)
        max_width: Maximum width in pixels (None = keep original)
        max_height: Maximum height in pixels (None = keep original)
    
    Returns:
        Path to compressed image
    """
    try:
        img = Image.open(input_path)
        original_format = img.format or "JPEG"
        
        # Resize if needed (maintaining aspect ratio)
        if max_width or max_height:
            img = resize_image_maintain_ratio(img, max_width, max_height)
        
        # Get the original file extension
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_compressed")
        
        # Convert to RGB if JPEG
        if ext in ["jpg", "jpeg"] and img.mode != "RGB":
            img = img.convert("RGB")
        
        # Save with compression
        if ext in ["jpg", "jpeg"]:
            img.save(output_path, "JPEG", quality=quality, optimize=True, progressive=True)
        elif ext == "webp":
            img.save(output_path, "WEBP", quality=quality, method=6)
        elif ext == "png":
            img.save(output_path, "PNG", optimize=True, compress_level=9)
        else:
            img.save(output_path, quality=quality, optimize=True)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Image compression error: {e}")
        return None


# ============================================================
# IMAGE RESIZING
# ============================================================

def resize_image(
    input_path: str,
    width: int,
    height: int,
    maintain_ratio: bool = True
) -> Optional[str]:
    """
    Resize an image to specific dimensions.
    
    Parameters:
        input_path: Path to original image
        width: Target width in pixels
        height: Target height in pixels
        maintain_ratio: If True, keeps original proportions
    
    Returns:
        Path to resized image
    """
    try:
        img = Image.open(input_path)
        
        if maintain_ratio:
            img = resize_image_maintain_ratio(img, width, height)
        else:
            img = img.resize((width, height), Image.LANCZOS)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_resized")
        
        # Convert to RGB if saving as JPEG
        if ext in ["jpg", "jpeg"] and img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode in ("RGBA", "LA"):
                bg.paste(img, mask=img.split()[-1])
            else:
                bg.paste(img)
            img = bg
        
        img.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image resize error: {e}")
        return None


def resize_image_maintain_ratio(
    img: Image.Image,
    max_width: Optional[int],
    max_height: Optional[int]
) -> Image.Image:
    """
    Resize image while maintaining aspect ratio.
    This is a helper function used by other functions.
    """
    original_width, original_height = img.size
    
    if max_width is None and max_height is None:
        return img
    
    # Calculate scaling factor
    if max_width and max_height:
        # Fit within both dimensions
        ratio_w = max_width / original_width
        ratio_h = max_height / original_height
        ratio = min(ratio_w, ratio_h)
    elif max_width:
        ratio = max_width / original_width
    else:
        ratio = max_height / original_height
    
    # Don't upscale (only shrink)
    if ratio >= 1.0:
        return img
    
    new_width = int(original_width * ratio)
    new_height = int(original_height * ratio)
    
    return img.resize((new_width, new_height), Image.LANCZOS)


# ============================================================
# IMAGE CROPPING
# ============================================================

def crop_image(
    input_path: str,
    left: int,
    top: int,
    right: int,
    bottom: int
) -> Optional[str]:
    """
    Crop an image to a specific region.
    
    Parameters:
        left, top: Top-left corner coordinates
        right, bottom: Bottom-right corner coordinates
    
    Example:
        crop_image("photo.jpg", 100, 50, 400, 300)
        # Crops a 300x250 region starting at (100, 50)
    """
    try:
        img = Image.open(input_path)
        
        # Ensure crop coordinates are within image bounds
        w, h = img.size
        left = max(0, min(left, w))
        top = max(0, min(top, h))
        right = max(left + 1, min(right, w))
        bottom = max(top + 1, min(bottom, h))
        
        cropped = img.crop((left, top, right, bottom))
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_cropped")
        
        cropped.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image crop error: {e}")
        return None


# ============================================================
# IMAGE ROTATION & FLIP
# ============================================================

def rotate_image(input_path: str, angle: int, expand: bool = True) -> Optional[str]:
    """
    Rotate an image by a specific angle.
    
    Parameters:
        angle: Rotation angle in degrees (positive = counter-clockwise)
        expand: If True, resize canvas to fit rotated image
    """
    try:
        img = Image.open(input_path)
        rotated = img.rotate(angle, expand=expand, resample=Image.BICUBIC)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_rotated")
        
        rotated.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image rotation error: {e}")
        return None


def flip_image(input_path: str, direction: str = "horizontal") -> Optional[str]:
    """
    Flip an image horizontally or vertically.
    
    Parameters:
        direction: "horizontal" or "vertical"
    """
    try:
        img = Image.open(input_path)
        
        if direction == "horizontal":
            flipped = ImageOps.mirror(img)
        else:
            flipped = ImageOps.flip(img)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_flipped")
        
        flipped.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image flip error: {e}")
        return None


# ============================================================
# IMAGE ENHANCEMENT
# ============================================================

def adjust_brightness_contrast(
    input_path: str,
    brightness: float = 1.0,
    contrast: float = 1.0,
    saturation: float = 1.0,
    sharpness: float = 1.0
) -> Optional[str]:
    """
    Adjust image brightness, contrast, saturation, and sharpness.
    
    Parameters (all default to 1.0 = no change):
        brightness: 0.0 = black, 1.0 = original, 2.0 = double bright
        contrast: 0.0 = gray, 1.0 = original, 2.0 = high contrast
        saturation: 0.0 = grayscale, 1.0 = original, 2.0 = vivid
        sharpness: 0.0 = blurry, 1.0 = original, 2.0 = sharp
    """
    try:
        img = Image.open(input_path)
        
        # Apply each enhancement
        if brightness != 1.0:
            img = ImageEnhance.Brightness(img).enhance(brightness)
        
        if contrast != 1.0:
            img = ImageEnhance.Contrast(img).enhance(contrast)
        
        if saturation != 1.0:
            img = ImageEnhance.Color(img).enhance(saturation)
        
        if sharpness != 1.0:
            img = ImageEnhance.Sharpness(img).enhance(sharpness)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_enhanced")
        
        # Save with original quality for non-JPEG
        if ext in ["jpg", "jpeg"] and img.mode != "RGB":
            img = img.convert("RGB")
        
        img.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image enhancement error: {e}")
        return None


def sharpen_image(input_path: str, strength: str = "medium") -> Optional[str]:
    """
    Sharpen a blurry image.
    
    Parameters:
        strength: "light", "medium", or "strong"
    """
    try:
        img = Image.open(input_path)
        
        # Apply sharpening filter based on strength
        if strength == "light":
            sharpened = img.filter(ImageFilter.SHARPEN)
        elif strength == "medium":
            sharpened = img.filter(ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3))
        else:  # strong
            sharpened = img.filter(ImageFilter.UnsharpMask(radius=3, percent=200, threshold=2))
            sharpened = sharpened.filter(ImageFilter.SHARPEN)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_sharpened")
        
        if ext in ["jpg", "jpeg"] and sharpened.mode != "RGB":
            sharpened = sharpened.convert("RGB")
        
        sharpened.save(output_path)
        return output_path
        
    except Exception as e:
        logger.error(f"Image sharpening error: {e}")
        return None


def convert_to_grayscale(input_path: str) -> Optional[str]:
    """Convert image to black and white (grayscale)."""
    try:
        img = Image.open(input_path)
        grayscale = ImageOps.grayscale(img)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_grayscale")
        
        if ext in ["jpg", "jpeg"]:
            grayscale.save(output_path, "JPEG", quality=90)
        else:
            grayscale.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Grayscale conversion error: {e}")
        return None


# ============================================================
# WATERMARK
# ============================================================

def add_text_watermark(
    input_path: str,
    watermark_text: str,
    position: str = "bottom-right",
    opacity: int = 50,
    font_size: int = 36,
    color: str = "white"
) -> Optional[str]:
    """
    Add a text watermark to an image.
    
    Parameters:
        watermark_text: The text to add as watermark
        position: Where to place it ("center", "bottom-right", "bottom-left", etc.)
        opacity: Transparency 0-100 (0=invisible, 100=fully visible)
        font_size: Size of the watermark text
        color: Text color ("white", "black", "red", etc.)
    """
    try:
        # Open base image and convert to RGBA for transparency support
        img = Image.open(input_path).convert("RGBA")
        
        # Create a transparent overlay for the watermark
        watermark_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark_layer)
        
        # Try to use a nice font, fall back to default if not available
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            try:
                font = ImageFont.load_default()
            except:
                font = None
        
        # Calculate text size
        if font:
            bbox = draw.textbbox((0, 0), watermark_text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
        else:
            text_width = len(watermark_text) * 10
            text_height = 20
        
        # Calculate position
        img_width, img_height = img.size
        padding = 20
        
        position_map = {
            "top-left": (padding, padding),
            "top-right": (img_width - text_width - padding, padding),
            "bottom-left": (padding, img_height - text_height - padding),
            "bottom-right": (img_width - text_width - padding, img_height - text_height - padding),
            "center": ((img_width - text_width) // 2, (img_height - text_height) // 2)
        }
        
        x, y = position_map.get(position, position_map["bottom-right"])
        
        # Convert opacity (0-100) to alpha (0-255)
        alpha = int(opacity * 2.55)
        
        # Draw text with shadow for better visibility
        color_map = {
            "white": (255, 255, 255, alpha),
            "black": (0, 0, 0, alpha),
            "red": (255, 0, 0, alpha),
            "yellow": (255, 255, 0, alpha),
            "blue": (0, 0, 255, alpha)
        }
        
        fill_color = color_map.get(color.lower(), (255, 255, 255, alpha))
        
        # Draw shadow first (offset by 2 pixels)
        shadow_color = (0, 0, 0, alpha // 2)
        draw.text((x + 2, y + 2), watermark_text, font=font, fill=shadow_color)
        
        # Draw main text
        draw.text((x, y), watermark_text, font=font, fill=fill_color)
        
        # Merge watermark with original image
        output_img = Image.alpha_composite(img, watermark_layer)
        
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_watermarked")
        
        # Convert back if saving as JPEG (no transparency support)
        if ext in ["jpg", "jpeg"]:
            output_img = output_img.convert("RGB")
            output_img.save(output_path, "JPEG", quality=90)
        else:
            output_img.save(output_path)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        return None


# ============================================================
# BACKGROUND REMOVAL
# ============================================================

def remove_background(input_path: str) -> Optional[str]:
    """
    Remove background from an image using AI (rembg library).
    The removed background becomes transparent.
    Works best on images with clear subjects.
    
    Note: Requires 'rembg' to be installed and first run downloads AI model (~170MB)
    """
    if not REMBG_AVAILABLE:
        logger.error("rembg library not available")
        return None
    
    try:
        # Read input image
        with open(input_path, "rb") as f:
            input_data = f.read()
        
        # Remove background (this uses AI)
        output_data = rembg_remove(input_data)
        
        # Save as PNG (to preserve transparency)
        output_path = generate_output_path(input_path, "png", "_nobg")
        
        with open(output_path, "wb") as f:
            f.write(output_data)
        
        return output_path
        
    except Exception as e:
        logger.error(f"Background removal error: {e}")
        return None


# ============================================================
# IMAGE TO PDF
# ============================================================

def image_to_pdf(input_paths: List[str]) -> Optional[str]:
    """
    Convert one or multiple images to a single PDF file.
    
    Parameters:
        input_paths: List of image file paths (can be just one)
    
    Returns:
        Path to the generated PDF file
    """
    try:
        if IMG2PDF_AVAILABLE:
            # Use img2pdf for perfect quality conversion
            output_path = generate_output_path(input_paths[0], "pdf")
            
            # Convert all images to PDF
            with open(output_path, "wb") as f:
                f.write(img2pdf.convert(input_paths))
            
            return output_path
        else:
            # Fallback using Pillow
            images = []
            for path in input_paths:
                img = Image.open(path)
                if img.mode != "RGB":
                    img = img.convert("RGB")
                images.append(img)
            
            output_path = generate_output_path(input_paths[0], "pdf")
            
            if len(images) == 1:
                images[0].save(output_path, "PDF")
            else:
                images[0].save(output_path, "PDF", save_all=True, append_images=images[1:])
            
            return output_path
            
    except Exception as e:
        logger.error(f"Image to PDF error: {e}")
        return None


# ============================================================
# GET IMAGE INFO
# ============================================================

def get_image_info(input_path: str) -> dict:
    """
    Get detailed information about an image.
    Returns a dictionary with width, height, format, mode, etc.
    """
    try:
        img = Image.open(input_path)
        info = {
            "width": img.width,
            "height": img.height,
            "format": img.format or "Unknown",
            "mode": img.mode,
            "size_px": f"{img.width} × {img.height}",
            "has_transparency": img.mode in ("RGBA", "LA", "P"),
            "megapixels": round((img.width * img.height) / 1_000_000, 2)
        }
        img.close()
        return info
    except Exception as e:
        logger.error(f"Error getting image info: {e}")
        return {}