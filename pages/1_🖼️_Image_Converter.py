# pages/1_🖼️_Image_Converter.py
import streamlit as st
from PIL import Image, ImageFilter, ImageEnhance
import io
import os
from pathlib import Path

# Advanced processing modules for local AI and computer vision
import cv2
import numpy as np
try:
    from rembg import remove as rembg_remove
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False

# 1. PAGE CONFIGURATION
st.set_page_config(page_title="Image Converter Studio", page_icon="🖼️", layout="wide")

st.markdown("""
<div style='background: linear-gradient(135deg, #1e1e2f 0%, #111125 100%);
     border-radius: 12px; padding: 1.5rem; text-align: center; margin-bottom: 2rem;
     border: 1px solid rgba(255,255,255,0.1);'>
    <h1 style='color: white; font-size: 2.3rem; margin: 0;'>🖼️ Image Processing & Converter Studio</h1>
    <p style='color: #8a8aa3; margin: 0.5rem 0 0;'>
        Perform local AI background removal, structural enhancements, batch pipelines, and format adjustments
    </p>
</div>
""", unsafe_allow_html=True)

# 2. INITIALIZE 10-TAB ROUTING ENGINE
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "🔄 PNG to JPG", 
    "🔄 JPG to PNG", 
    "🌐 WebP Converter", 
    "📐 Resize Image", 
    "🗜️ Compress Image", 
    "✂️ Crop Tool", 
    "🎨 Creative Filters", 
    "✨ Image Enhancer",
    "🎭 Background Remover/Adder",
    "📦 Batch Convert"
])

# Shared utility for stream compilation
def get_image_bytes(img, format_str="PNG", quality=100):
    buf = io.BytesIO()
    if format_str.upper() == "JPEG" or format_str.upper() == "JPG":
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=quality)
    else:
        img.save(buf, format=format_str.upper())
    return buf.getvalue()

# =====================================================================
# TAB 1: PNG TO JPG
# =====================================================================
with tab1:
    st.header("PNG to JPG Converter")
    uploaded_file = st.file_uploader("Upload PNG Image", type=["png"], key="png_to_jpg")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original PNG Image", use_container_width=False, width=400)
        
        if st.button("Convert to JPG", key="btn_png_jpg"):
            byte_im = get_image_bytes(image, "JPEG")
            st.success("Conversion successful!")
            st.download_button("📥 Download JPG Image", data=byte_im, file_name="converted_image.jpg", mime="image/jpeg")

# =====================================================================
# TAB 2: JPG TO PNG
# =====================================================================
with tab2:
    st.header("JPG to PNG Converter")
    uploaded_file = st.file_uploader("Upload JPG Image", type=["jpg", "jpeg"], key="jpg_to_png")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Original JPG Image", use_container_width=False, width=400)
        
        if st.button("Convert to PNG", key="btn_jpg_png"):
            byte_im = get_image_bytes(image, "PNG")
            st.success("Conversion successful!")
            st.download_button("📥 Download PNG Image", data=byte_im, file_name="converted_image.png", mime="image/png")

# =====================================================================
# TAB 3: WEBP CONVERTER
# =====================================================================
with tab3:
    st.header("Convert Any Image to WebP")
    uploaded_file = st.file_uploader("Upload Image (PNG/JPG)", type=["png", "jpg", "jpeg"], key="webp_key")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=False, width=400)
        
        if st.button("Convert to WebP", key="btn_webp"):
            byte_im = get_image_bytes(image, "WEBP")
            st.success("Converted to modern WebP format!")
            st.download_button("📥 Download WebP Image", data=byte_im, file_name="converted_image.webp", mime="image/webp")

# =====================================================================
# TAB 4: RESIZE IMAGE
# =====================================================================
with tab4:
    st.header("Resize Image Dimensions")
    uploaded_file = st.file_uploader("Upload Image to Resize", type=["png", "jpg", "jpeg"], key="resize_key")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        width, height = image.size
        st.write(f"Current Dimensions: **{width}x{height}** pixels")
        
        col1, col2 = st.columns(2)
        with col1: new_width = st.number_input("Target Width (px)", min_value=1, value=int(width))
        with col2: new_height = st.number_input("Target Height (px)", min_value=1, value=int(height))
        
        if st.button("Apply Resize", key="btn_resize"):
            resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            st.image(resized_image, caption=f"Resized Matrix Preview", use_container_width=False, width=400)
            
            fmt = image.format if image.format else "PNG"
            st.download_button("📥 Download Resized Image", get_image_bytes(resized_image, fmt), f"resized_{uploaded_file.name}")

