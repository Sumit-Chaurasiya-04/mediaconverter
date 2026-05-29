# config.py
# This file stores all configuration settings for the app
# Think of it like a settings file for the entire application

import os
import tempfile

# ============================================================
# APP SETTINGS
# ============================================================

APP_NAME = "MediaConvert Pro"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Universal File Conversion & Media Processing Platform"
APP_AUTHOR = "Your Name"

# ============================================================
# FILE SIZE LIMITS
# ============================================================
# These limits protect the server from being overwhelmed
# by huge files. Adjust based on your server's RAM.

MAX_IMAGE_SIZE_MB = 50        # Maximum image file size in MB
MAX_VIDEO_SIZE_MB = 500       # Maximum video file size in MB
MAX_AUDIO_SIZE_MB = 100       # Maximum audio file size in MB
MAX_DOCUMENT_SIZE_MB = 50     # Maximum document file size in MB

# Convert MB to bytes for comparison
MAX_IMAGE_SIZE_BYTES = MAX_IMAGE_SIZE_MB * 1024 * 1024
MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_MB * 1024 * 1024
MAX_AUDIO_SIZE_BYTES = MAX_AUDIO_SIZE_MB * 1024 * 1024
MAX_DOCUMENT_SIZE_BYTES = MAX_DOCUMENT_SIZE_MB * 1024 * 1024

# ============================================================
# TEMPORARY FILE SETTINGS
# ============================================================
# We store uploaded and processed files temporarily
# They get deleted after the user downloads them

# Use the system's temp directory (works on Windows, Mac, Linux)
TEMP_DIR = tempfile.gettempdir()
UPLOAD_DIR = os.path.join(TEMP_DIR, "mediaconvert_uploads")
OUTPUT_DIR = os.path.join(TEMP_DIR, "mediaconvert_outputs")

# Create directories if they don't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ============================================================
# SUPPORTED FILE FORMATS
# ============================================================

SUPPORTED_IMAGE_FORMATS = [
    "jpg", "jpeg", "png", "webp", "bmp", "tiff", "tif",
    "gif", "ico", "svg"
]

SUPPORTED_VIDEO_FORMATS = [
    "mp4", "avi", "mov", "mkv", "webm", "flv", "wmv",
    "m4v", "3gp", "ogv"
]

SUPPORTED_AUDIO_FORMATS = [
    "mp3", "wav", "aac", "flac", "ogg", "m4a", "wma",
    "opus", "aiff"
]

SUPPORTED_DOCUMENT_FORMATS = [
    "pdf", "docx", "doc", "xlsx", "xls", "csv",
    "pptx", "ppt", "txt"
]

# ============================================================
# IMAGE QUALITY SETTINGS
# ============================================================

IMAGE_QUALITY_OPTIONS = {
    "Low (Smallest file)": 30,
    "Medium": 60,
    "High": 80,
    "Best (Largest file)": 95
}

# ============================================================
# VIDEO QUALITY SETTINGS
# ============================================================

VIDEO_QUALITY_OPTIONS = {
    "144p": "256x144",
    "240p": "426x240",
    "360p": "640x360",
    "480p": "854x480",
    "720p (HD)": "1280x720",
    "1080p (Full HD)": "1920x1080",
    "Original": None
}

VIDEO_FPS_OPTIONS = [10, 15, 24, 25, 30, 60]

# ============================================================
# AUDIO QUALITY SETTINGS
# ============================================================

AUDIO_BITRATE_OPTIONS = {
    "64 kbps (Low)": "64k",
    "128 kbps (Standard)": "128k",
    "192 kbps (Good)": "192k",
    "256 kbps (High)": "256k",
    "320 kbps (Best)": "320k"
}

AUDIO_SAMPLE_RATE_OPTIONS = {
    "22050 Hz": 22050,
    "44100 Hz (CD Quality)": 44100,
    "48000 Hz (Studio)": 48000
}

# ============================================================
# THEME SETTINGS
# ============================================================

PRIMARY_COLOR = "#6C63FF"      # Purple - main brand color
SECONDARY_COLOR = "#FF6584"    # Pink - accent color
BACKGROUND_DARK = "#0E1117"    # Dark background
BACKGROUND_LIGHT = "#FFFFFF"   # Light background
SUCCESS_COLOR = "#00D4AA"      # Green for success messages
ERROR_COLOR = "#FF4B4B"        # Red for error messages
WARNING_COLOR = "#FFA500"      # Orange for warnings