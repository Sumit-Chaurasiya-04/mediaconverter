# pages/1_🖼️_Image_Converter.py

import streamlit as st
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MAX_IMAGE_SIZE_BYTES, SUPPORTED_IMAGE_FORMATS,
    IMAGE_QUALITY_OPTIONS, APP_NAME
)
from utils.file_utils import (
    save_uploaded_file, validate_file_size,
    get_file_size_formatted, create_download_button, cleanup_file
)
from utils.image_utils import (
    convert_image_format, compress_image, resize_image,
    rotate_image, flip_image, adjust_brightness_contrast,
    sharpen_image, convert_to_grayscale, add_text_watermark,
    image_to_pdf, get_image_info, crop_image
)

# Safe rembg import — works locally, gracefully disabled on cloud
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# ── PAGE SETUP ──────────────────────────────────────────────────
st.set_page_config(
    page_title=f"Image Converter - {APP_NAME}",
    page_icon="🖼️",
    layout="wide"
)

def load_css():
    css_path = os.path.join(Path(__file__).parent.parent, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

def get_file_size_str(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f} MB"

# ── PAGE HEADER ─────────────────────────────────────────────────
st.markdown("""
<div style='background: linear-gradient(135deg, #6C63FF 0%, #FF6584 100%);
     border-radius: 16px; padding: 2rem; text-align: center; margin-bottom: 2rem;'>
    <h1 style='color: white; font-size: 2.5rem; margin: 0;'>🖼️ Image Converter</h1>
    <p style='color: rgba(255,255,255,0.85); margin: 0.5rem 0 0;'>
        Convert, compress, resize, enhance, and process images
    </p>
</div>
""", unsafe_allow_html=True)

# ── TABS ────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "🔄 Convert Format",
    "📦 Compress",
    "📐 Resize",
    "✂️ Crop & Rotate",
    "✨ Enhance",
    "💧 Watermark",
    "🎨 Grayscale",
    "🪄 Remove BG",
    "📄 To PDF"
])

# ── TAB 1: FORMAT CONVERSION ─────────────────────────────────────
with tab1:
    st.markdown("#### Convert image from one format to another")

    uploaded_file = st.file_uploader(
        "Upload your image",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "gif", "ico"],
        key="convert_upload"
    )

    if uploaded_file is not None:
        is_valid, error_msg = validate_file_size(uploaded_file, MAX_IMAGE_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_file, caption="Original Image", use_container_width=True)
                st.markdown(f"**Size:** {get_file_size_str(len(uploaded_file.getbuffer()))}")

            with col2:
                current_ext = Path(uploaded_file.name).suffix.lower().lstrip(".")
                target_formats = ["png", "jpg", "webp", "bmp", "tiff", "gif", "ico"]
                if current_ext in target_formats:
                    target_formats.remove(current_ext)

                target_format = st.selectbox(
                    "Convert to:",
                    target_formats,
                    format_func=lambda x: x.upper(),
                    key="convert_format"
                )

                quality = 85
                if target_format in ["jpg", "jpeg", "webp"]:
                    quality_label = st.select_slider(
                        "Quality",
                        options=list(IMAGE_QUALITY_OPTIONS.keys()),
                        value="High",
                        key="convert_quality"
                    )
                    quality = IMAGE_QUALITY_OPTIONS[quality_label]

                if st.button("🔄 Convert Image", key="btn_convert", use_container_width=True):
                    with st.spinner(f"Converting to {target_format.upper()}..."):
                        saved_path = save_uploaded_file(uploaded_file)
                        if saved_path:
                            output_path = convert_image_format(saved_path, target_format, quality)
                            if output_path and os.path.exists(output_path):
                                original_size = len(uploaded_file.getbuffer())
                                converted_size = os.path.getsize(output_path)
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Original", get_file_size_str(original_size))
                                with col_b:
                                    st.metric("Converted", get_file_size_str(converted_size))
                                create_download_button(
                                    output_path,
                                    f"⬇️ Download {target_format.upper()}",
                                    f"{Path(uploaded_file.name).stem}.{target_format}"
                                )
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Conversion failed.")
                        else:
                            st.error("❌ Failed to save uploaded file.")

