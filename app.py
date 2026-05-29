# app.py
# This is the MAIN file - the home page of our application
# When you run "streamlit run app.py", this is what shows first

import streamlit as st
import os
import sys
from pathlib import Path

import logging
# Mute the specific moviepy warning from streamlit's video utils
logging.getLogger("streamlit.runtime.uploaded_file_manager").setLevel(logging.ERROR) 
logging.getLogger("utils.video_utils").setLevel(logging.ERROR)

# Add project root to Python path so imports work
sys.path.insert(0, str(Path(__file__).parent))

# Import our config
from config import APP_NAME, APP_VERSION, APP_DESCRIPTION

# ============================================================
# PAGE CONFIGURATION
# Must be the FIRST Streamlit command!
# ============================================================
st.set_page_config(
    page_title=f"{APP_NAME} - Universal File Converter",
    page_icon="🔄",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://github.com/yourusername/mediaconverter",
        "Report a bug": "https://github.com/yourusername/mediaconverter/issues",
        "About": f"## {APP_NAME}\nVersion {APP_VERSION}\n\n{APP_DESCRIPTION}"
    }
)

# ============================================================
# LOAD CUSTOM CSS
# ============================================================
def load_css():
    """Load our custom CSS styles."""
    css_path = os.path.join(os.path.dirname(__file__), "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# CLEAN UP OLD TEMP FILES
# ============================================================
from utils.file_utils import cleanup_old_files
cleanup_old_files(max_age_hours=2)

# ============================================================
# SIDEBAR NAVIGATION
# ============================================================
with st.sidebar:
    # Logo/App name
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0;'>
        <div style='font-size: 3rem;'>🔄</div>
        <h2 style='color: #6C63FF; margin: 0.5rem 0;'>MediaConvert</h2>
        <p style='color: #8B8FA8; font-size: 0.85rem;'>Universal File Converter</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Navigation links
    st.markdown("### 🗂️ Navigation")
    
    pages = {
        "🏠 Home": "Home",
        "🖼️ Image Converter": "pages/1_🖼️_Image_Converter.py",
        "🎬 Video Converter": "pages/2_🎬_Video_Converter.py",
        "🎵 Audio Converter": "pages/3_🎵_Audio_Converter.py",
        "📄 Document Converter": "pages/4_📄_Document_Converter.py"
    }
    
    st.markdown("Use the **sidebar pages** above to navigate!")
    
    st.markdown("---")
    
    # System status
    st.markdown("### ⚙️ System Status")
    
    # Check which tools are available
    import shutil
    
    status_items = [
        ("FFmpeg", shutil.which("ffmpeg") is not None),
        ("Tesseract OCR", shutil.which("tesseract") is not None),
        ("LibreOffice", shutil.which("libreoffice") is not None or shutil.which("soffice") is not None),
    ]
    
    for tool, available in status_items:
        icon = "✅" if available else "❌"
        color = "#00D4AA" if available else "#FF4B4B"
        st.markdown(
            f'<div style="color: {color}; font-size: 0.85rem;">{icon} {tool}</div>',
            unsafe_allow_html=True
        )
    
    # Python package status
    packages = [
        ("Pillow (Images)", "PIL"),
        ("MoviePy (Videos)", "moviepy"),
        ("PyPDF2 (PDFs)", "PyPDF2"),
        ("Pandas (Excel)", "pandas"),
        ("rembg (BG Remove)", "rembg"),
    ]
    
    for pkg_name, import_name in packages:
        try:
            __import__(import_name)
            st.markdown(
                f'<div style="color: #00D4AA; font-size: 0.85rem;">✅ {pkg_name}</div>',
                unsafe_allow_html=True
            )
        except ImportError:
            st.markdown(
                f'<div style="color: #FFA500; font-size: 0.85rem;">⚠️ {pkg_name}</div>',
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    st.markdown(
        '<div style="font-size: 0.75rem; color: #8B8FA8; text-align: center;">'
        f'v{APP_VERSION} • 100% Free & Open Source'
        '</div>',
        unsafe_allow_html=True
    )


# ============================================================
# MAIN PAGE CONTENT
# ============================================================

# Hero Section
st.markdown("""
<div class="hero-section">
    <h1>🔄 MediaConvert Pro</h1>
    <p>Universal File Conversion & Media Processing Platform</p>
    <p style="margin-top: 0.5rem; font-size: 1rem; opacity: 0.8;">
        Convert • Compress • Enhance • Process — All for FREE
    </p>
</div>
""", unsafe_allow_html=True)

# Stats Row
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">🖼️</span>
        <h3>Image Tools</h3>
        <p>20+ operations including conversion, compression, enhancement, background removal</p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">🎬</span>
        <h3>Video Tools</h3>
        <p>Convert, compress, trim, extract audio, create GIFs, merge videos</p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">🎵</span>
        <h3>Audio Tools</h3>
        <p>Convert formats, compress, trim, adjust volume, merge audio files</p>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">📄</span>
        <h3>Document Tools</h3>
        <p>Merge/split PDFs, OCR text extraction, Excel↔CSV, DOC conversions</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Quick Start Guide
st.markdown("## 🚀 How to Use")

step_col1, step_col2, step_col3 = st.columns(3)

with step_col1:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">📁</span>
        <h3>Step 1: Choose Tool</h3>
        <p>Click on one of the converter pages in the left sidebar based on your file type</p>
    </div>
    """, unsafe_allow_html=True)

with step_col2:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">⬆️</span>
        <h3>Step 2: Upload File</h3>
        <p>Drag and drop your file or click to browse. Select your conversion settings</p>
    </div>
    """, unsafe_allow_html=True)

with step_col3:
    st.markdown("""
    <div class="feature-card">
        <span class="icon">⬇️</span>
        <h3>Step 3: Download</h3>
        <p>Click the Convert button and download your processed file instantly</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Feature list
st.markdown("## ✨ All Features")

col_a, col_b = st.columns(2)

with col_a:
    st.markdown("""
    **🖼️ Image Features:**
    - JPG ↔ PNG ↔ WEBP ↔ BMP ↔ TIFF conversion
    - ICO file generator (icon files)
    - Image compression (reduce file size)
    - Image resizing with aspect ratio
    - Image cropping
    - Rotation & flipping
    - Brightness, contrast, saturation, sharpness adjustment
    - Add text watermarks
    - Convert to grayscale (black & white)
    - Background removal (AI-powered)
    - Convert image(s) to PDF
    - Sharpen blurry images
    
    **🎬 Video Features:**
    - MP4 ↔ AVI ↔ MOV ↔ MKV ↔ WEBM conversion
    - Video compression
    - Video trimming (cut a portion)
    - Extract audio from video
    - Generate GIF from video
    - Extract thumbnail image
    - Change frame rate (FPS)
    - Merge multiple videos
    """)

with col_b:
    st.markdown("""
    **🎵 Audio Features:**
    - MP3 ↔ WAV ↔ AAC ↔ FLAC ↔ OGG conversion
    - Audio compression
    - Audio trimming
    - Volume adjustment
    - Basic noise reduction
    - Merge multiple audio files
    
    **📄 Document Features:**
    - Merge multiple PDFs into one
    - Split PDF into pages
    - PDF compression
    - Extract text from PDF
    - OCR (read text from images/scanned docs)
    - Excel ↔ CSV conversion
    - Word document to PDF (requires LibreOffice)
    - PowerPoint to PDF (requires LibreOffice)
    
    **🔒 Security & Privacy:**
    - All processing happens locally on your computer
    - Files are automatically deleted after processing
    - No files sent to external servers
    - No account required
    """)

# Privacy notice
st.markdown("""
<div class="info-box">
    🔒 <strong>100% Private:</strong> All file processing happens on YOUR computer. 
    Your files are NEVER uploaded to any external server. 
    Temporary files are automatically deleted after download.
</div>
""", unsafe_allow_html=True)

# Footer
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #8B8FA8; font-size: 0.85rem; padding: 1rem 0;">
    <p>🔄 MediaConvert Pro • 100% Free & Open Source • No Account Required</p>
    <p>Built with ❤️ using Python, Streamlit, FFmpeg, and Pillow</p>
</div>
""", unsafe_allow_html=True)