# =====================================================================
# TAB 5: COMPRESS IMAGE
# =====================================================================
with tab5:
    st.header("Compress Image File Size")
    uploaded_file = st.file_uploader("Upload Image to Compress", type=["jpg", "jpeg"], key="compress_key")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        quality_val = st.slider("Select Quality Level (Lower % = smaller file size)", 1, 100, 70)
        
        if st.button("Compress Image", key="btn_compress"):
            byte_im = get_image_bytes(image, "JPEG", quality=quality_val)
            st.success(f"Compression Complete!")
            st.download_button("📥 Download Compressed Image", byte_im, f"compressed_{uploaded_file.name}", "image/jpeg")

# =====================================================================
# TAB 6: CROP TOOL
# =====================================================================
with tab6:
    st.header("✂️ Image Cropping Engine")
    uploaded_file = st.file_uploader("Upload Image to Crop", type=["png", "jpg", "jpeg"], key="crop_upload")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        w, h = image.size
        
        col1, col2, col3, col4 = st.columns(4)
        with col1: left = st.number_input("Left boundary coordinate", 0, w, 0)
        with col2: top = st.number_input("Top boundary coordinate", 0, h, 0)
        with col3: right = st.number_input("Right boundary coordinate", 0, w, w)
        with col4: bottom = st.number_input("Bottom boundary coordinate", 0, h, h)
            
        if right > left and bottom > top:
            if st.button("Execute Crop Operation"):
                cropped = image.crop((left, top, right, bottom))
                st.image(cropped, caption="Cropped Area Frame Preview", width=400)
                fmt = image.format if image.format else "PNG"
                st.download_button("📥 Download Cropped Image", get_image_bytes(cropped, fmt), f"cropped_{uploaded_file.name}")
        else:
            st.error("Invalid dimensions choice setup structural coordinates.")

# =====================================================================
# TAB 7: CREATIVE FILTERS
# =====================================================================
with tab7:
    st.header("🎨 Creative Image Filters")
    uploaded_file = st.file_uploader("Upload Image for Filtering", type=["png", "jpg", "jpeg"], key="filter_upload")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        filter_type = st.selectbox("Select Filter Effect Layer:", ["BLUR", "SHARPEN", "CONTOUR", "DETAIL", "SMOOTH"])
        
        if st.button("Apply Filter Layer", use_container_width=True):
            filter_map = {
                "BLUR": ImageFilter.BLUR, "SHARPEN": ImageFilter.SHARPEN,
                "CONTOUR": ImageFilter.CONTOUR, "DETAIL": ImageFilter.DETAIL, "SMOOTH": ImageFilter.SMOOTH
            }
            working_img = image.convert("RGB") if filter_type == "CONTOUR" else image
            filtered_image = working_img.filter(filter_map[filter_type])
            
            st.image(filtered_image, caption="Filtered Configuration Output", width=400)
            fmt = image.format if image.format else "PNG"
            st.download_button("📥 Download Filtered Image", get_image_bytes(filtered_image, fmt), f"filtered_{uploaded_file.name}")

# =====================================================================
# TAB 8: IMAGE ENHANCER (NEW FEATURE)
# =====================================================================
with tab8:
    st.header("✨ Advanced Image Enhancer")
    uploaded_file = st.file_uploader("Upload Image to Enhance", type=["png", "jpg", "jpeg"], key="enhance_upload")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Original Preview", use_container_width=True)
            
            # Enhancer scalar matrices adjustments setup
            brightness = st.slider("Brightness Scale Factor", 0.0, 3.0, 1.0, 0.1)
            contrast = st.slider("Contrast Scale Factor", 0.0, 3.0, 1.0, 0.1)
            sharpness = st.slider("Sharpness Scale Factor", 0.0, 5.0, 1.0, 0.1)
            color = st.slider("Color Saturation Factor", 0.0, 3.0, 1.0, 0.1)
            
            # Local OpenCV computational denoising block choice flag
            apply_denoise = st.checkbox("Apply local CV2 Denoising (Smooths out digital grain)")
            
        with col2:
            if st.button("Compute Enhancements Pipeline", use_container_width=True):
                with st.spinner("Processing enhancement balance vectors..."):
                    # Process standard PIL transformations matrix sequentially
                    curr = ImageEnhance.Brightness(image).enhance(brightness)
                    curr = ImageEnhance.Contrast(curr).enhance(contrast)
                    curr = ImageEnhance.Sharpness(curr).enhance(sharpness)
                    enhanced_img = ImageEnhance.Color(curr).enhance(color)
                    
                    # Convert to NumPy matrix if execution calls for Computer Vision filters
                    if apply_denoise:
                        img_np = np.array(enhanced_img)
                        if img_np.shape[2] == 4:  # Handle transparency transformations
                            img_np = cv2.cvtColor(img_np, cv2.cvtColor(img_np, cv2.COLOR_RGBA2RGB))
                        img_np = cv2.fastNlMeansDenoisingColored(img_np, None, 10, 10, 7, 21)
                        enhanced_img = Image.fromarray(img_np)
                        
                    st.image(enhanced_img, caption="Enhanced Result Structure", use_container_width=True)
                    fmt = image.format if image.format else "PNG"
                    st.download_button("📥 Download Enhanced Image", get_image_bytes(enhanced_img, fmt), f"enhanced_{uploaded_file.name}")

