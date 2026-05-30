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

# ── TAB 2: COMPRESSION ──────────────────────────────────────────
with tab2:
    st.markdown("#### Compress image — standard quality slider OR exact KB target")

    compress_mode = st.radio(
        "Compression mode:",
        ["🎚️ Quality Slider (standard)", "🎯 Target File Size (exact KB)"],
        horizontal=True,
        key="compress_mode_radio"
    )

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
            from PIL import Image as PILImage
            import io as _io

            # Load once into PIL — all ops in-memory from here
            raw_bytes = uploaded_compress.getvalue()
            pil_img = PILImage.open(_io.BytesIO(raw_bytes))
            original_kb = len(raw_bytes) // 1024

            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_compress, caption=f"Original — {original_kb} KB", use_container_width=True)

            with col2:

                # ── MODE A: Standard quality slider ─────────────────
                if compress_mode == "🎚️ Quality Slider (standard)":
                    quality = st.slider(
                        "Quality Level",
                        min_value=10, max_value=95, value=60,
                        help="Lower = smaller file. Higher = better quality.",
                        key="compress_quality_slider"
                    )

                    if quality < 30:
                        st.warning("⚠️ Very low quality")
                    elif quality < 60:
                        st.info("📌 Good compression balance")
                    else:
                        st.success("✅ High quality retained")

                    out_format = "JPEG" if uploaded_compress.name.lower().endswith(
                        (".jpg", ".jpeg")) else "WEBP"

                    if st.button("📦 Compress Image", key="btn_compress_slider", use_container_width=True):
                        with st.spinner("Compressing..."):
                            buf = _io.BytesIO()
                            img_out = pil_img.copy()
                            if img_out.mode not in ("RGB", "L"):
                                img_out = img_out.convert("RGB")
                            img_out.save(buf, format=out_format, quality=quality, optimize=True)
                            result_bytes = buf.getvalue()
                            result_kb = len(result_bytes) // 1024
                            reduction = (1 - len(result_bytes) / len(raw_bytes)) * 100

                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Original", f"{original_kb} KB")
                            col_b.metric("Compressed", f"{result_kb} KB")
                            col_c.metric("Reduction", f"{reduction:.1f}%")

                            ext = "jpg" if out_format == "JPEG" else "webp"
                            st.download_button(
                                "⬇️ Download Compressed Image",
                                data=result_bytes,
                                file_name=f"compressed_{Path(uploaded_compress.name).stem}.{ext}",
                                mime=f"image/{ext}",
                                use_container_width=True
                            )

                # ── MODE B: Target KB compression ───────────────────
                else:
                    from utils.smart_compress import compress_to_target_kb, suggest_resize_dimensions

                    st.markdown("**Quick presets:**")
                    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
                    preset_kb = None
                    if qcol1.button("20 KB", use_container_width=True, key="preset_20"):
                        preset_kb = 20
                    if qcol2.button("50 KB", use_container_width=True, key="preset_50"):
                        preset_kb = 50
                    if qcol3.button("100 KB", use_container_width=True, key="preset_100"):
                        preset_kb = 100
                    if qcol4.button("200 KB", use_container_width=True, key="preset_200"):
                        preset_kb = 200

                    # Store preset in session state so number_input reflects it
                    if preset_kb:
                        st.session_state["target_kb_value"] = preset_kb

                    target_kb = st.number_input(
                        "Or type exact target size (KB):",
                        min_value=5,
                        max_value=50000,
                        value=st.session_state.get("target_kb_value", 100),
                        step=5,
                        key="target_kb_input"
                    )

                    out_format = st.selectbox(
                        "Output format:",
                        ["JPEG", "WEBP"],
                        key="target_compress_format"
                    )

                    if original_kb <= target_kb:
                        st.info(f"ℹ️ Your image ({original_kb} KB) is already under {target_kb} KB. "
                                f"Download the original or pick a smaller target.")

                    if st.button(
                        f"🎯 Compress to under {target_kb} KB",
                        key="btn_compress_target",
                        use_container_width=True
                    ):
                        iteration_box = st.empty()
                        progress = st.progress(0, text="Starting binary search...")

                        # Patch compress_to_target_kb to report progress
                        # We call it directly and show a spinner
                        with st.spinner(
                            f"Finding best quality under {target_kb} KB "
                            f"(up to 10 iterations)..."
                        ):
                            result_bytes, quality_used, success = compress_to_target_kb(
                                pil_img,
                                int(target_kb),
                                output_format=out_format,
                                max_iterations=10,
                            )

                        progress.progress(100, text="Done!")
                        result_kb = len(result_bytes) // 1024
                        reduction = (1 - len(result_bytes) / len(raw_bytes)) * 100

                        if success:
                            st.success(
                                f"✅ Compressed to **{result_kb} KB** "
                                f"at quality **{quality_used}** "
                                f"— {reduction:.1f}% smaller"
                            )

                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Original", f"{original_kb} KB")
                            col_b.metric("Result", f"{result_kb} KB")
                            col_c.metric("Quality used", str(quality_used))

                        else:
                            st.error(
                                f"❌ Cannot compress below **{target_kb} KB** "
                                f"even at minimum quality. "
                                f"Result at quality=1 is **{result_kb} KB**."
                            )
                            sug_w, sug_h = suggest_resize_dimensions(pil_img, int(target_kb), out_format)
                            st.warning(
                                f"💡 **Suggestion:** Resize the image to approximately "
                                f"**{sug_w} × {sug_h} px** first, then compress again."
                            )

                        if result_bytes:
                            ext = "jpg" if out_format == "JPEG" else "webp"
                            st.download_button(
                                f"⬇️ Download ({result_kb} KB)",
                                data=result_bytes,
                                file_name=f"target{target_kb}kb_{Path(uploaded_compress.name).stem}.{ext}",
                                mime=f"image/{ext}",
                                use_container_width=True
                            )

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
        st.markdown("#### Visually drag to crop your image")

        # Check if streamlit-cropper is available
        try:
            from streamlit_cropper import st_cropper
            CROPPER_AVAILABLE = True
        except ImportError:
            CROPPER_AVAILABLE = False

        if not CROPPER_AVAILABLE:
            st.error(
                "❌ `streamlit-cropper` is not installed. "
                "Add `streamlit-cropper>=0.3.0` to requirements.txt and redeploy."
            )
        else:
            uploaded_crop = st.file_uploader(
                "Upload image to crop",
                type=["jpg", "jpeg", "png", "webp", "bmp"],
                key="crop_upload_visual"
            )

            if uploaded_crop is not None:
                import io as _io
                from PIL import Image as PILImage

                pil_img_crop = PILImage.open(_io.BytesIO(uploaded_crop.getvalue()))
                orig_w, orig_h = pil_img_crop.size

                st.markdown(f"**Original size:** {orig_w} × {orig_h} px")

                # ── Aspect ratio selector ───────────────────────────
                aspect_choice = st.radio(
                    "Aspect ratio lock:",
                    ["Freeform", "1:1 Square", "4:3", "16:9", "3:4 Portrait", "9:16 Portrait"],
                    horizontal=True,
                    key="crop_aspect"
                )

                aspect_map = {
                    "Freeform": None,
                    "1:1 Square": (1, 1),
                    "4:3": (4, 3),
                    "16:9": (16, 9),
                    "3:4 Portrait": (3, 4),
                    "9:16 Portrait": (9, 16),
                }
                aspect_ratio = aspect_map[aspect_choice]

                st.info("👆 Drag the handles on the image below to set your crop area.")

                col1, col2 = st.columns([3, 2])

                with col1:
                    # Interactive crop canvas
                    cropped_pil = st_cropper(
                        pil_img_crop,
                        realtime_update=True,
                        box_color="#6C63FF",
                        aspect_ratio=aspect_ratio,
                        key="cropper_canvas"
                    )

                with col2:
                    st.markdown("**Live Preview:**")

                    if cropped_pil is not None:
                        crop_w, crop_h = cropped_pil.size
                        st.image(
                            cropped_pil,
                            caption=f"Cropped: {crop_w} × {crop_h} px",
                            use_container_width=True
                        )

                        # Output format selector
                        crop_format = st.selectbox(
                            "Save as:",
                            ["PNG", "JPEG", "WEBP"],
                            key="crop_out_format"
                        )

                        if st.button(
                            "✂️ Download Cropped Image",
                            key="btn_visual_crop",
                            use_container_width=True
                        ):
                            buf = _io.BytesIO()

                            save_img = cropped_pil.copy()

                            if crop_format == "JPEG" and save_img.mode in ("RGBA", "LA", "P"):
                                bg = Image.new("RGB", save_img.size, (255, 255, 255))
                                bg.paste(save_img, mask=save_img.split()[-1]
                                         if save_img.mode in ("RGBA", "LA") else None)
                                save_img = bg
                            elif crop_format in ("JPEG",) and save_img.mode != "RGB":
                                save_img = save_img.convert("RGB")

                            save_kwargs = {"format": crop_format}
                            if crop_format in ("JPEG", "WEBP"):
                                save_kwargs["quality"] = 92
                                save_kwargs["optimize"] = True

                            save_img.save(buf, **save_kwargs)
                            result_bytes = buf.getvalue()
                            result_kb = len(result_bytes) // 1024

                            ext = crop_format.lower().replace("jpeg", "jpg")
                            st.success(f"✅ Cropped image ready — {result_kb} KB")
                            st.download_button(
                                label=f"⬇️ Save {crop_w}×{crop_h} px Image",
                                data=result_bytes,
                                file_name=f"cropped_{Path(uploaded_crop.name).stem}.{ext}",
                                mime=f"image/{ext}",
                                use_container_width=True
                            )
                    else:
                        st.info("Drag the crop box on the left to see a preview here.")
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
        import streamlit as st