# ── TAB 2: COMPRESSION ───────────────────────────────────────────
with tab2:
    st.markdown("#### Reduce image file size")

    uploaded_compress = st.file_uploader(
        "Upload image to compress",
        type=["jpg", "jpeg", "png", "webp"],
        key="compress_upload"
    )

    if uploaded_compress is not None:
        is_valid, error_msg = validate_file_size(uploaded_compress, MAX_IMAGE_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_compress, caption="Original", use_container_width=True)

            with col2:
                quality = st.slider(
                    "Quality Level",
                    min_value=10, max_value=95, value=60,
                    key="compress_quality"
                )

                if quality < 30:
                    st.warning("⚠️ Very low quality")
                elif quality < 60:
                    st.info("📌 Good compression")
                else:
                    st.success("✅ High quality")

                resize_option = st.checkbox("Also resize?", key="compress_resize")
                max_width = None
                max_height = None

                if resize_option:
                    max_width = st.number_input("Max Width (px)", min_value=100, value=1920, key="comp_w")
                    max_height = st.number_input("Max Height (px)", min_value=100, value=1080, key="comp_h")

                if st.button("📦 Compress Image", key="btn_compress", use_container_width=True):
                    with st.spinner("Compressing..."):
                        saved_path = save_uploaded_file(uploaded_compress)
                        if saved_path:
                            output_path = compress_image(saved_path, quality, max_width, max_height)
                            if output_path and os.path.exists(output_path):
                                original_size = len(uploaded_compress.getbuffer())
                                compressed_size = os.path.getsize(output_path)
                                reduction = (1 - compressed_size / original_size) * 100
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Original", get_file_size_str(original_size))
                                with col_b:
                                    st.metric("Compressed", get_file_size_str(compressed_size))
                                with col_c:
                                    st.metric("Reduction", f"{reduction:.1f}%")
                                create_download_button(output_path, "⬇️ Download Compressed Image")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Compression failed.")

# ── TAB 3: RESIZE ────────────────────────────────────────────────
with tab3:
    st.markdown("#### Resize image to specific dimensions")

    uploaded_resize = st.file_uploader(
        "Upload image to resize",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        key="resize_upload"
    )

    if uploaded_resize is not None:
        is_valid, error_msg = validate_file_size(uploaded_resize, MAX_IMAGE_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            from PIL import Image as PILImage
            import io

            img_bytes = uploaded_resize.getvalue()
            pil_img = PILImage.open(io.BytesIO(img_bytes))
            orig_w, orig_h = pil_img.size

            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_resize, caption=f"Original: {orig_w}×{orig_h}px", use_container_width=True)

            with col2:
                preset_sizes = {
                    "Custom": None,
                    "HD (1280×720)": (1280, 720),
                    "Full HD (1920×1080)": (1920, 1080),
                    "Profile Photo (400×400)": (400, 400),
                    "Instagram Post (1080×1080)": (1080, 1080),
                    "Thumbnail (320×240)": (320, 240),
                    "Icon (64×64)": (64, 64),
                }

                preset = st.selectbox("Quick presets:", list(preset_sizes.keys()), key="resize_preset")

                if preset == "Custom" or preset_sizes[preset] is None:
                    target_width = st.number_input("Width (px)", min_value=1, value=orig_w, key="resize_w")
                    target_height = st.number_input("Height (px)", min_value=1, value=orig_h, key="resize_h")
                else:
                    target_width, target_height = preset_sizes[preset]
                    st.info(f"Will resize to: {target_width} × {target_height} pixels")

                maintain_ratio = st.checkbox("Maintain aspect ratio", value=True, key="resize_ratio")

                if st.button("📐 Resize Image", key="btn_resize", use_container_width=True):
                    with st.spinner("Resizing..."):
                        saved_path = save_uploaded_file(uploaded_resize)
                        if saved_path:
                            output_path = resize_image(saved_path, target_width, target_height, maintain_ratio)
                            if output_path and os.path.exists(output_path):
                                result_img = PILImage.open(output_path)
                                new_w, new_h = result_img.size
                                result_img.close()
                                st.success(f"✅ Resized to {new_w}×{new_h}px")
                                create_download_button(output_path, "⬇️ Download Resized Image")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Resize failed.")

