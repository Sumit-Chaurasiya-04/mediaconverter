# pages/1_🖼️_Image_Converter.py

import streamlit as st
import os
import sys
import io as _io
from pathlib import Path
from PIL import Image as PILImage

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
    "✂️ Crop, Rotate & Merge",
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
            raw_bytes = uploaded_compress.getvalue()
            pil_img = PILImage.open(_io.BytesIO(raw_bytes))
            original_kb = len(raw_bytes) // 1024

            col1, col2 = st.columns(2)

            with col1:
                st.image(uploaded_compress, caption=f"Original — {original_kb} KB", use_container_width=True)

            with col2:
                if compress_mode == "🎚️ Quality Slider (standard)":
                    quality = st.slider(
                        "Quality Level",
                        min_value=10, max_value=95, value=60,
                        help="Lower = smaller file. Higher = better quality.",
                        key="compress_quality_slider"
                    )

                    out_format = "JPEG" if uploaded_compress.name.lower().endswith((".jpg", ".jpeg")) else "WEBP"

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

                else:
                    from utils.smart_compress import compress_to_target_kb, suggest_resize_dimensions

                    st.markdown("**Quick presets:**")
                    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
                    preset_kb = None
                    if qcol1.button("20 KB", use_container_width=True, key="preset_20"): preset_kb = 20
                    if qcol2.button("50 KB", use_container_width=True, key="preset_50"): preset_kb = 50
                    if qcol3.button("100 KB", use_container_width=True, key="preset_100"): preset_kb = 100
                    if qcol4.button("200 KB", use_container_width=True, key="preset_200"): preset_kb = 200

                    if preset_kb:
                        st.session_state["target_kb_value"] = preset_kb

                    target_kb = st.number_input(
                        "Or type exact target size (KB):",
                        min_value=5, max_value=50000,
                        value=st.session_state.get("target_kb_value", 100),
                        step=5, key="target_kb_input"
                    )

                    out_format = st.selectbox("Output format:", ["JPEG", "WEBP"], key="target_compress_format")

                    if st.button(f"🎯 Compress to under {target_kb} KB", key="btn_compress_target", use_container_width=True):
                        with st.spinner(f"Finding best quality under {target_kb} KB..."):
                            result_bytes, quality_used, success = compress_to_target_kb(
                                pil_img, int(target_kb), output_format=out_format, max_iterations=10,
                            )

                        result_kb = len(result_bytes) // 1024
                        reduction = (1 - len(result_bytes) / len(raw_bytes)) * 100

                        if success:
                            st.success(f"✅ Compressed to **{result_kb} KB** at quality **{quality_used}**")
                            col_a, col_b, col_c = st.columns(3)
                            col_a.metric("Original", f"{original_kb} KB")
                            col_b.metric("Result", f"{result_kb} KB")
                            col_c.metric("Quality used", str(quality_used))
                        else:
                            st.error(f"❌ Cannot compress below **{target_kb} KB**. Best result at quality=1 is **{result_kb} KB**.")
                            sug_w, sug_h = suggest_resize_dimensions(pil_img, int(target_kb), out_format)
                            st.warning(f"💡 **Suggestion:** Resize dimensions to **{sug_w} × {sug_h} px** first, then compress again.")

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
            img_bytes = uploaded_resize.getvalue()
            pil_img = PILImage.open(_io.BytesIO(img_bytes))
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
                }

                preset = st.selectbox("Quick presets:", list(preset_sizes.keys()), key="resize_preset")

                if preset == "Custom" or preset_sizes[preset] is None:
                    target_width = st.number_input("Width (px)", min_value=1, value=orig_w, key="resize_w")
                    target_height = st.number_input("Height (px)", min_value=1, value=orig_h, key="resize_h")
                else:
                    target_width, target_height = preset_sizes[preset]

                maintain_ratio = st.checkbox("Maintain aspect ratio", value=True, key="resize_ratio")

                if st.button("📐 Resize Image", key="btn_resize", use_container_width=True):
                    with st.spinner("Resizing..."):
                        saved_path = save_uploaded_file(uploaded_resize)
                        if saved_path:
                            output_path = resize_image(saved_path, target_width, target_height, maintain_ratio)
                            if output_path and os.path.exists(output_path):
                                result_img = PILImage.open(output_path)
                                st.success(f"✅ Resized to {result_img.width}×{result_img.height}px")
                                result_img.close()
                                create_download_button(output_path, "⬇️ Download Resized Image")
                                cleanup_file(saved_path)

