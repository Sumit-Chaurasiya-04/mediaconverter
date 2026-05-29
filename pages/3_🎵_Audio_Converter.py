# pages/3_🎵_Audio_Converter.py
# Audio conversion and processing page

import streamlit as st
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MAX_AUDIO_SIZE_BYTES, AUDIO_BITRATE_OPTIONS, APP_NAME
from utils.file_utils import (
    save_uploaded_file, validate_file_size,
    create_download_button, cleanup_file
)
from utils.audio_utils import (
    convert_audio_format, compress_audio, trim_audio,
    adjust_volume, merge_audio_files, reduce_noise,
    get_audio_info
)
from utils.video_utils import check_ffmpeg

st.set_page_config(
    page_title=f"Audio Converter - {APP_NAME}",
    page_icon="🎵",
    layout="wide"
)

def load_css():
    css_path = os.path.join(Path(__file__).parent.parent, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# Header
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #2d1b69 50%, #11998e 100%);
     border-radius: 16px; padding: 2rem; text-align: center; margin-bottom: 2rem;
     border: 1px solid rgba(108,99,255,0.3);'>
    <h1 style='color: white; font-size: 2.5rem; margin: 0;'>🎵 Audio Converter</h1>
    <p style='color: rgba(255,255,255,0.7); margin: 0.5rem 0 0;'>
        Convert, compress, trim, and enhance audio files
    </p>
</div>
""", unsafe_allow_html=True)

# Check FFmpeg
if not check_ffmpeg():
    st.error("""
    ❌ **FFmpeg is not installed!**
    Audio processing requires FFmpeg. Please install it first (see Installation Guide).
    """)
    st.stop()

# Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "🔄 Convert Format",
    "📦 Compress",
    "✂️ Trim",
    "🔊 Volume",
    "🔇 Noise Reduction",
    "➕ Merge Audio"
])

# ============================================================
# TAB 1: FORMAT CONVERSION
# ============================================================
with tab1:
    st.markdown("#### Convert audio from one format to another")
    
    uploaded_audio = st.file_uploader(
        "Upload audio file",
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a", "wma", "opus"],
        key="audio_convert_upload"
    )
    
    if uploaded_audio is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio, MAX_AUDIO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Audio player
                st.audio(uploaded_audio)
                st.caption(f"📁 {uploaded_audio.name} | {len(uploaded_audio.getbuffer())/(1024*1024):.1f} MB")
            
            with col2:
                current_ext = Path(uploaded_audio.name).suffix.lower().lstrip(".")
                target_formats = ["mp3", "wav", "aac", "flac", "ogg", "m4a", "opus"]
                if current_ext in target_formats:
                    target_formats.remove(current_ext)
                
                target_format = st.selectbox(
                    "Convert to:",
                    target_formats,
                    format_func=lambda x: x.upper(),
                    key="audio_target_format"
                )
                
                format_descriptions = {
                    "mp3": "📌 MP3: Universal compatibility, good compression",
                    "wav": "📌 WAV: Uncompressed, perfect quality, large files",
                    "aac": "📌 AAC: Better quality than MP3 at same bitrate",
                    "flac": "📌 FLAC: Lossless compression, audiophile choice",
                    "ogg": "📌 OGG: Open source, good for web",
                    "m4a": "📌 M4A: Apple format, high quality",
                    "opus": "📌 Opus: Modern format, excellent for voice"
                }
                st.caption(format_descriptions.get(target_format, ""))
                
                if target_format not in ["wav", "flac"]:
                    bitrate_label = st.selectbox(
                        "Audio quality:",
                        list(AUDIO_BITRATE_OPTIONS.keys()),
                        index=2,
                        key="audio_bitrate"
                    )
                    bitrate = AUDIO_BITRATE_OPTIONS[bitrate_label]
                    
                    sample_rate = st.selectbox(
                        "Sample rate:",
                        [22050, 44100, 48000],
                        index=1,
                        format_func=lambda x: f"{x} Hz",
                        key="audio_sample_rate"
                    )
                else:
                    bitrate = "192k"
                    sample_rate = 44100
                    st.info(f"ℹ️ {target_format.upper()} is lossless - bitrate not applicable")
                
                if st.button("🎵 Convert Audio", key="btn_audio_convert", use_container_width=True):
                    with st.spinner(f"Converting to {target_format.upper()}..."):
                        saved_path = save_uploaded_file(uploaded_audio)
                        
                        if saved_path:
                            output_path = convert_audio_format(
                                saved_path, target_format, bitrate, sample_rate
                            )
                            
                            if output_path and os.path.exists(output_path):
                                st.success("✅ Conversion successful!")
                                audio_bytes = open(output_path, "rb").read()
                                st.audio(audio_bytes, format=f"audio/{target_format}")
                                
                                original_size = len(uploaded_audio.getbuffer()) / (1024 * 1024)
                                converted_size = os.path.getsize(output_path) / (1024 * 1024)
                                
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.metric("Original", f"{original_size:.1f} MB")
                                with col_b:
                                    st.metric("Converted", f"{converted_size:.1f} MB",
                                             delta=f"{converted_size - original_size:+.1f} MB")
                                
                                create_download_button(
                                    output_path,
                                    f"⬇️ Download {target_format.upper()}",
                                    f"{Path(uploaded_audio.name).stem}.{target_format}"
                                )
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Conversion failed.")


# ============================================================
# TAB 2: COMPRESSION
# ============================================================
with tab2:
    st.markdown("#### Reduce audio file size")
    
    uploaded_audio_c = st.file_uploader(
        "Upload audio to compress",
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="audio_compress_upload"
    )
    
    if uploaded_audio_c is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio_c, MAX_AUDIO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.audio(uploaded_audio_c)
            original_size_mb = len(uploaded_audio_c.getbuffer()) / (1024 * 1024)
            st.info(f"📊 Original size: **{original_size_mb:.1f} MB**")
            
            bitrate_options = {
                "64 kbps (Smallest, voice quality)": "64k",
                "96 kbps (Small, acceptable quality)": "96k",
                "128 kbps (Good balance)": "128k",
                "192 kbps (Good quality)": "192k"
            }
            
            bitrate_label = st.selectbox(
                "Target quality:",
                list(bitrate_options.keys()),
                index=2,
                key="audio_compress_bitrate"
            )
            bitrate = bitrate_options[bitrate_label]
            
            if st.button("📦 Compress Audio", key="btn_audio_compress", use_container_width=True):
                with st.spinner("Compressing audio..."):
                    saved_path = save_uploaded_file(uploaded_audio_c)
                    if saved_path:
                        output_path = compress_audio(saved_path, bitrate)
                        if output_path:
                            compressed_size = os.path.getsize(output_path) / (1024 * 1024)
                            reduction = (1 - compressed_size / original_size_mb) * 100
                            
                            st.success(f"✅ Compressed! Size reduced by {reduction:.1f}%")
                            audio_bytes = open(output_path, "rb").read()
                            st.audio(audio_bytes, format="audio/mp3")
                            
                            col_a, col_b, col_c = st.columns(3)
                            with col_a:
                                st.metric("Original", f"{original_size_mb:.1f} MB")
                            with col_b:
                                st.metric("Compressed", f"{compressed_size:.1f} MB")
                            with col_c:
                                st.metric("Reduction", f"{reduction:.1f}%")
                            
                            create_download_button(output_path, "⬇️ Download Compressed Audio")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Compression failed.")


# ============================================================
# TAB 3: TRIM
# ============================================================
with tab3:
    st.markdown("#### Cut audio to a specific portion")
    
    uploaded_audio_t = st.file_uploader(
        "Upload audio to trim",
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="audio_trim_upload"
    )
    
    if uploaded_audio_t is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio_t, MAX_AUDIO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.audio(uploaded_audio_t)
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown("**Start Time:**")
                start_m = st.number_input("Minutes", 0, 999, 0, key="at_sm")
                start_s = st.number_input("Seconds", 0, 59, 0, key="at_ss")
                start_time = f"00:{start_m:02d}:{start_s:02d}"
                st.info(f"Start: **{start_time}**")
            
            with col2:
                st.markdown("**End Time:**")
                end_m = st.number_input("Minutes", 0, 999, 1, key="at_em")
                end_s = st.number_input("Seconds", 0, 59, 0, key="at_es")
                end_time = f"00:{end_m:02d}:{end_s:02d}"
                st.info(f"End: **{end_time}**")
            
            total_secs = (end_m * 60 + end_s) - (start_m * 60 + start_s)
            
            if total_secs > 0:
                st.success(f"✅ Will extract **{total_secs} seconds** of audio")
                
                if st.button("✂️ Trim Audio", key="btn_audio_trim", use_container_width=True):
                    with st.spinner("Trimming audio..."):
                        saved_path = save_uploaded_file(uploaded_audio_t)
                        if saved_path:
                            output_path = trim_audio(saved_path, start_time, end_time)
                            if output_path:
                                st.success("✅ Trimmed!")
                                audio_bytes = open(output_path, "rb").read()
                                ext = Path(uploaded_audio_t.name).suffix.lstrip(".")
                                st.audio(audio_bytes, format=f"audio/{ext}")
                                create_download_button(output_path, "⬇️ Download Trimmed Audio")
                                cleanup_file(saved_path)
                            else:
                                st.error("❌ Trim failed.")
            else:
                st.error("❌ End time must be after start time")


# ============================================================
# TAB 4: VOLUME
# ============================================================
with tab4:
    st.markdown("#### Adjust audio volume")
    
    uploaded_audio_v = st.file_uploader(
        "Upload audio to adjust volume",
        type=["mp3", "wav", "aac", "flac", "ogg", "m4a"],
        key="audio_vol_upload"
    )
    
    if uploaded_audio_v is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio_v, MAX_AUDIO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.audio(uploaded_audio_v)
            
            volume_multiplier = st.slider(
                "Volume multiplier",
                min_value=0.1,
                max_value=3.0,
                value=1.0,
                step=0.1,
                help="1.0 = original, 0.5 = half volume, 2.0 = double volume",
                key="vol_mult"
            )
            
            if volume_multiplier < 1.0:
                st.info(f"🔉 Will make audio {(1-volume_multiplier)*100:.0f}% quieter")
            elif volume_multiplier > 1.0:
                st.info(f"🔊 Will make audio {(volume_multiplier-1)*100:.0f}% louder")
                if volume_multiplier > 2.0:
                    st.warning("⚠️ Very high volume boost may cause audio distortion (clipping)")
            else:
                st.info("🔊 No change in volume")
            
            if st.button("🔊 Adjust Volume", key="btn_audio_vol", use_container_width=True):
                with st.spinner("Adjusting volume..."):
                    saved_path = save_uploaded_file(uploaded_audio_v)
                    if saved_path:
                        output_path = adjust_volume(saved_path, volume_multiplier)
                        if output_path:
                            st.success("✅ Volume adjusted!")
                            audio_bytes = open(output_path, "rb").read()
                            ext = Path(uploaded_audio_v.name).suffix.lstrip(".")
                            st.audio(audio_bytes, format=f"audio/{ext}")
                            create_download_button(output_path, "⬇️ Download")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Failed.")


# ============================================================
# TAB 5: NOISE REDUCTION
# ============================================================
with tab5:
    st.markdown("#### Reduce background noise from audio")
    
    st.markdown("""
    <div class="info-box">
        ℹ️ This applies basic noise filtering. 
        Works best for constant background noises like hum, hiss, or fan noise.
        For professional noise reduction, dedicated software like Audacity (free) is recommended.
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_audio_n = st.file_uploader(
        "Upload audio for noise reduction",
        type=["mp3", "wav", "aac", "ogg", "flac"],
        key="audio_noise_upload"
    )
    
    if uploaded_audio_n is not None:
        is_valid, error_msg = validate_file_size(uploaded_audio_n, MAX_AUDIO_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.audio(uploaded_audio_n)
            
            noise_level = st.select_slider(
                "Noise reduction strength:",
                options=["light", "medium", "strong"],
                value="medium",
                key="noise_level"
            )
            
            descriptions = {
                "light": "Light filtering - preserves most of the original audio",
                "medium": "Balanced - removes moderate noise",
                "strong": "Aggressive - removes most noise but may affect audio quality"
            }
            st.caption(f"📌 {descriptions[noise_level]}")
            
            if st.button("🔇 Reduce Noise", key="btn_noise", use_container_width=True):
                with st.spinner("Applying noise reduction..."):
                    saved_path = save_uploaded_file(uploaded_audio_n)
                    if saved_path:
                        output_path = reduce_noise(saved_path, noise_level)
                        if output_path:
                            st.success("✅ Noise reduction applied!")
                            audio_bytes = open(output_path, "rb").read()
                            ext = Path(uploaded_audio_n.name).suffix.lstrip(".")
                            st.audio(audio_bytes, format=f"audio/{ext}")
                            create_download_button(output_path, "⬇️ Download Denoised Audio")
                            cleanup_file(saved_path)
                        else:
                            st.error("❌ Noise reduction failed.")


# ============================================================
# TAB 6: MERGE AUDIO
# ============================================================
with tab6:
    st.markdown("#### Merge multiple audio files into one")
    
    uploaded_audio_merge = st.file_uploader(
        "Upload audio files to merge (select multiple)",
        type=["mp3", "wav", "aac", "ogg", "flac", "m4a"],
        key="audio_merge_upload",
        accept_multiple_files=True
    )
    
    if uploaded_audio_merge and len(uploaded_audio_merge) >= 2:
        st.info(f"🎵 {len(uploaded_audio_merge)} audio files selected")
        
        for i, audio_f in enumerate(uploaded_audio_merge):
            size_mb = len(audio_f.getbuffer()) / (1024 * 1024)
            st.caption(f"  {i+1}. {audio_f.name} ({size_mb:.1f} MB)")
        
        output_format = st.selectbox(
            "Output format:",
            ["mp3", "wav", "ogg", "flac"],
            key="merge_audio_format"
        )
        
        if st.button("➕ Merge Audio Files", key="btn_merge_audio", use_container_width=True):
            with st.spinner(f"Merging {len(uploaded_audio_merge)} audio files..."):
                saved_paths = []
                for af in uploaded_audio_merge:
                    p = save_uploaded_file(af)
                    if p:
                        saved_paths.append(p)
                
                if len(saved_paths) >= 2:
                    output_path = merge_audio_files(saved_paths, output_format)
                    
                    if output_path and os.path.exists(output_path):
                        st.success("✅ Merged successfully!")
                        audio_bytes = open(output_path, "rb").read()
                        st.audio(audio_bytes, format=f"audio/{output_format}")
                        create_download_button(output_path, "⬇️ Download Merged Audio")
                    else:
                        st.error("❌ Merge failed.")
                    
                    for p in saved_paths:
                        cleanup_file(p)
    
    elif uploaded_audio_merge and len(uploaded_audio_merge) == 1:
        st.warning("Please upload at least 2 audio files to merge.")