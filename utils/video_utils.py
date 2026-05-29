# utils/video_utils.py
# All video processing functions
# We use MoviePy (Python wrapper for FFmpeg) and direct FFmpeg commands

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional, List, Tuple

from utils.file_utils import generate_output_path

logger = logging.getLogger(__name__)

# Check if FFmpeg is installed on the system
def check_ffmpeg() -> bool:
    """Check if FFmpeg is installed and available in PATH."""
    return shutil.which("ffmpeg") is not None

# Check if MoviePy is available
try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, concatenate_videoclips,
        CompositeVideoClip, TextClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available.")

FFMPEG_AVAILABLE = check_ffmpeg()


def run_ffmpeg_command(command: List[str]) -> Tuple[bool, str]:
    """
    Run an FFmpeg command and return success status and output.
    
    Parameters:
        command: List of command parts like ["ffmpeg", "-i", "input.mp4", "output.mp4"]
    
    Returns:
        (True, output) if successful
        (False, error_message) if failed
    """
    try:
        result = subprocess.run(
            command,
            capture_output=True,  # Capture both stdout and stderr
            text=True,             # Return strings instead of bytes
            timeout=300            # 5 minute timeout
        )
        
        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        return False, "Processing timed out (5 minutes limit)"
    except FileNotFoundError:
        return False, "FFmpeg not found. Please install FFmpeg first."
    except Exception as e:
        return False, str(e)


# ============================================================
# VIDEO FORMAT CONVERSION
# ============================================================