# ── TAB 4: CROP & ROTATE ─────────────────────────────────────────
with tab4:
    st.markdown("#### Crop or rotate your image")

    cr_sub1, cr_sub2 = st.tabs(["Rotate / Flip", "Crop"])

    with cr_sub1:
        uploaded_rotate = st.file_uploader(
            "Upload image to rotate/flip",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="rotate_upload"
        )

        if uploaded_rotate is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_rotate, caption="Original", use_container_width=True)

            with col2:
                operation = st.radio("Operation:", ["Rotate", "Flip"], key="rotate_op")

                if operation == "Rotate":
                    angle = st.selectbox(
                        "Rotation angle:",
                        [90, 180, 270, 45, -45, -90],
                        format_func=lambda x: f"{x}°",
                        key="rotate_angle"
                    )
                    expand = st.checkbox("Expand canvas to fit", value=True, key="rotate_expand")

                    if st.button("↪️ Rotate Image", key="btn_rotate", use_container_width=True):
                        with st.spinner("Rotating..."):
                            saved_path = save_uploaded_file(uploaded_rotate)
                            if saved_path:
                                output_path = rotate_image(saved_path, angle, expand)
                                if output_path:
                                    create_download_button(output_path, "⬇️ Download Rotated Image")
                                    cleanup_file(saved_path)
                                else:
                                    st.error("❌ Rotation failed.")
                else:
                    direction = st.radio(
                        "Flip direction:",
                        ["horizontal", "vertical"],
                        format_func=lambda x: x.capitalize(),
                        key="flip_dir"
                    )

                    if st.button("↔️ Flip Image", key="btn_flip", use_container_width=True):
                        with st.spinner("Flipping..."):
                            saved_path = save_uploaded_file(uploaded_rotate)
                            if saved_path:
                                output_path = flip_image(saved_path, direction)
                                if output_path:
                                    create_download_button(output_path, "⬇️ Download Flipped Image")
                                    cleanup_file(saved_path)
                                else:
                                    st.error("❌ Flip failed.")

    with cr_sub2:
        uploaded_crop = st.file_uploader(
            "Upload image to crop",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="crop_upload"
        )

        if uploaded_crop is not None:
            from PIL import Image as PILImage
            import io

            pil_img = PILImage.open(io.BytesIO(uploaded_crop.getvalue()))
            w, h = pil_img.size

            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_crop, caption=f"Size: {w}×{h}px", use_container_width=True)

            with col2:
                st.markdown(f"**Image size:** {w} × {h} pixels")
                left = st.number_input("Left (px)", 0, w - 1, 0, key="crop_left")
                top = st.number_input("Top (px)", 0, h - 1, 0, key="crop_top")
                right = st.number_input("Right (px)", 1, w, w, key="crop_right")
                bottom = st.number_input("Bottom (px)", 1, h, h, key="crop_bottom")

                crop_w = right - left
                crop_h = bottom - top

                if crop_w > 0 and crop_h > 0:
                    st.success(f"Crop result: {crop_w} × {crop_h} px")
                else:
                    st.error("❌ Invalid crop area")

                if st.button("✂️ Crop Image", key="btn_crop", use_container_width=True):
                    if crop_w > 0 and crop_h > 0:
                        with st.spinner("Cropping..."):
                            saved_path = save_uploaded_file(uploaded_crop)
                            if saved_path:
                                output_path = crop_image(saved_path, int(left), int(top), int(right), int(bottom))
                                if output_path:
                                    create_download_button(output_path, "⬇️ Download Cropped Image")
                                    cleanup_file(saved_path)
                                else:
                                    st.error("❌ Crop failed.")

