# utils/audio_utils.py
# All audio processing functions
# Uses FFmpeg for most operations

import os
import subprocess
import logging
import shutil
from pathlib import Path
from typing import Optional, List

from utils.file_utils import generate_output_path

logger = logging.getLogger(__name__)

FFMPEG_AVAILABLE = shutil.which("ffmpeg") is not None


def run_ffmpeg_command(command: List[str]):
    """Run an FFmpeg command. Returns (success, output)."""
    try:
        result = subprocess.run(
            command, capture_output=True, text=True, timeout=300
        )
        return result.returncode == 0, result.stderr
    except Exception as e:
        return False, str(e)


# ============================================================
# AUDIO FORMAT CONVERSION
# ============================================================

def convert_audio_format(
    input_path: str,
    output_format: str,
    bitrate: str = "192k",
    sample_rate: int = 44100
) -> Optional[str]:
    """
    Convert audio from one format to another.
    
    Parameters:
        input_path: Path to original audio
        output_format: Target format ("mp3", "wav", "aac", "flac", "ogg")
        bitrate: Audio quality ("64k", "128k", "192k", "256k", "320k")
        sample_rate: Sample rate in Hz (22050, 44100, 48000)
    
    Returns:
        Path to converted audio file
    """
    if not FFMPEG_AVAILABLE:
        logger.error("FFmpeg not available")
        return None
    
    try:
        output_path = generate_output_path(input_path, output_format)
        
        command = ["ffmpeg", "-i", input_path]
        
        # Set codec based on output format
        if output_format == "mp3":
            command.extend([
                "-acodec", "libmp3lame",
                "-ab", bitrate,
                "-ar", str(sample_rate)
            ])
        elif output_format == "wav":
            command.extend([
                "-acodec", "pcm_s16le",   # 16-bit PCM (standard WAV)
                "-ar", str(sample_rate),
                "-ac", "2"                 # Stereo
            ])
        elif output_format == "aac":
            command.extend([
                "-acodec", "aac",
                "-ab", bitrate,
                "-ar", str(sample_rate)
            ])
        elif output_format == "flac":
            command.extend([
                "-acodec", "flac",
                "-ar", str(sample_rate)
            ])
        elif output_format == "ogg":
            command.extend([
                "-acodec", "libvorbis",
                "-ab", bitrate,
                "-ar", str(sample_rate)
            ])
        elif output_format == "opus":
            command.extend([
                "-acodec", "libopus",
                "-ab", bitrate
            ])
        elif output_format == "m4a":
            command.extend([
                "-acodec", "aac",
                "-ab", bitrate,
                "-ar", str(sample_rate)
            ])
        else:
            command.extend(["-acodec", "copy"])
        
        command.extend(["-y", output_path])
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Audio conversion failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Audio conversion error: {e}")
        return None


# ============================================================
# AUDIO COMPRESSION
# ============================================================

