# utils/file_utils.py
# This file handles all file management operations
# Like saving uploaded files, cleaning up temp files, etc.

import os
import uuid
import shutil
import hashlib
import time
import logging
from pathlib import Path
from typing import Optional, Tuple
import streamlit as st

# Set up logging so we can see what's happening
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our config settings
from config import UPLOAD_DIR, OUTPUT_DIR

def save_uploaded_file(uploaded_file, subfolder: str = "") -> Optional[str]:
    """
    Save a file uploaded by the user to our temporary storage.
    
    Parameters:
        uploaded_file: The file object from Streamlit's file_uploader
        subfolder: Optional subfolder name inside UPLOAD_DIR
    
    Returns:
        The full path where the file was saved, or None if it failed
    
    Example:
        path = save_uploaded_file(uploaded_file)
        # path = "/tmp/mediaconvert_uploads/abc123_photo.jpg"
    """
    try:
        # Create a unique filename to avoid conflicts
        # If two people upload "photo.jpg" at the same time, they won't clash
        unique_id = str(uuid.uuid4())[:8]  # Random 8-character ID
        safe_filename = f"{unique_id}_{uploaded_file.name}"
        
        # Determine save directory
        save_dir = UPLOAD_DIR
        if subfolder:
            save_dir = os.path.join(UPLOAD_DIR, subfolder)
            os.makedirs(save_dir, exist_ok=True)
        
        # Full path where file will be saved
        file_path = os.path.join(save_dir, safe_filename)
        
        # Write the file to disk
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        logger.info(f"File saved: {file_path}")
        return file_path
        
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return None


def save_multiple_uploaded_files(uploaded_files: list) -> list:
    """
    Save multiple uploaded files at once.
    Returns a list of saved file paths.
    """
    saved_paths = []
    for uploaded_file in uploaded_files:
        path = save_uploaded_file(uploaded_file)
        if path:
            saved_paths.append(path)
    return saved_paths


def generate_output_path(input_path: str, new_extension: str, suffix: str = "") -> str:
    """
    Generate a path for the output/processed file.
    
    Parameters:
        input_path: Path to the original input file
        new_extension: The new file extension (e.g., "png", "mp4")
        suffix: Optional suffix to add to filename (e.g., "_compressed")
    
    Returns:
        Full path for the output file
    
    Example:
        output = generate_output_path("/tmp/photo.jpg", "png")
        # Returns: "/tmp/mediaconvert_outputs/photo_converted.png"
    """
    # Get just the filename without extension
    base_name = Path(input_path).stem
    
    # Remove any unique ID prefix we added earlier
    if len(base_name) > 9 and base_name[8] == "_":
        base_name = base_name[9:]  # Remove the "abc12345_" prefix
    
    # Create clean extension (remove dot if present)
    ext = new_extension.lstrip(".")
    
    # Build output filename
    output_filename = f"{base_name}{suffix}_converted.{ext}"
    
    # Full output path
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    
    return output_path


def get_file_size_mb(file_path: str) -> float:
    """
    Get file size in megabytes.
    
    Example:
        size = get_file_size_mb("/tmp/video.mp4")
        # Returns: 25.3 (meaning 25.3 MB)
    """
    size_bytes = os.path.getsize(file_path)
    size_mb = size_bytes / (1024 * 1024)
    return round(size_mb, 2)