# ── TAB 5: ENHANCE ───────────────────────────────────────────────
with tab5:
    st.markdown("#### Enhance image quality")

    enh_sub1, enh_sub2 = st.tabs(["Brightness / Contrast", "Sharpen"])

    with enh_sub1:
        uploaded_enhance = st.file_uploader(
            "Upload image to enhance",
            type=["jpg", "jpeg", "png", "webp", "bmp"],
            key="enhance_upload"
        )

        if uploaded_enhance is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_enhance, caption="Original", use_container_width=True)

            with col2:
                brightness = st.slider("☀️ Brightness", 0.1, 3.0, 1.0, 0.1, key="brightness")
                contrast = st.slider("🌗 Contrast", 0.1, 3.0, 1.0, 0.1, key="contrast")
                saturation = st.slider("🎨 Saturation", 0.0, 3.0, 1.0, 0.1, key="saturation")
                sharpness = st.slider("🔍 Sharpness", 0.0, 3.0, 1.0, 0.1, key="sharpness")

                if st.button("✨ Enhance Image", key="btn_enhance", use_container_width=True):
                    with st.spinner("Enhancing..."):
                        saved_path = save_uploaded_file(uploaded_enhance)
                        if saved_path:
                            output_path = adjust_brightness_contrast(
                                saved_path, brightness, contrast, saturation, sharpness
                            )
                            if output_path:
                                st.image(output_path, caption="Enhanced", use_container_width=True)
                                create_download_button(output_path, "⬇️ Download Enhanced Image")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Enhancement failed.")

    with enh_sub2:
        uploaded_sharpen = st.file_uploader(
            "Upload blurry image to sharpen",
            type=["jpg", "jpeg", "png", "webp"],
            key="sharpen_upload"
        )

        if uploaded_sharpen is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_sharpen, caption="Original", use_container_width=True)

            with col2:
                strength = st.select_slider(
                    "Sharpening strength:",
                    options=["light", "medium", "strong"],
                    value="medium",
                    key="sharpen_strength"
                )

                if st.button("🔍 Sharpen Image", key="btn_sharpen", use_container_width=True):
                    with st.spinner("Sharpening..."):
                        saved_path = save_uploaded_file(uploaded_sharpen)
                        if saved_path:
                            output_path = sharpen_image(saved_path, strength)
                            if output_path:
                                st.image(output_path, caption="Sharpened", use_container_width=True)
                                create_download_button(output_path, "⬇️ Download Sharpened Image")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Sharpening failed.")

# ── TAB 6: WATERMARK ─────────────────────────────────────────────
with tab6:
    st.markdown("#### Add text watermark to image")

    uploaded_wm = st.file_uploader(
        "Upload image for watermark",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        key="watermark_upload"
    )

    if uploaded_wm is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.image(uploaded_wm, caption="Original", use_container_width=True)

        with col2:
            watermark_text = st.text_input("Watermark text:", value="© Your Name 2024", key="wm_text")
            position = st.selectbox(
                "Position:",
                ["bottom-right", "bottom-left", "top-right", "top-left", "center"],
                key="wm_position"
            )
            opacity = st.slider("Opacity (%)", 10, 100, 50, key="wm_opacity")
            font_size = st.slider("Font size (px)", 12, 100, 36, key="wm_size")
            color = st.selectbox("Color:", ["white", "black", "yellow", "red", "blue"], key="wm_color")

            if st.button("💧 Add Watermark", key="btn_watermark", use_container_width=True):
                with st.spinner("Adding watermark..."):
                    saved_path = save_uploaded_file(uploaded_wm)
                    if saved_path:
                        output_path = add_text_watermark(
                            saved_path, watermark_text, position, opacity, font_size, color
                        )
                        if output_path:
                            st.image(output_path, caption="With Watermark", use_container_width=True)
                            create_download_button(output_path, "⬇️ Download Watermarked Image")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Watermark failed.")