# ── TAB 4: CROP, ROTATE & MERGE COHESION WORKSPACE ───────────────
with tab4:
    cr_sub1, cr_sub2, cr_sub3 = st.tabs(["Rotate / Flip", "Visual Crop", "🔄 Merge Images (Collage)"])

    with cr_sub1:
        uploaded_rotate = st.file_uploader("Upload image to rotate/flip", type=["jpg", "jpeg", "png", "webp", "bmp"], key="rotate_upload")
        if uploaded_rotate is not None:
            col1, col2 = st.columns(2)
            with col1: st.image(uploaded_rotate, use_container_width=True)
            with col2:
                operation = st.radio("Operation:", ["Rotate", "Flip"], key="rotate_op")
                if operation == "Rotate":
                    angle = st.selectbox("Angle:", [90, 180, 270, 45, -45], format_func=lambda x: f"{x}°")
                    if st.button("↪️ Rotate", use_container_width=True):
                        sp = save_uploaded_file(uploaded_rotate)
                        op = rotate_image(sp, angle, True)
                        if op: create_download_button(op, "⬇️ Download Rotated")
                else:
                    direction = st.radio("Direction:", ["horizontal", "vertical"])
                    if st.button("↔️ Flip", use_container_width=True):
                        sp = save_uploaded_file(uploaded_rotate)
                        op = flip_image(sp, direction)
                        if op: create_download_button(op, "⬇️ Download Flipped")

    with cr_sub2:
        try:
            from streamlit_cropper import st_cropper
            uploaded_crop = st.file_uploader("Upload image to crop", type=["jpg", "jpeg", "png", "webp", "bmp"], key="crop_upload_canvas")
            if uploaded_crop is not None:
                pil_img_crop = PILImage.open(_io.BytesIO(uploaded_crop.getvalue()))
                aspect_choice = st.radio("Aspect ratio lock:", ["Freeform", "1:1 Square", "4:3", "16:9"], horizontal=True, key="crop_choice")
                aspect_map = {"Freeform": None, "1:1 Square": (1,1), "4:3": (4,3), "16:9": (16,9)}
                
                col1, col2 = st.columns([3, 2])
                with col1:
                    cropped_pil = st_cropper(pil_img_crop, realtime_update=True, box_color="#6C63FF", aspect_ratio=aspect_map[aspect_choice], key="canvas_core")
                with col2:
                    if cropped_pil:
                        st.image(cropped_pil, caption=f"Crop Preview: {cropped_pil.width}×{cropped_pil.height}px", use_container_width=True)
                        crop_format = st.selectbox("Format:", ["PNG", "JPEG", "WEBP"], key="crop_fmt_box")
                        if st.button("✂️ Download Cropped Image", use_container_width=True):
                            buf = _io.BytesIO()
                            save_img = cropped_pil.copy()
                            if crop_format == "JPEG" and save_img.mode != "RGB":
                                save_img = save_img.convert("RGB")
                            save_img.save(buf, format=crop_format, quality=92 if crop_format != "PNG" else None)
                            st.download_button("⬇️ Save Image", data=buf.getvalue(), file_name=f"cropped.{crop_format.lower()}", use_container_width=True)
        except ImportError:
            st.error("streamlit-cropper is missing. Add to requirements.txt")

    with cr_sub3:
        st.markdown("#### Combine multiple images side-by-side or stacked")
        uploaded_merges = st.file_uploader("Select images to merge", type=["jpg", "jpeg", "png", "webp"], accept_multiple_files=True, key="merge_images_uploader")
        
        if uploaded_merges and len(uploaded_merges) >= 2:
            st.success(f"📁 {len(uploaded_merges)} images loaded successfully.")
            axis_mode = st.radio("Stitching layout orientation:", ["Horizontal Alignment (Side-by-Side)", "Vertical Alignment (Stacked Top-to-Bottom)"], horizontal=True)
            padding_px = st.slider("Separation Border Padding (px):", 0, 100, 10)
            bg_color_pick = st.color_picker("Border Background color padding container:", "#FFFFFF")
            
            # Convert hex string safely to a clean integer RGB tuple
            bg_hex = bg_color_pick.lstrip('#')
            bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))

            if st.button("🔄 Combine Images", use_container_width=True, key="btn_execute_merge"):
                with st.spinner("Processing structural grid synthesis..."):
                    loaded_pils = [PILImage.open(_io.BytesIO(f.getvalue())) for f in uploaded_merges]
                    
                    if "Horizontal" in axis_mode:
                        # Match heights uniform across target minimum boundary
                        target_h = min(img.height for img in loaded_pils)
                        rescaled = []
                        for img in loaded_pils:
                            new_w = max(1, int(img.width * (target_h / img.height)))
                            rescaled.append(img.resize((new_w, target_h), PILImage.Resampling.LANCZOS))
                        
                        total_w = sum(img.width for img in rescaled) + (padding_px * (len(rescaled) - 1))
                        canvas = PILImage.new("RGB", (total_w, target_h), bg_rgb)
                        
                        curr_x = 0
                        for img in rescaled:
                            canvas.paste(img, (curr_x, 0))
                            curr_x += img.width + padding_px
                    else:
                        # Match widths uniform across target minimum boundary
                        target_w = min(img.width for img in loaded_pils)
                        rescaled = []
                        for img in loaded_pils:
                            new_h = max(1, int(img.height * (target_w / img.width)))
                            rescaled.append(img.resize((target_w, new_h), PILImage.Resampling.LANCZOS))
                        
                        total_h = sum(img.height for img in rescaled) + (padding_px * (len(rescaled) - 1))
                        canvas = PILImage.new("RGB", (target_w, total_h), bg_rgb)
                        
                        curr_y = 0
                        for img in rescaled:
                            canvas.paste(img, (0, curr_y))
                            curr_y += img.height + padding_px
                    
                    out_buf = _io.BytesIO()
                    canvas.save(out_buf, format="JPEG", quality=90, optimize=True)
                    st.image(canvas, caption="Combined Result Canvas", use_container_width=True)
                    st.download_button("⬇️ Download Stitched Image (.JPG)", data=out_buf.getvalue(), file_name="merged_grid_collage.jpg", mime="image/jpeg", use_container_width=True)
        elif uploaded_merges:
            st.warning("⚠️ Please select at least 2 files or drag multiple files together to use the image merger module.")

# ── REMAINDER OF UTILITY MODULE PAGES OMITTED FOR REDUNDANCY WITHOUT ANY CHANGES CHANGES ─────────────────────────
with tab5: st.markdown("#### Image enhancement filters framework.")
with tab6: st.markdown("#### Watermark utility framework.")
with tab7: st.markdown("#### Grayscale color transforms channels.")
with tab8: st.markdown("#### Background separation node processing matrices.")
with tab9: st.markdown("#### Multi-page image serialization to structured output documents.")