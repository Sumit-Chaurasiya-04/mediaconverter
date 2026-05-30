# app.py
# Home page with smart file dropzone — detects file type and routes to the right tool

import streamlit as st
import os
import sys
import io
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import APP_NAME, APP_VERSION

# ── PAGE CONFIG ─────────────────────────────────────────────────
st.set_page_config(
    page_title=f"{APP_NAME} - Universal File Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ──────────────────────────────────────────────────────────
def load_css():
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ── CLEANUP OLD TEMP FILES ───────────────────────────────────────
from utils.file_utils import cleanup_old_files
cleanup_old_files(max_age_hours=2)

# ── SESSION STATE DEFAULTS ───────────────────────────────────────
# These flags control which inline tool widget is rendered
defaults = {
    "router_file": None,
    "router_ext": None,
    "active_tool": None,   # e.g. "compress_kb", "visual_crop", "csv_excel", "pdf_merge" …
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── ROUTING MATRIX ───────────────────────────────────────────────
IMAGE_EXTS   = {"png", "jpg", "jpeg", "webp", "bmp", "tiff", "gif"}
VIDEO_EXTS   = {"mp4", "avi", "mov", "mkv", "webm"}
AUDIO_EXTS   = {"mp3", "wav", "aac", "flac", "ogg", "m4a"}
DOC_EXTS     = {"pdf", "docx", "doc"}
SHEET_EXTS   = {"csv", "xlsx", "xls"}

ALL_EXTS = list(IMAGE_EXTS | VIDEO_EXTS | AUDIO_EXTS | DOC_EXTS | SHEET_EXTS)

def detect_category(ext: str) -> str:
    ext = ext.lower().lstrip(".")
    if ext in IMAGE_EXTS:   return "image"
    if ext in VIDEO_EXTS:   return "video"
    if ext in AUDIO_EXTS:   return "audio"
    if ext in DOC_EXTS:     return "document"
    if ext in SHEET_EXTS:   return "spreadsheet"
    return "unknown"

# ── SIDEBAR ───────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='text-align:center; padding:1.5rem 0;'>
        <div style='font-size:3rem;'>🔄</div>
        <h2 style='color:#6C63FF; margin:0.5rem 0;'>MediaConvert</h2>
        <p style='color:#8B8FA8; font-size:0.85rem;'>Universal File Converter</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🗂️ All Tools")
    st.markdown("""
    Use the **pages** in this sidebar or **drop a file** on the home page
    and let the app guide you to the right tool automatically.
    """)
    st.markdown("---")

    import shutil
    st.markdown("### ⚙️ System Status")
    tools = [
        ("FFmpeg",      shutil.which("ffmpeg") is not None),
        ("Ghostscript", shutil.which("gs") is not None or shutil.which("gswin64c") is not None),
        ("LibreOffice", shutil.which("libreoffice") is not None or shutil.which("soffice") is not None),
        ("Tesseract",   shutil.which("tesseract") is not None),
    ]
    for name, ok in tools:
        color = "#00D4AA" if ok else "#FF4B4B"
        icon  = "✅" if ok else "❌"
        st.markdown(f'<div style="color:{color};font-size:0.85rem;">{icon} {name}</div>',
                    unsafe_allow_html=True)

    packages = [
        ("Pillow",   "PIL"),
        ("MoviePy",  "moviepy"),
        ("PyPDF2",   "PyPDF2"),
        ("Pandas",   "pandas"),
        ("st-cropper", "streamlit_cropper"),
    ]
    for pkg_name, imp in packages:
        try:
            __import__(imp)
            st.markdown(f'<div style="color:#00D4AA;font-size:0.85rem;">✅ {pkg_name}</div>',
                        unsafe_allow_html=True)
        except ImportError:
            st.markdown(f'<div style="color:#FFA500;font-size:0.85rem;">⚠️ {pkg_name}</div>',
                        unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(f'<div style="font-size:0.75rem;color:#8B8FA8;text-align:center;">v{APP_VERSION} • 100% Free</div>',
                unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# HERO
# ════════════════════════════════════════════════════════════════
st.markdown("""
<div style='background:linear-gradient(135deg,#6C63FF 0%,#FF6584 100%);
     border-radius:20px;padding:2.5rem 2rem;text-align:center;margin-bottom:2rem;'>
    <h1 style='color:white;font-size:2.8rem;margin:0;'>🔄 MediaConvert Pro</h1>
    <p style='color:rgba(255,255,255,0.88);margin:0.6rem 0 0;font-size:1.15rem;'>
        Drop any file below — we'll show you exactly what to do with it.
    </p>
</div>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════
# SMART DROP ZONE
# ════════════════════════════════════════════════════════════════
st.markdown("## 📂 Smart File Drop Zone")
st.markdown("Upload any file and the app will automatically suggest the best tools for it.")

dropped_file = st.file_uploader(
    "Drop your file here — images, videos, audio, PDFs, Word docs, spreadsheets",
    type=ALL_EXTS,
    key="smart_router_upload",
    label_visibility="collapsed"
)

if dropped_file is not None:
    ext = Path(dropped_file.name).suffix.lower().lstrip(".")
    category = detect_category(ext)
    file_kb = len(dropped_file.getbuffer()) // 1024

    # Store in session for inline tool widgets to use
    st.session_state["router_file"] = dropped_file
    st.session_state["router_ext"]  = ext

    # ── File info banner ────────────────────────────────────────
    cat_icons = {
        "image": "🖼️", "video": "🎬", "audio": "🎵",
        "document": "📄", "spreadsheet": "📊", "unknown": "📁"
    }
    st.markdown(f"""
    <div style='background:rgba(108,99,255,0.12);border:1px solid rgba(108,99,255,0.35);
         border-radius:12px;padding:1rem 1.5rem;margin-bottom:1.5rem;
         display:flex;align-items:center;gap:1rem;'>
        <span style='font-size:2.5rem;'>{cat_icons.get(category,"📁")}</span>
        <div>
            <strong style='color:#fff;font-size:1.05rem;'>{dropped_file.name}</strong><br>
            <span style='color:#8B8FA8;font-size:0.9rem;'>
                {file_kb} KB &nbsp;•&nbsp; .{ext.upper()} &nbsp;•&nbsp; {category.capitalize()}
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── ROUTE BUTTONS ────────────────────────────────────────────
    st.markdown("### ⚡ What would you like to do?")

    if category == "image":
        c1, c2, c3, c4 = st.columns(4)
        if c1.button("🎯 Compress to Exact KB",   use_container_width=True, key="rt_compress_kb"):
            st.session_state["active_tool"] = "compress_kb"
        if c2.button("✂️ Visual Crop Canvas",      use_container_width=True, key="rt_crop"):
            st.session_state["active_tool"] = "visual_crop"
        if c3.button("🔄 Convert Format",          use_container_width=True, key="rt_convert"):
            st.session_state["active_tool"] = "convert_format"
        if c4.button("📐 Resize Image",            use_container_width=True, key="rt_resize"):
            st.session_state["active_tool"] = "resize_image"

        c5, c6, c7, _ = st.columns(4)
        if c5.button("✨ Enhance / Adjust",        use_container_width=True, key="rt_enhance"):
            st.session_state["active_tool"] = "enhance"
        if c6.button("💧 Add Watermark",           use_container_width=True, key="rt_watermark"):
            st.session_state["active_tool"] = "watermark"
        if c7.button("📄 Image → PDF",             use_container_width=True, key="rt_img2pdf"):
            st.session_state["active_tool"] = "img2pdf"

    elif category == "spreadsheet":
        c1, c2, _ , __ = st.columns(4)
        if c1.button("📊 Convert to Excel (.xlsx)", use_container_width=True, key="rt_csv_excel"):
            st.session_state["active_tool"] = "csv_excel"
        if c2.button("📄 Convert to CSV",           use_container_width=True, key="rt_excel_csv"):
            st.session_state["active_tool"] = "excel_csv"

    elif category == "document":
        c1, c2, c3, _ = st.columns(4)
        if c1.button("📎 Merge / Split PDF",        use_container_width=True, key="rt_pdf_merge"):
            st.session_state["active_tool"] = "pdf_merge"
        if c2.button("📝 Word → PDF",               use_container_width=True, key="rt_word_pdf"):
            st.session_state["active_tool"] = "word_pdf"
        if c3.button("📋 Extract Text / OCR",       use_container_width=True, key="rt_ocr"):
            st.session_state["active_tool"] = "extract_text"

    elif category in ("video", "audio"):
        st.info(f"🎬 For {category} files, use the **{category.capitalize()} Converter** page in the sidebar — "
                f"it has all available tools for your `.{ext}` file.")

    # Clear tool button
    if st.session_state.get("active_tool"):
        st.markdown("---")
        if st.button("✖ Close tool / choose different action", key="rt_clear"):
            st.session_state["active_tool"] = None
            st.rerun()

# ════════════════════════════════════════════════════════════════
# INLINE TOOL WIDGETS (rendered by session state flags)
# ════════════════════════════════════════════════════════════════

active = st.session_state.get("active_tool")
routed_file = st.session_state.get("router_file")

if active and routed_file:
    st.markdown("---")

    # ── TOOL: Compress to exact KB ───────────────────────────────
    if active == "compress_kb":
        st.markdown("### 🎯 Compress to Exact KB")

        from utils.smart_compress import compress_to_target_kb, suggest_resize_dimensions
        from PIL import Image as PILImage

        raw = routed_file.getvalue()
        pil_img = PILImage.open(io.BytesIO(raw))
        original_kb = len(raw) // 1024

        st.image(routed_file, caption=f"Original — {original_kb} KB", use_container_width=False, width=400)

        st.markdown("**Quick presets:**")
        qc1, qc2, qc3, qc4 = st.columns(4)
        if qc1.button("20 KB",  key="home_p20",  use_container_width=True): st.session_state["home_target_kb"] = 20
        if qc2.button("50 KB",  key="home_p50",  use_container_width=True): st.session_state["home_target_kb"] = 50
        if qc3.button("100 KB", key="home_p100", use_container_width=True): st.session_state["home_target_kb"] = 100
        if qc4.button("200 KB", key="home_p200", use_container_width=True): st.session_state["home_target_kb"] = 200

        target_kb = st.number_input(
            "Or enter exact KB target:",
            min_value=5, max_value=50000,
            value=st.session_state.get("home_target_kb", 100),
            step=5, key="home_target_kb_input"
        )
        out_fmt = st.selectbox("Output format:", ["JPEG", "WEBP"], key="home_compress_fmt")

        if st.button(f"🎯 Compress to under {target_kb} KB", key="home_btn_compress", use_container_width=True):
            with st.spinner("Running binary search compression..."):
                result_bytes, quality_used, success = compress_to_target_kb(
                    pil_img, int(target_kb), output_format=out_fmt
                )
            result_kb = len(result_bytes) // 1024

            if success:
                st.success(f"✅ Compressed to **{result_kb} KB** at quality **{quality_used}**")
            else:
                st.error(f"❌ Could not reach {target_kb} KB. Best result: {result_kb} KB at quality=1")
                sug_w, sug_h = suggest_resize_dimensions(pil_img, int(target_kb), out_fmt)
                st.warning(f"💡 Try resizing to **{sug_w} × {sug_h} px** first, then compress again.")

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Original",  f"{original_kb} KB")
            col_b.metric("Result",    f"{result_kb} KB")
            col_c.metric("Quality",   str(quality_used))

            ext_out = "jpg" if out_fmt == "JPEG" else "webp"
            st.download_button(
                f"⬇️ Download ({result_kb} KB)",
                data=result_bytes,
                file_name=f"compressed_{Path(routed_file.name).stem}.{ext_out}",
                mime=f"image/{ext_out}",
                use_container_width=True,
                key="home_dl_compress"
            )

    # ── TOOL: Visual Crop ─────────────────────────────────────────
    elif active == "visual_crop":
        st.markdown("### ✂️ Visual Crop Canvas")

        try:
            from streamlit_cropper import st_cropper
            from PIL import Image as PILImage

            pil_img_c = PILImage.open(io.BytesIO(routed_file.getvalue()))
            orig_w, orig_h = pil_img_c.size
            st.markdown(f"**Original:** {orig_w} × {orig_h} px")

            aspect_choice = st.radio(
                "Aspect ratio:",
                ["Freeform", "1:1 Square", "4:3", "16:9", "3:4 Portrait", "9:16 Portrait"],
                horizontal=True,
                key="home_crop_aspect"
            )
            aspect_map = {
                "Freeform": None, "1:1 Square": (1,1),
                "4:3": (4,3), "16:9": (16,9),
                "3:4 Portrait": (3,4), "9:16 Portrait": (9,16),
            }

            col1, col2 = st.columns([3, 2])
            with col1:
                cropped = st_cropper(
                    pil_img_c,
                    realtime_update=True,
                    box_color="#6C63FF",
                    aspect_ratio=aspect_map[aspect_choice],
                    key="home_cropper"
                )
            with col2:
                if cropped:
                    cw, ch = cropped.size
                    st.image(cropped, caption=f"Preview: {cw}×{ch}px", use_container_width=True)
                    crop_fmt = st.selectbox("Save as:", ["PNG","JPEG","WEBP"], key="home_crop_fmt")
                    buf = io.BytesIO()
                    save_img = cropped.copy()
                    if crop_fmt == "JPEG" and save_img.mode != "RGB":
                        save_img = save_img.convert("RGB")
                    save_img.save(buf, format=crop_fmt,
                                  **{"quality": 92, "optimize": True} if crop_fmt != "PNG" else {})
                    ext_c = crop_fmt.lower().replace("jpeg","jpg")
                    st.download_button(
                        f"⬇️ Download {cw}×{ch} px",
                        data=buf.getvalue(),
                        file_name=f"cropped_{Path(routed_file.name).stem}.{ext_c}",
                        mime=f"image/{ext_c}",
                        use_container_width=True,
                        key="home_dl_crop"
                    )
        except ImportError:
            st.error("❌ `streamlit-cropper` not installed. Add it to requirements.txt and redeploy.")

    # ── TOOL: Convert Format ──────────────────────────────────────
    elif active == "convert_format":
        st.markdown("### 🔄 Convert Image Format")
        from utils.image_utils import convert_image_format
        from utils.file_utils import save_uploaded_file, cleanup_file
        from PIL import Image as PILImage

        col1, col2 = st.columns(2)
        with col1:
            st.image(routed_file, caption=f"Original .{st.session_state['router_ext']}", use_container_width=True)
        with col2:
            cur_ext = st.session_state["router_ext"]
            fmts = [f for f in ["png","jpg","webp","bmp","tiff","gif","ico"] if f != cur_ext]
            tgt = st.selectbox("Convert to:", fmts, format_func=str.upper, key="home_conv_fmt")
            quality = 85
            if tgt in ["jpg","webp"]:
                quality = st.slider("Quality", 10, 95, 85, key="home_conv_q")
            if st.button("🔄 Convert", key="home_btn_conv", use_container_width=True):
                with st.spinner("Converting..."):
                    sp = save_uploaded_file(routed_file)
                    if sp:
                        op = convert_image_format(sp, tgt, quality)
                        if op:
                            result_kb = os.path.getsize(op) // 1024
                            st.success(f"✅ Converted — {result_kb} KB")
                            with open(op,"rb") as f:
                                st.download_button(
                                    f"⬇️ Download .{tgt.upper()}",
                                    data=f.read(),
                                    file_name=f"{Path(routed_file.name).stem}.{tgt}",
                                    mime=f"image/{tgt}",
                                    use_container_width=True,
                                    key="home_dl_conv"
                                )
                            cleanup_file(sp)
                        else:
                            st.error("❌ Conversion failed.")

    # ── TOOL: Resize ──────────────────────────────────────────────
    elif active == "resize_image":
        st.markdown("### 📐 Resize Image")
        from utils.image_utils import resize_image
        from utils.file_utils import save_uploaded_file, cleanup_file
        from PIL import Image as PILImage

        pil_r = PILImage.open(io.BytesIO(routed_file.getvalue()))
        ow, oh = pil_r.size
        st.image(routed_file, caption=f"Original: {ow}×{oh}px", use_container_width=False, width=350)

        presets = {
            "Custom": None,
            "HD 1280×720": (1280,720),
            "Full HD 1920×1080": (1920,1080),
            "Square 1080×1080": (1080,1080),
            "Thumbnail 320×240": (320,240),
        }
        choice = st.selectbox("Preset:", list(presets.keys()), key="home_res_preset")
        if presets[choice]:
            tw, th = presets[choice]
        else:
            tw = st.number_input("Width px", 1, 8000, ow, key="home_rw")
            th = st.number_input("Height px", 1, 8000, oh, key="home_rh")

        maintain = st.checkbox("Maintain aspect ratio", True, key="home_ratio")

        if st.button("📐 Resize", key="home_btn_resize", use_container_width=True):
            with st.spinner("Resizing..."):
                sp = save_uploaded_file(routed_file)
                if sp:
                    op = resize_image(sp, tw, th, maintain)
                    if op:
                        result_img = PILImage.open(op)
                        nw, nh = result_img.size
                        result_img.close()
                        st.success(f"✅ Resized to {nw}×{nh} px")
                        with open(op,"rb") as f:
                            st.download_button(
                                "⬇️ Download Resized Image",
                                data=f.read(),
                                file_name=f"resized_{routed_file.name}",
                                mime=f"image/{st.session_state['router_ext']}",
                                use_container_width=True,
                                key="home_dl_resize"
                            )
                        cleanup_file(sp)
                    else:
                        st.error("❌ Resize failed.")

    # ── TOOL: Enhance ─────────────────────────────────────────────
    elif active == "enhance":
        st.markdown("### ✨ Enhance Image")
        from utils.image_utils import adjust_brightness_contrast
        from utils.file_utils import save_uploaded_file, cleanup_file

        col1, col2 = st.columns(2)
        with col1:
            st.image(routed_file, caption="Original", use_container_width=True)
        with col2:
            br = st.slider("☀️ Brightness", 0.1, 3.0, 1.0, 0.1, key="home_br")
            co = st.slider("🌗 Contrast",   0.1, 3.0, 1.0, 0.1, key="home_co")
            sa = st.slider("🎨 Saturation", 0.0, 3.0, 1.0, 0.1, key="home_sa")
            sh = st.slider("🔍 Sharpness",  0.0, 3.0, 1.0, 0.1, key="home_sh")
            if st.button("✨ Apply", key="home_btn_enh", use_container_width=True):
                with st.spinner("Enhancing..."):
                    sp = save_uploaded_file(routed_file)
                    if sp:
                        op = adjust_brightness_contrast(sp, br, co, sa, sh)
                        if op:
                            st.image(op, caption="Enhanced", use_container_width=True)
                            with open(op,"rb") as f:
                                st.download_button("⬇️ Download", data=f.read(),
                                    file_name=f"enhanced_{routed_file.name}",
                                    use_container_width=True, key="home_dl_enh")
                            cleanup_file(sp)

    # ── TOOL: Watermark ───────────────────────────────────────────
    elif active == "watermark":
        st.markdown("### 💧 Add Watermark")
        from utils.image_utils import add_text_watermark
        from utils.file_utils import save_uploaded_file, cleanup_file

        col1, col2 = st.columns(2)
        with col1:
            st.image(routed_file, use_container_width=True)
        with col2:
            wm_text = st.text_input("Watermark text:", "© 2024", key="home_wm_txt")
            wm_pos  = st.selectbox("Position:", ["bottom-right","bottom-left","top-right","top-left","center"], key="home_wm_pos")
            wm_op   = st.slider("Opacity %", 10, 100, 50, key="home_wm_op")
            wm_size = st.slider("Font size", 12, 100, 36, key="home_wm_sz")
            wm_col  = st.selectbox("Color:", ["white","black","yellow","red"], key="home_wm_col")
            if st.button("💧 Apply Watermark", key="home_btn_wm", use_container_width=True):
                with st.spinner("Adding watermark..."):
                    sp = save_uploaded_file(routed_file)
                    if sp:
                        op = add_text_watermark(sp, wm_text, wm_pos, wm_op, wm_size, wm_col)
                        if op:
                            st.image(op, caption="Watermarked", use_container_width=True)
                            with open(op,"rb") as f:
                                st.download_button("⬇️ Download", data=f.read(),
                                    file_name=f"watermarked_{routed_file.name}",
                                    use_container_width=True, key="home_dl_wm")
                            cleanup_file(sp)

    # ── TOOL: Image to PDF ────────────────────────────────────────
    elif active == "img2pdf":
        st.markdown("### 📄 Convert Image to PDF")
        from utils.image_utils import image_to_pdf
        from utils.file_utils import save_uploaded_file, cleanup_file

        st.image(routed_file, caption="Image to convert", use_container_width=False, width=350)
        if st.button("📄 Create PDF", key="home_btn_i2pdf", use_container_width=True):
            with st.spinner("Creating PDF..."):
                sp = save_uploaded_file(routed_file)
                if sp:
                    op = image_to_pdf([sp])
                    if op:
                        size_kb = os.path.getsize(op) // 1024
                        st.success(f"✅ PDF created — {size_kb} KB")
                        with open(op,"rb") as f:
                            st.download_button("⬇️ Download PDF", data=f.read(),
                                file_name=f"{Path(routed_file.name).stem}.pdf",
                                mime="application/pdf",
                                use_container_width=True, key="home_dl_i2pdf")
                        cleanup_file(sp)

    # ── TOOL: CSV → Excel ─────────────────────────────────────────
    elif active == "csv_excel":
        st.markdown("### 📊 Convert CSV to Excel")
        from utils.document_utils import csv_to_excel
        from utils.file_utils import save_uploaded_file, cleanup_file
        import pandas as pd

        df_prev = pd.read_csv(io.BytesIO(routed_file.getvalue()))
        st.markdown(f"**Preview:** {len(df_prev)} rows × {len(df_prev.columns)} columns")
        st.dataframe(df_prev.head(10), use_container_width=True)

        if st.button("📊 Convert to Excel", key="home_btn_csv", use_container_width=True):
            with st.spinner("Converting..."):
                sp = save_uploaded_file(routed_file)
                if sp:
                    op = csv_to_excel(sp)
                    if op:
                        with open(op,"rb") as f:
                            st.download_button("⬇️ Download .xlsx", data=f.read(),
                                file_name=f"{Path(routed_file.name).stem}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True, key="home_dl_csv")
                        cleanup_file(sp)

    # ── TOOL: Excel → CSV ─────────────────────────────────────────
    elif active == "excel_csv":
        st.markdown("### 📄 Convert Excel to CSV")
        from utils.document_utils import excel_to_csv, get_excel_sheets
        from utils.file_utils import save_uploaded_file, cleanup_file
        import pandas as pd

        sp = save_uploaded_file(routed_file)
        if sp:
            sheets = get_excel_sheets(sp)
            sel = st.selectbox("Sheet:", sheets, key="home_sheet") if sheets else None
            df_prev = pd.read_excel(sp, sheet_name=sel, engine="openpyxl")
            st.dataframe(df_prev.head(10), use_container_width=True)
            if st.button("📄 Convert to CSV", key="home_btn_excel", use_container_width=True):
                with st.spinner("Converting..."):
                    op = excel_to_csv(sp, sel)
                    if op:
                        with open(op,"rb") as f:
                            st.download_button("⬇️ Download .csv", data=f.read(),
                                file_name=f"{Path(routed_file.name).stem}.csv",
                                mime="text/csv",
                                use_container_width=True, key="home_dl_excel")
                        cleanup_file(sp)

    # ── TOOL: PDF Merge/Split ─────────────────────────────────────
    elif active == "pdf_merge":
        st.markdown("### 📎 PDF — Merge / Split")
        from utils.document_utils import split_pdf, get_pdf_page_count
        from utils.file_utils import save_uploaded_file, cleanup_file

        sp = save_uploaded_file(routed_file)
        if sp:
            total = get_pdf_page_count(sp)
            st.info(f"📄 This PDF has **{total} pages**")
            c1, c2 = st.columns(2)
            start_p = c1.number_input("From page:", 1, total, 1, key="home_sp")
            end_p   = c2.number_input("To page:",   1, total, total, key="home_ep")
            if st.button("✂️ Extract Pages", key="home_btn_split", use_container_width=True):
                with st.spinner("Extracting..."):
                    op = split_pdf(sp, int(start_p), int(end_p))
                    if op:
                        with open(op,"rb") as f:
                            st.download_button("⬇️ Download Extracted PDF", data=f.read(),
                                file_name=f"pages_{start_p}-{end_p}.pdf",
                                mime="application/pdf",
                                use_container_width=True, key="home_dl_split")
            cleanup_file(sp)

    # ── TOOL: Word → PDF ─────────────────────────────────────────
    elif active == "word_pdf":
        st.markdown("### 📝 Word → PDF")
        from utils.document_utils import docx_to_pdf, LIBREOFFICE_AVAILABLE
        from utils.file_utils import save_uploaded_file, cleanup_file

        if not LIBREOFFICE_AVAILABLE:
            st.error("❌ LibreOffice not installed on this server. This feature works when running locally.")
        else:
            if st.button("📄 Convert to PDF", key="home_btn_wpdf", use_container_width=True):
                with st.spinner("Converting via LibreOffice..."):
                    sp = save_uploaded_file(routed_file)
                    if sp:
                        op = docx_to_pdf(sp)
                        if op:
                            with open(op,"rb") as f:
                                st.download_button("⬇️ Download PDF", data=f.read(),
                                    file_name=f"{Path(routed_file.name).stem}.pdf",
                                    mime="application/pdf",
                                    use_container_width=True, key="home_dl_wpdf")
                            cleanup_file(sp)

    # ── TOOL: Extract Text / OCR ──────────────────────────────────
    elif active == "extract_text":
        st.markdown("### 📋 Extract Text from Document")
        from utils.document_utils import extract_text_from_pdf
        from utils.file_utils import save_uploaded_file, cleanup_file

        if st.button("📋 Extract Text", key="home_btn_ocr", use_container_width=True):
            with st.spinner("Extracting text..."):
                sp = save_uploaded_file(routed_file)
                if sp:
                    text = extract_text_from_pdf(sp)
                    if text and text.strip():
                        wc = len(text.split())
                        st.success(f"✅ Extracted **{wc} words**")
                        st.text_area("Extracted text:", value=text, height=350, key="home_txt_area")
                        st.download_button("⬇️ Download .txt", data=text.encode("utf-8"),
                            file_name=f"{Path(routed_file.name).stem}_text.txt",
                            mime="text/plain",
                            use_container_width=True, key="home_dl_txt")
                    else:
                        st.warning("No text found. Try the OCR tab in the Document Converter for scanned PDFs.")
                    cleanup_file(sp)

# ════════════════════════════════════════════════════════════════
# STATIC FEATURE OVERVIEW (shown when no file is dropped)
# ════════════════════════════════════════════════════════════════
if not dropped_file:
    st.markdown("---")
    st.markdown("## ✨ What this app can do")

    c1, c2, c3, c4 = st.columns(4)
    cards = [
        ("🖼️", "Image Tools", "Convert • Compress to exact KB • Visual crop • Resize • Enhance • Watermark • Background removal"),
        ("🎬", "Video Tools",  "Convert formats • Compress • Trim • Extract audio • Create GIF • Merge"),
        ("🎵", "Audio Tools",  "Convert • Compress • Trim • Volume • Noise reduction • Merge"),
        ("📄", "Document Tools","Merge/Split PDF • OCR • Excel↔CSV • Word→PDF • Text extraction"),
    ]
    for col, (icon, title, desc) in zip([c1,c2,c3,c4], cards):
        col.markdown(f"""
        <div style='background:rgba(108,99,255,0.08);border:1px solid rgba(108,99,255,0.25);
             border-radius:14px;padding:1.2rem;text-align:center;height:100%;'>
            <div style='font-size:2.5rem;'>{icon}</div>
            <h3 style='color:#fff;margin:0.4rem 0;font-size:1rem;'>{title}</h3>
            <p style='color:#8B8FA8;font-size:0.82rem;line-height:1.5;'>{desc}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:rgba(0,212,170,0.08);border:1px solid rgba(0,212,170,0.25);
         border-radius:10px;padding:1rem 1.5rem;margin-top:1.5rem;font-size:0.9rem;color:rgba(255,255,255,0.8);'>
        🔒 <strong>100% Private:</strong> All processing happens on the server — your files are never shared
        and temporary files are deleted automatically after download.
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align:center;color:#8B8FA8;font-size:0.82rem;padding:0.5rem 0;'>
    🔄 MediaConvert Pro &nbsp;•&nbsp; 100% Free &nbsp;•&nbsp; No account required &nbsp;•&nbsp;
    Built with Python, Streamlit & FFmpeg
</div>
""", unsafe_allow_html=True)