# ── TAB 7: GRAYSCALE ─────────────────────────────────────────────
with tab7:
    st.markdown("#### Convert image to black & white")

    uploaded_gray = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        key="gray_upload"
    )

    if uploaded_gray is not None:
        col1, col2 = st.columns(2)

        with col1:
            st.image(uploaded_gray, caption="Original (Color)", use_container_width=True)

        with col2:
            st.markdown("""
            **Grayscale removes all color and keeps brightness.**
            - Smaller file size
            - Classic / vintage look
            """)

            if st.button("🎨 Convert to Grayscale", key="btn_gray", use_container_width=True):
                with st.spinner("Converting to grayscale..."):
                    saved_path = save_uploaded_file(uploaded_gray)
                    if saved_path:
                        output_path = convert_to_grayscale(saved_path)
                        if output_path:
                            st.image(output_path, caption="Grayscale", use_container_width=True)
                            create_download_button(output_path, "⬇️ Download Grayscale Image")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Grayscale conversion failed.")

# ── TAB 8: BACKGROUND REMOVAL ────────────────────────────────────
with tab8:
    st.markdown("#### Remove image background (AI-powered)")

    if not REMBG_AVAILABLE:
        st.warning("""
        ⚠️ **Background removal is not available on Streamlit Cloud.**

        This feature requires the `rembg` library which is too large for free cloud hosting.

        **To use this feature:**
        - Run the app locally on your computer
        - Install rembg: `pip install rembg`
        - Restart the app

        All other image features work perfectly on the cloud! ✅
        """)
    else:
        uploaded_bg = st.file_uploader(
            "Upload image for background removal",
            type=["jpg", "jpeg", "png", "webp"],
            key="bg_upload"
        )

        if uploaded_bg is not None:
            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_bg, caption="Original", use_container_width=True)

            with col2:
                st.markdown("Output will be a **PNG with transparent background**.")

                if st.button("🪄 Remove Background", key="btn_bg", use_container_width=True):
                    with st.spinner("Removing background (30-60 seconds)..."):
                        saved_path = save_uploaded_file(uploaded_bg)
                        if saved_path:
                            with open(saved_path, "rb") as f:
                                input_bytes = f.read()
                            output_bytes = rembg_remove(input_bytes)
                            from utils.file_utils import generate_output_path
                            output_path = generate_output_path(saved_path, "png", "_nobg")
                            with open(output_path, "wb") as f:
                                f.write(output_bytes)
                            st.image(output_path, caption="Background Removed", use_container_width=True)
                            create_download_button(output_path, "⬇️ Download PNG (No Background)")
                            cleanup_file(saved_path)

# ── TAB 9: IMAGE TO PDF ──────────────────────────────────────────
with tab9:
    st.markdown("#### Convert image(s) to PDF")

    uploaded_imgs_pdf = st.file_uploader(
        "Upload images (you can select multiple)",
        type=["jpg", "jpeg", "png", "webp", "bmp", "tiff"],
        key="img2pdf_upload",
        accept_multiple_files=True
    )

    if uploaded_imgs_pdf:
        st.info(f"📁 {len(uploaded_imgs_pdf)} image(s) selected")

        cols = st.columns(min(len(uploaded_imgs_pdf), 4))
        for idx, img_file in enumerate(uploaded_imgs_pdf[:4]):
            with cols[idx]:
                st.image(img_file, caption=f"Page {idx + 1}", use_container_width=True)

        if st.button("📄 Create PDF", key="btn_img2pdf", use_container_width=True):
            with st.spinner(f"Creating PDF from {len(uploaded_imgs_pdf)} images..."):
                saved_paths = []
                for img_file in uploaded_imgs_pdf:
                    path = save_uploaded_file(img_file)
                    if path:
                        saved_paths.append(path)

                if saved_paths:
                    output_path = image_to_pdf(saved_paths)
                    if output_path and os.path.exists(output_path):
                        create_download_button(output_path, "⬇️ Download PDF", "images_combined.pdf")
                    else:
                        st.error("❌ PDF creation failed.")
                    for path in saved_paths:
                        cleanup_file(path)