from PIL import Image
import io

# Ensure rembg is installed in your local virtual environment
try:
    from rembg import remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

st.header("Remove Image Background (AI-Powered)")

if not REMBG_AVAILABLE:
    st.error("❌ 'rembg' library is missing. Run `pip install \"rembg[cpu]\"` in your terminal and restart.")
else:
    uploaded_img = st.file_uploader("Upload an image to isolate the subject", type=["png", "jpg", "jpeg", "webp"])

    if uploaded_img is not None:
        # Load the uploaded file into a PIL Image object
        input_image = Image.open(uploaded_img)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(input_image, caption="Original Image", use_container_width=True)
            
        with col2:
            if st.button("🪄 Isolate Subject & Remove Background", use_container_width=True):
                with st.spinner("Analyzing matrices and separating layers..."):
                    try:
                        # Convert PIL Image to raw bytes for rembg processing
                        img_byte_arr = io.BytesIO()
                        input_image.save(img_byte_arr, format=input_image.format if input_image.format else "PNG")
                        raw_bytes = img_byte_arr.getvalue()
                        
                        # Process using the AI engine
                        output_bytes = remove(raw_bytes)
                        
                        # Convert resulting bytes back to a displayable PIL Image
                        result_image = Image.open(io.BytesIO(output_bytes))
                        
                        st.image(result_image, caption="AI Isolated Image", use_container_width=True)
                        
                        # Prepare clean download buffer
                        buf = io.BytesIO()
                        result_image.save(buf, format="PNG") # PNG handles transparency alpha channels natively
                        byte_im = buf.getvalue()
                        
                        st.download_button(
                            label="📥 Download Transparent Image",
                            data=byte_im,
                            file_name=f"{uploaded_img.name.split('.')[0]}_nobg.png",
                            mime="image/png",
                            use_container_width=True
                        )
                    except Exception as e:
                        st.error(f"Execution Error: {str(e)}")
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