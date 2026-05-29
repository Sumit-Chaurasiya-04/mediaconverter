# pages/2_🎬_Video_Converter.py
# Video conversion and processing page

import streamlit as st
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MAX_VIDEO_SIZE_BYTES, APP_NAME
from utils.file_utils import (
    save_uploaded_file, save_multiple_uploaded_files,
    validate_file_size, get_file_size_formatted,
    create_download_button, cleanup_file
)
from utils.video_utils import (
    convert_video_format, compress_video, trim_video,
    extract_audio_from_video, extract_thumbnail,
    get_video_info, change_frame_rate, merge_videos,
    check_ffmpeg
)

st.set_page_config(
    page_title=f"Video Converter - {APP_NAME}",
    page_icon="🎬",
    layout="wide"
)

def load_css():
    css_path = os.path.join(Path(__file__).parent.parent, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Page header
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
     border-radius: 16px; padding: 2rem; text-align: center; margin-bottom: 2rem;
     border: 1px solid rgba(108,99,255,0.3);'>
    <h1 style='color: white; font-size: 2.5rem; margin: 0;'>🎬 Video Converter</h1>
    <p style='color: rgba(255,255,255,0.7); margin: 0.5rem 0 0;'>
        Convert, compress, trim, and process videos
    </p>
</div>
""", unsafe_allow_html=True)

# Check FFmpeg
if not check_ffmpeg():
    st.error("""
    ❌ **FFmpeg is not installed!**
    
    Video processing requires FFmpeg. Please install it:
    
    **Windows:**
    1. Download from: https://ffmpeg.org/download.html
    2. Extract to `C:\\ffmpeg`
    3. Add `C:\\ffmpeg\\bin` to Windows PATH (see Installation Guide)
    
    Then restart VS Code and try again.
    """)
    st.stop()

# Tabs for different operations
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🔄 Convert Format",
    "📦 Compress",
    "✂️ Trim",
    "🎵 Extract Audio",
    "🖼️ Thumbnail",
    "🔢 Change FPS",
    "🎞️ Create GIF",
    "➕ Merge Videos"
])

# ============================================================
# TAB 1: FORMAT CONVERSION
# ============================================================
with tab1:
    st.markdown("#### Convert video to a different format")
    
    st.markdown("""
    <div class="info-box">
        ⏰ Video processing takes longer than images. Please be patient!
        Processing time depends on file size and your computer speed.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_video = st.file_uploader(
        "Upload video file",
        type=["mp4", "avi", "mov", "mkv", "webm", "flv", "wmv", "m4v"],
        key="video_convert_upload",
        help="Maximum file size: 500MB"
    )
    
    if uploaded_video is not None:
        is_valid, error_msg = validate_file_size(uploaded_video, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Show file info
                file_size_mb = len(uploaded_video.getbuffer()) / (1024 * 1024)
                st.markdown(f"""
                **Uploaded File:**
                - 📁 Name: `{uploaded_video.name}`
                - 📊 Size: `{file_size_mb:.1f} MB`
                """)
                
                # Video preview (only works for MP4/WebM in browser)
                ext = Path(uploaded_video.name).suffix.lower()
                if ext in [".mp4", ".webm"]:
                    st.video(uploaded_video)
                else:
                    st.info(f"Preview not available for {ext} format. Processing will still work.")
            
            with col2:
                current_ext = Path(uploaded_video.name).suffix.lower().lstrip(".")
                
                target_formats = ["mp4", "avi", "mov", "mkv", "webm", "gif"]
                if current_ext in target_formats:
                    target_formats.remove(current_ext)
                
                target_format = st.selectbox(
                    "Convert to:",
                    target_formats,
                    format_func=lambda x: x.upper(),
                    key="video_target_format"
                )
                
                quality = st.select_slider(
                    "Quality:",
                    options=["low", "medium", "high"],
                    value="medium",
                    key="video_quality"
                )
                
                format_info = {
                    "mp4": "📌 MP4: Most compatible format. Works everywhere. Best choice for most uses.",
                    "avi": "📌 AVI: Old Windows format. Large file size but very compatible.",
                    "mov": "📌 MOV: Apple QuickTime format. Good quality.",
                    "mkv": "📌 MKV: Open format, supports multiple audio/subtitle tracks.",
                    "webm": "📌 WEBM: Web optimized. Best for web embedding.",
                    "gif": "📌 GIF: Animated image. No audio. Best for short clips <10 seconds."
                }
                st.info(format_info.get(target_format, ""))
                
                st.warning(f"⏰ Processing a {file_size_mb:.0f} MB video may take several minutes.")
                
                if st.button("🎬 Convert Video", key="btn_video_convert", use_container_width=True):
                    with st.spinner(f"Converting to {target_format.upper()}... Please wait, this may take a few minutes."):
                        progress_bar = st.progress(0, text="Saving uploaded file...")
                        saved_path = save_uploaded_file(uploaded_video)
                        progress_bar.progress(20, text="Processing video...")
                        
                        if saved_path:
                            output_path = convert_video_format(saved_path, target_format, quality)
                            progress_bar.progress(90, text="Finalizing...")
                            
                            if output_path and os.path.exists(output_path):
                                progress_bar.progress(100, text="Done!")
                                original_size_mb = file_size_mb
                                converted_size_mb = os.path.getsize(output_path) / (1024 * 1024)
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Original Size", f"{original_size_mb:.1f} MB")
                                with col_b:
                                    st.metric("Converted Size", f"{converted_size_mb:.1f} MB",
                                             delta=f"{converted_size_mb - original_size_mb:+.1f} MB")
                                
                                create_download_button(
                                    output_path,
                                    f"⬇️ Download {target_format.upper()} Video",
                                    f"{Path(uploaded_video.name).stem}.{target_format}"
                                )
                                cleanup_file(saved_path)
                            else:
                                progress_bar.empty()
                                st.error("❌ Conversion failed. Make sure FFmpeg is properly installed.")
                        else:
                            st.error("❌ Failed to save uploaded file.")


# ============================================================
# TAB 2: COMPRESSION
# ============================================================
with tab2:
    st.markdown("#### Reduce video file size")
    
    uploaded_compress_v = st.file_uploader(
        "Upload video to compress",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="video_compress_upload"
    )
    
    if uploaded_compress_v is not None:
        is_valid, error_msg = validate_file_size(uploaded_compress_v, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            file_size_mb = len(uploaded_compress_v.getbuffer()) / (1024 * 1024)
            st.info(f"📊 Original file size: **{file_size_mb:.1f} MB**")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                crf = st.slider(
                    "Compression Level (CRF)",
                    min_value=18, max_value=51,
                    value=28,
                    help="Lower = better quality, larger file. Higher = worse quality, smaller file. 28 is a good balance.",
                    key="compress_v_crf"
                )
                
                if crf <= 23:
                    st.success("✅ High quality - minimal visible quality loss")
                elif crf <= 30:
                    st.info("📌 Good balance - moderate compression")
                elif crf <= 38:
                    st.warning("⚠️ High compression - noticeable quality reduction")
                else:
                    st.error("❌ Very high compression - poor quality")
                
                preset = st.select_slider(
                    "Encoding speed:",
                    options=["ultrafast", "fast", "medium", "slow"],
                    value="medium",
                    help="Slower = better compression at same quality but takes longer",
                    key="compress_v_preset"
                )
            
            with col2:
                resize_video = st.checkbox("Also reduce resolution?", key="compress_v_resize")
                resolution = None
                
                if resize_video:
                    res_choice = st.selectbox(
                        "Target resolution:",
                        ["1920x1080 (Full HD)", "1280x720 (HD)", "854x480 (480p)", "640x360 (360p)"],
                        key="compress_v_res"
                    )
                    resolution = res_choice.split(" ")[0]
                
                st.warning(f"⏰ Compressing {file_size_mb:.0f} MB video may take several minutes.")
                
                if st.button("📦 Compress Video", key="btn_compress_v", use_container_width=True):
                    with st.spinner("Compressing video... Please be patient."):
                        saved_path = save_uploaded_file(uploaded_compress_v)
                        
                        if saved_path:
                            output_path = compress_video(saved_path, None, crf, preset, resolution)
                            
                            if output_path and os.path.exists(output_path):
                                original_mb = file_size_mb
                                compressed_mb = os.path.getsize(output_path) / (1024 * 1024)
                                reduction = (1 - compressed_mb / original_mb) * 100
                                
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Original", f"{original_mb:.1f} MB")
                                with col_b:
                                    st.metric("Compressed", f"{compressed_mb:.1f} MB")
                                with col_c:
                                    st.metric("Reduction", f"{reduction:.1f}%")
                                
                                create_download_button(output_path, "⬇️ Download Compressed Video")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Compression failed.")


# ============================================================
# TAB 3: TRIM
# ============================================================
with tab3:
    st.markdown("#### Cut/trim video to a specific portion")
    
    uploaded_trim_v = st.file_uploader(
        "Upload video to trim",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="video_trim_upload"
    )
    
    if uploaded_trim_v is not None:
        is_valid, error_msg = validate_file_size(uploaded_trim_v, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            ext = Path(uploaded_trim_v.name).suffix.lower()
            if ext in [".mp4", ".webm"]:
                st.video(uploaded_trim_v)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Set Start Time:**")
                start_h = st.number_input("Hours", 0, 23, 0, key="trim_sh")
                start_m = st.number_input("Minutes", 0, 59, 0, key="trim_sm")
                start_s = st.number_input("Seconds", 0, 59, 0, key="trim_ss")
                start_time = f"{start_h:02d}:{start_m:02d}:{start_s:02d}"
                st.info(f"Start: **{start_time}**")
            
            with col2:
                st.markdown("**Set End Time:**")
                end_h = st.number_input("Hours", 0, 23, 0, key="trim_eh")
                end_m = st.number_input("Minutes", 0, 59, 1, key="trim_em")
                end_s = st.number_input("Seconds", 0, 59, 0, key="trim_es")
                end_time = f"{end_h:02d}:{end_m:02d}:{end_s:02d}"
                st.info(f"End: **{end_time}**")
            
            duration_secs = ((end_h - start_h) * 3600 + 
                           (end_m - start_m) * 60 + 
                           (end_s - start_s))
            
            if duration_secs > 0:
                st.success(f"✅ Will extract **{duration_secs} seconds** of video")
            else:
                st.error("❌ End time must be after start time")
            
            if duration_secs > 0 and st.button("✂️ Trim Video", key="btn_trim_v", use_container_width=True):
                with st.spinner("Trimming video..."):
                    saved_path = save_uploaded_file(uploaded_trim_v)
                    if saved_path:
                        output_path = trim_video(saved_path, start_time, end_time)
                        if output_path:
                            create_download_button(output_path, "⬇️ Download Trimmed Video")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Trimming failed.")


# ============================================================
# TAB 4: EXTRACT AUDIO
# ============================================================
with tab4:
    st.markdown("#### Extract audio track from video")
    
    uploaded_audio_ex = st.file_uploader(
        "Upload video to extract audio from",
        type=["mp4", "avi", "mov", "mkv", "webm", "flv"],
        key="audio_extract_upload"
    )
    
    if uploaded_audio_ex is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio_ex, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"**File:** `{uploaded_audio_ex.name}`")
                
                audio_format = st.selectbox(
                    "Extract as:",
                    ["mp3", "wav", "aac", "flac", "ogg"],
                    key="audio_ex_format"
                )
                
                format_info = {
                    "mp3": "MP3: Most compatible, good compression",
                    "wav": "WAV: Uncompressed, perfect quality, large file",
                    "aac": "AAC: Better quality than MP3 at same size",
                    "flac": "FLAC: Lossless compressed, excellent quality",
                    "ogg": "OGG: Open format, good quality"
                }
                st.caption(f"📌 {format_info[audio_format]}")
            
            with col2:
                if audio_format != "wav" and audio_format != "flac":
                    bitrate_options = {
                        "128 kbps (Standard)": "128k",
                        "192 kbps (Good)": "192k",
                        "256 kbps (High)": "256k",
                        "320 kbps (Best)": "320k"
                    }
                    bitrate_label = st.selectbox(
                        "Audio quality:",
                        list(bitrate_options.keys()),
                        index=1,
                        key="audio_ex_bitrate"
                    )
                    bitrate = bitrate_options[bitrate_label]
                else:
                    bitrate = "192k"
                    st.info(f"ℹ️ {audio_format.upper()} is {'lossless' if audio_format == 'flac' else 'uncompressed'} — quality not applicable")
            
            if st.button("🎵 Extract Audio", key="btn_audio_ex", use_container_width=True):
                with st.spinner("Extracting audio..."):
                    saved_path = save_uploaded_file(uploaded_audio_ex)
                    if saved_path:
                        output_path = extract_audio_from_video(saved_path, audio_format, bitrate)
                        if output_path:
                            st.success("✅ Audio extracted!")
                            # Show audio player
                            audio_bytes = open(output_path, "rb").read()
                            st.audio(audio_bytes, format=f"audio/{audio_format}")
                            create_download_button(
                                output_path,
                                f"⬇️ Download {audio_format.upper()} Audio",
                                f"{Path(uploaded_audio_ex.name).stem}.{audio_format}"
                            )
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Audio extraction failed.")


# ============================================================
# TAB 5: THUMBNAIL
# ============================================================
with tab5:
    st.markdown("#### Extract a thumbnail image from video")
    
    uploaded_thumb = st.file_uploader(
        "Upload video",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="thumb_upload"
    )
    
    if uploaded_thumb is not None:
        is_valid, error_msg = validate_file_size(uploaded_thumb, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                thumb_h = st.number_input("At hour:", 0, 23, 0, key="thumb_h")
                thumb_m = st.number_input("At minute:", 0, 59, 0, key="thumb_m")
                thumb_s = st.number_input("At second:", 0, 59, 5, key="thumb_s")
                time_position = f"{thumb_h:02d}:{thumb_m:02d}:{thumb_s:02d}"
                st.info(f"Will grab frame at: **{time_position}**")
            
            with col2:
                thumb_width = st.select_slider(
                    "Thumbnail width:",
                    options=[320, 480, 640, 1280, 1920],
                    value=640,
                    key="thumb_width"
                )
                
            if st.button("📸 Extract Thumbnail", key="btn_thumb", use_container_width=True):
                with st.spinner("Extracting thumbnail..."):
                    saved_path = save_uploaded_file(uploaded_thumb)
                    if saved_path:
                        output_path = extract_thumbnail(saved_path, time_position, thumb_width)
                        if output_path:
                            st.image(output_path, caption=f"Thumbnail at {time_position}", use_container_width=True)
                            create_download_button(output_path, "⬇️ Download Thumbnail")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Thumbnail extraction failed. Try a different time position.")


# ============================================================
# TAB 6: CHANGE FPS
# ============================================================
with tab6:
    st.markdown("#### Change video frame rate (FPS)")
    
    st.info("""
    **What is FPS?**
    FPS = Frames Per Second. Higher FPS = smoother video but larger file.
    - 24 FPS: Cinema standard, slight motion blur
    - 30 FPS: Standard web/TV
    - 60 FPS: Super smooth, gaming/sports
    - 15 FPS: Choppy but very small file size
    """)
    
    uploaded_fps = st.file_uploader(
        "Upload video",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="fps_upload"
    )
    
    if uploaded_fps is not None:
        is_valid, error_msg = validate_file_size(uploaded_fps, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            target_fps = st.select_slider(
                "Target FPS:",
                options=[10, 15, 24, 25, 30, 60],
                value=30,
                key="target_fps"
            )
            
            if st.button("🔢 Change FPS", key="btn_fps", use_container_width=True):
                with st.spinner(f"Changing FPS to {target_fps}..."):
                    saved_path = save_uploaded_file(uploaded_fps)
                    if saved_path:
                        output_path = change_frame_rate(saved_path, target_fps)
                        if output_path:
                            create_download_button(output_path, "⬇️ Download Video")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ FPS change failed.")


# ============================================================
# TAB 7: CREATE GIF
# ============================================================
with tab7:
    st.markdown("#### Create animated GIF from video")
    
    st.info("""
    **Tips for good GIFs:**
    - Use short clips (under 10 seconds) for smaller file size
    - Lower FPS (8-12) creates smaller GIFs
    - Smaller width = much smaller file size
    - GIFs can get very large with long clips!
    """)
    
    uploaded_gif = st.file_uploader(
        "Upload video to convert to GIF",
        type=["mp4", "avi", "mov", "mkv", "webm"],
        key="gif_upload"
    )
    
    if uploaded_gif is not None:
        is_valid, error_msg = validate_file_size(uploaded_gif, MAX_VIDEO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                gif_h = st.number_input("Start (hours):", 0, 23, 0, key="gif_sh")
                gif_m = st.number_input("Start (minutes):", 0, 59, 0, key="gif_sm")
                gif_s = st.number_input("Start (seconds):", 0, 59, 0, key="gif_ss")
                gif_start = f"{gif_h:02d}:{gif_m:02d}:{gif_s:02d}"
            
            with col2:
                gif_duration = st.slider("Duration (seconds):", 1, 30, 5, key="gif_dur")
                gif_width = st.select_slider("GIF width (px):", options=[160, 240, 320, 480, 640], value=320, key="gif_w")
                gif_fps = st.slider("FPS:", 5, 30, 10, key="gif_fps")
            
            # Estimate file size
            estimated_mb = (gif_width * (gif_width * 0.5625) * gif_fps * gif_duration * 3) / (1024 * 1024 * 8)
            st.warning(f"⚠️ Estimated GIF size: ~{estimated_mb:.0f} MB (actual size varies)")
            
            if st.button("🎞️ Create GIF", key="btn_gif", use_container_width=True):
                with st.spinner("Creating GIF... This may take a while for longer clips."):
                    saved_path = save_uploaded_file(uploaded_gif)
                    
                    if saved_path:
                        # Trim first, then convert to GIF
                        end_time_secs = (gif_h * 3600 + gif_m * 60 + gif_s) + gif_duration
                        end_h = end_time_secs // 3600
                        end_m = (end_time_secs % 3600) // 60
                        end_s = end_time_secs % 60
                        end_time = f"{int(end_h):02d}:{int(end_m):02d}:{int(end_s):02d}"
                        
                        trimmed = trim_video(saved_path, gif_start, end_time)
                        
                        if trimmed:
                            output_path = convert_video_format(trimmed, "gif")
                            
                            if output_path and os.path.exists(output_path):
                                gif_size = os.path.getsize(output_path) / (1024 * 1024)
                                st.image(output_path, caption=f"Animated GIF ({gif_size:.1f} MB)", use_container_width=True)
                                create_download_button(output_path, "⬇️ Download GIF")
                            else:
                                st.error("❌ GIF creation failed.")
                            
                            cleanup_file(trimmed)
                        cleanup_file(saved_path)


# ============================================================
# TAB 8: MERGE VIDEOS
# ============================================================
with tab8:
    st.markdown("#### Merge multiple videos into one")
    
    st.warning("""
    ⚠️ **Important:** For best results, all videos should have:
    - Same resolution (e.g., all 1080p)
    - Same frame rate (e.g., all 30 FPS)  
    - Same codec (e.g., all MP4/H.264)
    
    Otherwise, re-encoding may be needed which takes longer.
    """)
    
    uploaded_merge_videos = st.file_uploader(
        "Upload videos to merge (select multiple)",
        type=["mp4", "avi", "mov", "mkv"],
        key="merge_videos_upload",
        accept_multiple_files=True
    )
    
    if uploaded_merge_videos and len(uploaded_merge_videos) >= 2:
        st.info(f"📁 {len(uploaded_merge_videos)} videos selected")
        
        for i, v in enumerate(uploaded_merge_videos):
            size_mb = len(v.getbuffer()) / (1024 * 1024)
            st.caption(f"  {i+1}. {v.name} ({size_mb:.1f} MB)")
        
        if st.button("➕ Merge Videos", key="btn_merge_v", use_container_width=True):
            with st.spinner(f"Merging {len(uploaded_merge_videos)} videos..."):
                saved_paths = []
                for v in uploaded_merge_videos:
                    p = save_uploaded_file(v)
                    if p:
                        saved_paths.append(p)
                
                if len(saved_paths) >= 2:
                    output_path = merge_videos(saved_paths)
                    
                    if output_path and os.path.exists(output_path):
                        output_mb = os.path.getsize(output_path) / (1024 * 1024)
                        st.success(f"✅ Merged! Output size: {output_mb:.1f} MB")
                        create_download_button(output_path, "⬇️ Download Merged Video")
                    else:
                        st.error("❌ Merge failed. Check that videos have compatible formats.")
                    
                    for p in saved_paths:
                        cleanup_file(p)
    
    elif uploaded_merge_videos and len(uploaded_merge_videos) == 1:
        st.warning("Please upload at least 2 videos to merge.")