def convert_video_format(
    input_path: str,
    output_format: str,
    quality: str = "medium"
) -> Optional[str]:
    """
    Convert a video from one format to another.
    
    Parameters:
        input_path: Path to the original video
        output_format: Target format like "mp4", "avi", "webm"
        quality: "low", "medium", "high" - affects file size vs quality
    
    Returns:
        Path to converted video, or None if failed
    """
    if not FFMPEG_AVAILABLE:
        logger.error("FFmpeg not installed")
        return None
    
    try:
        output_path = generate_output_path(input_path, output_format)
        
        # Quality settings for different formats
        # CRF = Constant Rate Factor: lower = better quality, larger file
        # 18=excellent, 23=good(default), 28=acceptable, 35=poor
        quality_crf = {"low": "35", "medium": "23", "high": "18"}
        crf = quality_crf.get(quality, "23")
        
        # Build FFmpeg command based on output format
        if output_format in ["mp4", "mov", "m4v"]:
            command = [
                "ffmpeg", "-i", input_path,
                "-c:v", "libx264",      # H.264 video codec
                "-crf", crf,             # Quality
                "-preset", "medium",     # Encoding speed (slow=better quality)
                "-c:a", "aac",           # AAC audio codec
                "-b:a", "128k",          # Audio bitrate
                "-movflags", "+faststart",  # Optimizes for web streaming
                "-y",                    # Overwrite output without asking
                output_path
            ]
        elif output_format == "webm":
            command = [
                "ffmpeg", "-i", input_path,
                "-c:v", "libvp9",        # VP9 codec for WebM
                "-crf", crf,
                "-b:v", "0",             # Variable bitrate
                "-c:a", "libopus",       # Opus audio for WebM
                "-b:a", "128k",
                "-y", output_path
            ]
        elif output_format == "avi":
            command = [
                "ffmpeg", "-i", input_path,
                "-c:v", "mpeg4",         # MPEG4 for AVI
                "-q:v", "5",             # Quality (1-31, lower=better)
                "-c:a", "mp3",
                "-b:a", "128k",
                "-y", output_path
            ]
        elif output_format == "mkv":
            command = [
                "ffmpeg", "-i", input_path,
                "-c:v", "libx264",
                "-crf", crf,
                "-c:a", "copy",          # Copy audio stream without re-encoding
                "-y", output_path
            ]
        elif output_format == "gif":
            # Special handling for GIF creation
            command = [
                "ffmpeg", "-i", input_path,
                "-vf", "fps=10,scale=320:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse",
                "-loop", "0",
                "-y", output_path
            ]
        else:
            # Generic conversion
            command = [
                "ffmpeg", "-i", input_path,
                "-c:v", "copy",
                "-c:a", "copy",
                "-y", output_path
            ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Video conversion failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Video conversion error: {e}")
        return None


# ============================================================
# VIDEO COMPRESSION
# ============================================================

def compress_video(
    input_path: str,
    target_size_mb: Optional[float] = None,
    crf: int = 28,
    preset: str = "medium",
    resolution: Optional[str] = None
) -> Optional[str]:
    """
    Compress a video to reduce file size.
    
    Parameters:
        input_path: Path to original video
        target_size_mb: Target file size in MB (optional)
        crf: Quality factor 18-35 (23=default, 28=compressed, 35=very compressed)
        preset: Encoding speed - "ultrafast", "fast", "medium", "slow", "veryslow"
                (slower = better compression at same quality)
        resolution: Optional resize like "1280x720" or "854x480"
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        output_path = generate_output_path(input_path, "mp4", "_compressed")
        
        # Build video filter string
        vf_parts = []
        if resolution:
            vf_parts.append(f"scale={resolution}")
        
        command = [
            "ffmpeg", "-i", input_path,
            "-c:v", "libx264",
            "-crf", str(crf),
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "128k",
        ]
        
        if vf_parts:
            command.extend(["-vf", ",".join(vf_parts)])
        
        command.extend(["-movflags", "+faststart", "-y", output_path])
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Video compression failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Video compression error: {e}")
        return None


# ============================================================
# VIDEO TRIMMING
# ============================================================

def trim_video(
    input_path: str,
    start_time: str,
    end_time: str
) -> Optional[str]:
    """
    Trim a video to a specific time range.
    
    Parameters:
        input_path: Path to original video
        start_time: Start time in format "HH:MM:SS" or seconds like "30"
        end_time: End time in format "HH:MM:SS" or seconds like "90"
    
    Example:
        trim_video("video.mp4", "00:01:00", "00:02:30")
        # Extracts minutes 1:00 to 2:30 (90 seconds)
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_trimmed")
        
        command = [
            "ffmpeg",
            "-ss", str(start_time),      # Start time
            "-i", input_path,
            "-to", str(end_time),         # End time
            "-c", "copy",                  # Copy streams without re-encoding (fast!)
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Video trim failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Video trim error: {e}")
        return None


# ============================================================
# AUDIO EXTRACTION FROM VIDEO
# ============================================================

def extract_audio_from_video(
    input_path: str,
    output_format: str = "mp3",
    bitrate: str = "192k"
) -> Optional[str]:
    """
    Extract the audio track from a video file.
    
    Parameters:
        input_path: Path to video file
        output_format: Audio format to extract as ("mp3", "wav", "aac", "flac")
        bitrate: Audio quality ("128k", "192k", "320k")
    
    Returns:
        Path to extracted audio file
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        output_path = generate_output_path(input_path, output_format, "_audio")
        
        if output_format == "wav":
            command = [
                "ffmpeg", "-i", input_path,
                "-vn",                    # No video
                "-acodec", "pcm_s16le",   # PCM codec for WAV
                "-ar", "44100",           # Sample rate
                "-ac", "2",               # Stereo
                "-y", output_path
            ]
        elif output_format == "flac":
            command = [
                "ffmpeg", "-i", input_path,
                "-vn",
                "-acodec", "flac",
                "-y", output_path
            ]
        else:  # mp3, aac, ogg, etc.
            command = [
                "ffmpeg", "-i", input_path,
                "-vn",
                "-acodec", "libmp3lame" if output_format == "mp3" else output_format,
                "-ab", bitrate,
                "-y", output_path
            ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Audio extraction failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Audio extraction error: {e}")
        return None


# ============================================================
# VIDEO THUMBNAIL
# ============================================================

def extract_thumbnail(
    input_path: str,
    time_position: str = "00:00:05",
    width: int = 640
) -> Optional[str]:
    """
    Extract a thumbnail image from a video at a specific time.
    
    Parameters:
        input_path: Path to video file
        time_position: Time to extract frame from ("HH:MM:SS")
        width: Width of thumbnail in pixels
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        output_path = generate_output_path(input_path, "jpg", "_thumbnail")
        
        command = [
            "ffmpeg",
            "-ss", time_position,         # Seek to position
            "-i", input_path,
            "-vframes", "1",              # Extract exactly 1 frame
            "-vf", f"scale={width}:-1",   # Resize maintaining aspect ratio
            "-q:v", "2",                   # Quality (1-31, lower=better)
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Thumbnail extraction failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Thumbnail extraction error: {e}")
        return None


# ============================================================
# VIDEO INFO
# ============================================================

def get_video_info(input_path: str) -> dict:
    """
    Get detailed information about a video file using FFprobe.
    FFprobe is included with FFmpeg installation.
    """
    if not FFMPEG_AVAILABLE:
        return {}
    
    try:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            input_path
        ]
        
        result = subprocess.run(command, capture_output=True, text=True)
        
        if result.returncode == 0:
            import json
            probe_data = json.loads(result.stdout)
            
            info = {
                "duration": "Unknown",
                "size": "Unknown",
                "width": "Unknown",
                "height": "Unknown",
                "fps": "Unknown",
                "video_codec": "Unknown",
                "audio_codec": "Unknown",
                "bitrate": "Unknown"
            }
            
            # Extract format info
            if "format" in probe_data:
                fmt = probe_data["format"]
                if "duration" in fmt:
                    duration_sec = float(fmt["duration"])
                    mins = int(duration_sec // 60)
                    secs = int(duration_sec % 60)
                    info["duration"] = f"{mins:02d}:{secs:02d}"
                if "size" in fmt:
                    size_mb = int(fmt["size"]) / (1024 * 1024)
                    info["size"] = f"{size_mb:.1f} MB"
                if "bit_rate" in fmt:
                    info["bitrate"] = f"{int(fmt['bit_rate']) // 1000} kbps"
            
            # Extract stream info
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    info["width"] = stream.get("width", "Unknown")
                    info["height"] = stream.get("height", "Unknown")
                    info["video_codec"] = stream.get("codec_name", "Unknown").upper()
                    # Calculate FPS from r_frame_rate
                    fps_str = stream.get("r_frame_rate", "0/1")
                    if "/" in fps_str:
                        num, den = fps_str.split("/")
                        fps = round(int(num) / int(den), 2) if int(den) > 0 else 0
                        info["fps"] = f"{fps} fps"
                elif stream.get("codec_type") == "audio":
                    info["audio_codec"] = stream.get("codec_name", "Unknown").upper()
            
            return info
        
        return {}
        
    except Exception as e:
        logger.error(f"Error getting video info: {e}")
        return {}


# ============================================================
# CHANGE VIDEO FRAME RATE
# ============================================================

def change_frame_rate(input_path: str, target_fps: int) -> Optional[str]:
    """
    Change the frame rate (FPS) of a video.
    
    Parameters:
        input_path: Path to video
        target_fps: Target frames per second (e.g., 24, 30, 60)
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, f"_{target_fps}fps")
        
        command = [
            "ffmpeg", "-i", input_path,
            "-filter:v", f"fps={target_fps}",
            "-c:a", "copy",
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"FPS change failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"FPS change error: {e}")
        return None


# ============================================================
# MERGE VIDEOS
# ============================================================

def merge_videos(input_paths: List[str], output_format: str = "mp4") -> Optional[str]:
    """
    Merge multiple videos into one video.
    
    Parameters:
        input_paths: List of video file paths to merge
        output_format: Output format for merged video
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        # Create a text file listing all input videos
        # FFmpeg concat demuxer requires a file list
        import tempfile
        list_file = os.path.join(tempfile.gettempdir(), "ffmpeg_concat_list.txt")
        
        with open(list_file, "w") as f:
            for video_path in input_paths:
                # FFmpeg requires forward slashes even on Windows
                clean_path = video_path.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
        
        output_path = generate_output_path(input_paths[0], output_format, "_merged")
        
        command = [
            "ffmpeg",
            "-f", "concat",          # Use concat demuxer
            "-safe", "0",            # Allow absolute paths
            "-i", list_file,
            "-c", "copy",            # Copy streams (fast, no re-encoding)
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        # Clean up the list file
        if os.path.exists(list_file):
            os.remove(list_file)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Video merge failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Video merge error: {e}")
        return None