def get_file_size_formatted(file_path: str) -> str:
    """
    Get file size as a human-readable string.
    
    Example:
        get_file_size_formatted("/tmp/photo.jpg")
        # Returns: "2.5 MB" or "450 KB"
    """
    size_bytes = os.path.getsize(file_path)
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def get_file_size_formatted_from_bytes(size_bytes: int) -> str:
    """
    Convert raw byte size into human-readable format.
    """

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def cleanup_file(file_path: str) -> bool:
    """
    Delete a temporary file to free up disk space.
    Always call this after the user downloads their file!
    
    Returns True if deleted successfully, False if there was an error.
    """
    try:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up file: {file_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting file {file_path}: {e}")
    return False


def cleanup_old_files(max_age_hours: int = 2):
    """
    Delete all temporary files older than max_age_hours.
    This prevents the server from running out of disk space.
    
    Parameters:
        max_age_hours: Files older than this many hours get deleted
    """
    current_time = time.time()
    max_age_seconds = max_age_hours * 3600
    
    for directory in [UPLOAD_DIR, OUTPUT_DIR]:
        if not os.path.exists(directory):
            continue
            
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            # Get file age
            file_age = current_time - os.path.getmtime(file_path)
            
            # Delete if too old
            if file_age > max_age_seconds:
                cleanup_file(file_path)
                logger.info(f"Auto-deleted old file: {filename}")


def validate_file_size(uploaded_file, max_size_bytes: int) -> Tuple[bool, str]:
    """
    Check if uploaded file is within the size limit.
    
    Returns:
        (True, "") if file is OK
        (False, "error message") if file is too large
    """
    file_size = len(uploaded_file.getbuffer())
    max_size_mb = max_size_bytes / (1024 * 1024)
    
    if file_size > max_size_bytes:
        actual_size_mb = file_size / (1024 * 1024)
        return False, f"File is too large ({actual_size_mb:.1f} MB). Maximum allowed: {max_size_mb:.0f} MB"
    
    return True, ""


def validate_file_extension(filename: str, allowed_extensions: list) -> Tuple[bool, str]:
    """
    Check if the file has an allowed extension.
    
    Example:
        valid, msg = validate_file_extension("photo.jpg", ["jpg", "png", "gif"])
        # valid = True, msg = ""
    """
    ext = Path(filename).suffix.lower().lstrip(".")
    
    if ext not in allowed_extensions:
        return False, f"File type '.{ext}' is not supported. Allowed types: {', '.join(allowed_extensions)}"
    
    return True, ""


def get_mime_type(file_extension: str) -> str:
    """
    Get the MIME type for a file extension.
    This is needed for proper file downloads.
    
    Example:
        get_mime_type("mp4")
        # Returns: "video/mp4"
    """
    mime_types = {
        # Images
        "jpg": "image/jpeg",
        "jpeg": "image/jpeg",
        "png": "image/png",
        "webp": "image/webp",
        "gif": "image/gif",
        "bmp": "image/bmp",
        "tiff": "image/tiff",
        "tif": "image/tiff",
        "ico": "image/x-icon",
        "svg": "image/svg+xml",
        # Videos
        "mp4": "video/mp4",
        "avi": "video/x-msvideo",
        "mov": "video/quicktime",
        "mkv": "video/x-matroska",
        "webm": "video/webm",
        "flv": "video/x-flv",
        "wmv": "video/x-ms-wmv",
        "gif": "image/gif",
        # Audio
        "mp3": "audio/mpeg",
        "wav": "audio/wav",
        "aac": "audio/aac",
        "flac": "audio/flac",
        "ogg": "audio/ogg",
        "m4a": "audio/mp4",
        "opus": "audio/opus",
        # Documents
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "csv": "text/csv",
        "txt": "text/plain",
        "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
    
    return mime_types.get(file_extension.lower(), "application/octet-stream")


def read_file_as_bytes(file_path: str) -> Optional[bytes]:
    """
    Read a file and return its contents as bytes.
    Used for serving download buttons in Streamlit.
    """
    try:
        with open(file_path, "rb") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return None


def create_download_button(
    file_path: str,
    button_label: str = "⬇️ Download File",
    file_name: Optional[str] = None
) -> bool:
    """
    Create a Streamlit download button for a processed file.
    
    Parameters:
        file_path: Path to the file to download
        button_label: Text shown on the button
        file_name: Name for the downloaded file (defaults to original name)
    
    Returns:
        True if button was created successfully
    """
    try:
        if not os.path.exists(file_path):
            st.error("Output file not found. Please try again.")
            return False
        
        # Read file contents
        file_bytes = read_file_as_bytes(file_path)
        if file_bytes is None:
            st.error("Could not read output file.")
            return False
        
        # Get file info
        if file_name is None:
            file_name = os.path.basename(file_path)
        
        ext = Path(file_path).suffix.lstrip(".")
        mime_type = get_mime_type(ext)
        file_size = get_file_size_formatted(file_path)
        
        # Show file info
        st.success(f"✅ Processing complete! File size: {file_size}")
        
        # Create download button
        st.download_button(
            label=button_label,
            data=file_bytes,
            file_name=file_name,
            mime=mime_type,
            use_container_width=True
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating download button: {e}")
        st.error(f"Error preparing download: {str(e)}")
        return False