def compress_audio(
    input_path: str,
    target_bitrate: str = "128k"
) -> Optional[str]:
    """
    Compress audio by reducing bitrate.
    Lower bitrate = smaller file but lower quality.
    
    Parameters:
        input_path: Path to original audio
        target_bitrate: Target bitrate ("64k", "96k", "128k", "192k")
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, "mp3", "_compressed")
        
        command = [
            "ffmpeg", "-i", input_path,
            "-acodec", "libmp3lame",
            "-ab", target_bitrate,
            "-ar", "44100",
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Audio compression failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Audio compression error: {e}")
        return None


# ============================================================
# AUDIO TRIMMING
# ============================================================

def trim_audio(
    input_path: str,
    start_time: str,
    end_time: str
) -> Optional[str]:
    """
    Trim audio to a specific time range.
    
    Parameters:
        start_time: Start time "HH:MM:SS" or just seconds "30"
        end_time: End time "HH:MM:SS" or seconds "90"
    
    Example:
        trim_audio("music.mp3", "00:00:30", "00:01:00")
        # Keeps only seconds 30 to 60
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_trimmed")
        
        command = [
            "ffmpeg",
            "-ss", str(start_time),
            "-i", input_path,
            "-to", str(end_time),
            "-c", "copy",
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Audio trim failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Audio trim error: {e}")
        return None


# ============================================================
# VOLUME ADJUSTMENT
# ============================================================

def adjust_volume(input_path: str, volume_multiplier: float = 1.5) -> Optional[str]:
    """
    Increase or decrease audio volume.
    
    Parameters:
        volume_multiplier: 
            0.5 = half volume (quieter)
            1.0 = original volume
            1.5 = 50% louder
            2.0 = double volume
    
    Note: If too loud, audio will "clip" (distort).
    Use values between 0.1 and 2.0 for best results.
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_volume")
        
        command = [
            "ffmpeg", "-i", input_path,
            "-af", f"volume={volume_multiplier}",  # Audio filter for volume
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Volume adjustment failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Volume adjustment error: {e}")
        return None


# ============================================================
# MERGE AUDIO FILES
# ============================================================

def merge_audio_files(input_paths: List[str], output_format: str = "mp3") -> Optional[str]:
    """
    Merge multiple audio files into one audio file (concatenate them).
    
    Parameters:
        input_paths: List of audio file paths
        output_format: Output format for merged audio
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        import tempfile
        list_file = os.path.join(tempfile.gettempdir(), "ffmpeg_audio_concat.txt")
        
        with open(list_file, "w") as f:
            for audio_path in input_paths:
                clean_path = audio_path.replace("\\", "/")
                f.write(f"file '{clean_path}'\n")
        
        output_path = generate_output_path(input_paths[0], output_format, "_merged")
        
        command = [
            "ffmpeg",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c", "copy",
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if os.path.exists(list_file):
            os.remove(list_file)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Audio merge failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Audio merge error: {e}")
        return None


# ============================================================
# NOISE REDUCTION (Basic)
# ============================================================

def reduce_noise(input_path: str, noise_reduction_level: str = "medium") -> Optional[str]:
    """
    Apply basic noise reduction to audio.
    
    Note: This is a simple high-pass + low-pass filter approach.
    For professional noise reduction, specialized tools are needed.
    
    Parameters:
        noise_reduction_level: "light", "medium", or "strong"
    """
    if not FFMPEG_AVAILABLE:
        return None
    
    try:
        ext = Path(input_path).suffix.lower().lstrip(".")
        output_path = generate_output_path(input_path, ext, "_denoised")
        
        # High-pass filter removes low-frequency rumble
        # Low-pass filter removes high-frequency hiss
        # afftdn is FFmpeg's noise reduction filter
        if noise_reduction_level == "light":
            af = "afftdn=nf=-20"
        elif noise_reduction_level == "medium":
            af = "afftdn=nf=-25,highpass=f=80,lowpass=f=8000"
        else:  # strong
            af = "afftdn=nf=-35,highpass=f=100,lowpass=f=7000"
        
        command = [
            "ffmpeg", "-i", input_path,
            "-af", af,
            "-y", output_path
        ]
        
        success, output = run_ffmpeg_command(command)
        
        if success and os.path.exists(output_path):
            return output_path
        else:
            logger.error(f"Noise reduction failed: {output}")
            return None
            
    except Exception as e:
        logger.error(f"Noise reduction error: {e}")
        return None


# ============================================================
# AUDIO INFO
# ============================================================

def get_audio_info(input_path: str) -> dict:
    """Get information about an audio file."""
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
            
            info = {}
            
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
            
            for stream in probe_data.get("streams", []):
                if stream.get("codec_type") == "audio":
                    info["codec"] = stream.get("codec_name", "Unknown").upper()
                    info["channels"] = "Stereo" if stream.get("channels", 1) == 2 else "Mono"
                    info["sample_rate"] = f"{stream.get('sample_rate', 'Unknown')} Hz"
                    break
            
            return info
        
        return {}
        
    except Exception as e:
        logger.error(f"Error getting audio info: {e}")
        return {}