# =====================================================================
# TAB 9: BACKGROUND REMOVER & ADDER (NEW LOCAL AI ENGINE)
# =====================================================================
with tab9:
    st.header("🎭 Local AI Background Removal & Replacement")
    st.caption("Powered by automated local machine learning segmentation matrices. No APIs or internet access required.")
    
    uploaded_file = st.file_uploader("Upload Subject Image", type=["png", "jpg", "jpeg"], key="bg_upload")
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        
        col1, col2 = st.columns(2)
        with col1:
            st.image(image, caption="Target Foreground Subject Source", use_container_width=True)
            bg_mode = st.radio("Background Pipeline Logic:", ["Transparent (.png format)", "Solid Hex Color Backdrop", "Custom Image Backdrop Layer"])
            
            selected_color = "#FFFFFF"
            bg_image_file = None
            
            if bg_mode == "Solid Hex Color Backdrop":
                selected_color = st.color_picker("Choose Background Hex Vector:", "#00FF00")
            elif bg_mode == "Custom Image Backdrop Layer":
                bg_image_file = st.file_uploader("Upload Backdrop Environment Image", type=["png", "jpg", "jpeg"], key="canvas_bg")
                
        with col2:
            if st.button("Execute Segmentation Engine", use_container_width=True):
                with st.spinner("Isolating foreground contours (Initial execution downloads local u2net model)..."):
                    # Step 1: Extract clean Alpha transparency mask via rembg
                    input_bytes = uploaded_file.getvalue()
                    output_bytes = remove(input_bytes)
                    foreground = Image.open(io.BytesIO(output_bytes)).convert("RGBA")
                    
                    # Step 2: Handle composite pipeline generation logic structure
                    if bg_mode == "Transparent (.png format)":
                        final_output = foreground
                    else:
                        # Construct flat canvas platform layer mirroring parent bounds dimensions
                        canvas = Image.new("RGBA", foreground.size, (0, 0, 0, 0))
                        
                        if bg_mode == "Solid Hex Color Backdrop":
                            # Process structural hex strings to standard integer tuple representations
                            hex_val = selected_color.lstrip('#')
                            rgb_tuple = tuple(int(hex_val[i:i+2], 16) for i in (0, 2, 4))
                            bg_layer = Image.new("RGBA", foreground.size, rgb_tuple + (255,))
                            canvas = Image.alpha_composite(canvas, bg_layer)
                            
                        elif bg_mode == "Custom Image Backdrop Layer" and bg_image_file is not None:
                            bg_layer = Image.open(bg_image_file).convert("RGBA")
                            # Interpolate matching pixel canvas dimensions boundaries matrix cleanly
                            bg_layer = bg_layer.resize(foreground.size, Image.Resampling.LANCZOS)
                            canvas = Image.alpha_composite(canvas, bg_layer)
                            
                        # Overlay the alpha mask composite layer directly over background frame
                        final_output = Image.alpha_composite(canvas, foreground)
                    
                    st.image(final_output, caption="Composition Engine Output Result", use_container_width=True)
                    
                    # Route download binary extensions cleanly matching formatting choices
                    if bg_mode == "Transparent (.png format)":
                        st.download_button("📥 Download Cutout PNG", get_image_bytes(final_output, "PNG"), "cutout_transparent.png")
                    else:
                        st.download_button("📥 Download Composite Image", get_image_bytes(final_output, "JPEG"), "composite_background.jpg")

# =====================================================================
# TAB 10: BATCH CONVERT
# =====================================================================
with tab10:
    st.header("📦 Batch Process Engineering")
    uploaded_files = st.file_uploader("Upload Multiple Images", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_upload")
    
    if uploaded_files:
        target_fmt = st.selectbox("Batch Export Format Target:", ["PNG", "JPEG", "WEBP"])
        
        if st.button("Process Batch Conversion Pipeline", use_container_width=True):
            for file in uploaded_files:
                img = Image.open(file)
                buf = io.BytesIO()
                
                if target_fmt == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img.save(buf, format=target_fmt)
                
                st.success(f"Processed: {file.name} ➔ Out.{target_fmt.lower()}")
                st.download_button(f"📥 Download {Path(file.name).stem}.{target_fmt.lower()}", buf.getvalue(), f"batch_{Path(file.name).stem}.{target_fmt.lower()}")