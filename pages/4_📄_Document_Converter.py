# pages/4_📄_Document_Converter.py
# Document conversion and processing page

import streamlit as st
import os
import sys
import pytesseract
from pathlib import Path
from PIL import Image
import io

# ============================================================
# 1. STREAMLIT PAGE INITIALIZATION (MUST BE FIRST EXECUTABLE)
# ============================================================
# Tesseract path configuration mapped cleanly to system binaries
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# System routing configurations
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MAX_DOCUMENT_SIZE_BYTES, APP_NAME
from utils.file_utils import (
    save_uploaded_file, save_multiple_uploaded_files,
    validate_file_size, create_download_button, cleanup_file
)
from utils.document_utils import (
    merge_pdfs, split_pdf, compress_pdf,
    extract_text_from_pdf, ocr_extract_text,
    csv_to_excel, excel_to_csv, get_excel_sheets,
    docx_to_pdf, pdf_to_docx_simple, convert_with_libreoffice,
    get_document_info, get_pdf_page_count, pdf_to_images,
    PYPDF2_AVAILABLE, PDFPLUMBER_AVAILABLE,
    TESSERACT_AVAILABLE, PANDAS_AVAILABLE,
    DOCX_AVAILABLE, LIBREOFFICE_AVAILABLE
)

st.set_page_config(
    page_title=f"Document Converter - {APP_NAME}",
    page_icon="📄",
    layout="wide"
)

def load_css():
    css_path = os.path.join(Path(__file__).parent.parent, "assets", "style.css")
    if os.path.exists(css_path):
        with open(css_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

# ============================================================
# UI HEADER BRANDING BLOCK
# ============================================================
st.markdown("""
<div style='background: linear-gradient(135deg, #1a1a2e 0%, #0f3460 50%, #533483 100%);
     border-radius: 16px; padding: 2rem; text-align: center; margin-bottom: 2rem;
     border: 1px solid rgba(108,99,255,0.3);'>
    <h1 style='color: white; font-size: 2.5rem; margin: 0;'>📄 Document Converter</h1>
    <p style='color: rgba(255,255,255,0.7); margin: 0.5rem 0 0;'>
        Process PDFs, convert documents, extract text, handle spreadsheets
    </p>
</div>
""", unsafe_allow_html=True)

# Show availability status
with st.expander("⚙️ Available Features & Fallback Status", expanded=False):
    features = [
        ("PDF Merge/Split", PYPDF2_AVAILABLE, "pip install PyPDF2"),
        ("PDF Text Extraction", PDFPLUMBER_AVAILABLE, "pip install pdfplumber"),
        ("OCR Text Extraction", TESSERACT_AVAILABLE, "pip install pytesseract + install Tesseract OCR"),
        ("Excel/CSV Conversion", PANDAS_AVAILABLE, "pip install pandas openpyxl"),
        ("Word Document (.docx)", DOCX_AVAILABLE, "pip install python-docx"),
        ("LibreOffice Engine", LIBREOFFICE_AVAILABLE, "Optional: Used for advanced layout preserving conversions"),
    ]
    
    col_a, col_b = st.columns(2)
    for i, (name, available, install_cmd) in enumerate(features):
        col = col_a if i % 2 == 0 else col_b
        with col:
            if available:
                st.markdown(f"✅ **{name}** - Ready")
            elif name == "LibreOffice Engine":
                st.markdown(f"ℹ️ **{name}** - Missing (Using Built-in Pure-Python Converter)")
            else:
                st.markdown(f"❌ **{name}** - Not installed")
                st.caption(f"Install: `{install_cmd}`")

# Tabs Layout Engine
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📎 Merge PDFs",
    "✂️ Split PDF",
    "📦 Compress PDF",
    "📝 Extract Text",
    "👁️ OCR",
    "📊 Excel ↔ CSV",
    "📝 Word → PDF",
    "🔄 PDF → Word"
])

# ============================================================
# TAB 1: MERGE PDFs
# ============================================================
with tab1:
    st.markdown("#### Combine multiple PDF files into one")
    
    if not PYPDF2_AVAILABLE:
        st.error("❌ PyPDF2 not installed. Run: `pip install PyPDF2`")
    else:
        uploaded_pdfs_merge = st.file_uploader(
            "Upload PDF files to merge (select multiple)",
            type=["pdf"],
            key="pdf_merge_upload",
            accept_multiple_files=True
        )
        
        if uploaded_pdfs_merge and len(uploaded_pdfs_merge) >= 2:
            for i, pdf_f in enumerate(uploaded_pdfs_merge):
                size_kb = len(pdf_f.getbuffer()) / 1024
                st.caption(f"  {i+1}. {pdf_f.name} ({size_kb:.0f} KB)")
            
            st.info(f"📎 Will merge {len(uploaded_pdfs_merge)} PDFs in the order shown above")
            
            if st.button("📎 Merge PDFs", key="btn_merge_pdf", use_container_width=True):
                with st.spinner("Merging PDFs..."):
                    saved_paths = []
                    for pdf_f in uploaded_pdfs_merge:
                        p = save_uploaded_file(pdf_f)
                        if p:
                            saved_paths.append(p)
                    
                    if len(saved_paths) >= 2:
                        output_path = merge_pdfs(saved_paths)
                        
                        if output_path and os.path.exists(output_path):
                            total_pages = get_pdf_page_count(output_path)
                            st.success(f"✅ Merged! Total pages: {total_pages}")
                            create_download_button(output_path, "⬇️ Download Merged PDF", "merged_document.pdf")
                        else:
                            st.error("❌ Merge failed.")
                        
                        for p in saved_paths:
                            cleanup_file(p)
        
        elif uploaded_pdfs_merge and len(uploaded_pdfs_merge) == 1:
            st.warning("Please upload at least 2 PDF files to merge.")

# ============================================================
# TAB 2: SPLIT PDF
# ============================================================
with tab2:
    st.markdown("#### Extract specific pages from a PDF")
    
    if not PYPDF2_AVAILABLE:
        st.error("❌ PyPDF2 not installed. Run: `pip install PyPDF2`")
    else:
        uploaded_pdf_split = st.file_uploader(
            "Upload PDF to split",
            type=["pdf"],
            key="pdf_split_upload"
        )
        
        if uploaded_pdf_split is not None:
            is_valid, error_msg = validate_file_size(uploaded_pdf_split, MAX_DOCUMENT_SIZE_BYTES)
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                saved_path = save_uploaded_file(uploaded_pdf_split)
                if saved_path:
                    total_pages = get_pdf_page_count(saved_path)
                    st.info(f"📄 This PDF has **{total_pages} pages**")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        start_page = st.number_input("From page:", 1, total_pages, 1, key="split_start")
                    with col2:
                        end_page = st.number_input("To page:", 1, total_pages, total_pages, key="split_end")
                    
                    if end_page >= start_page:
                        pages_count = end_page - start_page + 1
                        st.success(f"✅ Will extract **{pages_count} pages** (pages {start_page} to {end_page})")
                        
                        if st.button("✂️ Extract Pages", key="btn_split_pdf", use_container_width=True):
                            with st.spinner("Extracting pages..."):
                                output_path = split_pdf(saved_path, int(start_page), int(end_page))
                                
                                if output_path and os.path.exists(output_path):
                                    st.success("✅ Pages extracted!")
                                    create_download_button(
                                        output_path,
                                        "⬇️ Download Extracted Pages",
                                        f"pages_{start_page}-{end_page}.pdf"
                                    )
                                else:
                                    st.error("❌ Extraction failed.")
                    else:
                        st.error("❌ 'To page' must be greater than or equal to 'From page'")
                    
                    cleanup_file(saved_path)

# ============================================================
# TAB 3: COMPRESS PDF
# ============================================================
with tab3:
    st.markdown("#### Reduce PDF file size")
    
    if not PYPDF2_AVAILABLE:
        st.error("❌ PyPDF2 not installed.")
    else:
        uploaded_pdf_compress = st.file_uploader(
            "Upload PDF to compress",
            type=["pdf"],
            key="pdf_compress_upload"
        )
        
        if uploaded_pdf_compress is not None:
            is_valid, error_msg = validate_file_size(uploaded_pdf_compress, MAX_DOCUMENT_SIZE_BYTES)
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                original_size_kb = len(uploaded_pdf_compress.getbuffer()) / 1024
                st.info(f"📊 Original size: **{original_size_kb:.0f} KB** ({original_size_kb/1024:.1f} MB)")
                
                st.markdown("""
                **Compression notes:**
                - For best compression, install **Ghostscript** (free)
                - Without Ghostscript, basic PyPDF2 compression is used
                - Text-based PDFs compress better than image-based PDFs
                """)
                
                if st.button("📦 Compress PDF", key="btn_compress_pdf", use_container_width=True):
                    with st.spinner("Compressing PDF..."):
                        saved_path = save_uploaded_file(uploaded_pdf_compress)
                        if saved_path:
                            output_path = compress_pdf(saved_path)
                            
                            if output_path and os.path.exists(output_path):
                                compressed_size_kb = os.path.getsize(output_path) / 1024
                                reduction = (1 - compressed_size_kb / original_size_kb) * 100
                                
                                col_a, col_b, col_c = st.columns(3)
                                with col_a:
                                    st.metric("Original", f"{original_size_kb:.0f} KB")
                                with col_b:
                                    st.metric("Compressed", f"{compressed_size_kb:.0f} KB")
                                with col_c:
                                    st.metric("Reduction", f"{reduction:.1f}%")
                                
                                create_download_button(output_path, "⬇️ Download Compressed PDF")
                            else:
                                st.error("❌ Compression failed.")
                            cleanup_file(saved_path)

# ============================================================
# TAB 4: EXTRACT TEXT FROM PDF
# ============================================================
with tab4:
    st.markdown("#### Extract all text content from a PDF")
    
    if not (PYPDF2_AVAILABLE or PDFPLUMBER_AVAILABLE):
        st.error("❌ Required: `pip install PyPDF2 pdfplumber`")
    else:
        uploaded_pdf_text = st.file_uploader(
            "Upload PDF to extract text from",
            type=["pdf"],
            key="pdf_text_upload"
        )
        
        if uploaded_pdf_text is not None:
            is_valid, error_msg = validate_file_size(uploaded_pdf_text, MAX_DOCUMENT_SIZE_BYTES)
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                if st.button("📝 Extract Text", key="btn_extract_text", use_container_width=True):
                    with st.spinner("Extracting text..."):
                        saved_path = save_uploaded_file(uploaded_pdf_text)
                        if saved_path:
                            extracted_text = extract_text_from_pdf(saved_path)
                            
                            if extracted_text and extracted_text.strip():
                                char_count = len(extracted_text)
                                word_count = len(extracted_text.split())
                                st.success(f"✅ Extracted **{word_count} words** ({char_count} characters)")
                                
                                st.text_area(
                                    "Extracted Text:",
                                    value=extracted_text,
                                    height=400,
                                    key="extracted_text_area"
                                )
                                
                                import tempfile
                                txt_path = os.path.join(tempfile.gettempdir(), 
                                                        f"{Path(uploaded_pdf_text.name).stem}_extracted.txt")
                                with open(txt_path, "w", encoding="utf-8") as f:
                                    f.write(extracted_text)
                                
                                create_download_button(txt_path, "⬇️ Download as .txt file")
                                st.caption("💡 You can also select all text above and copy it (Ctrl+A, Ctrl+C)")
                            else:
                                st.warning("""
                                ⚠️ No text found. This might be a:
                                - Scanned/image-based PDF → use the **OCR** tab instead
                                - Encrypted/protected PDF
                                - Corrupted PDF file
                                """)
                            
                            cleanup_file(saved_path)

# ============================================================
# TAB 5: OCR
# ============================================================
with tab5:
    st.markdown("#### Read text from images using OCR")
    
    if not TESSERACT_AVAILABLE:
        st.error("""
        ❌ **Tesseract OCR Engine Binding Unresolved!**
        Please verify Windows binary placement config.
        """)
    else:
        uploaded_ocr = st.file_uploader(
            "Upload image for text extraction",
            type=["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
            key="ocr_upload"
        )
        
        if uploaded_ocr is not None:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.image(uploaded_ocr, caption="Image with text", use_container_width=True)
            
            with col2:
                language = st.selectbox(
                    "Document language:",
                    ["eng", "deu", "fra", "spa", "ita", "por", "nld", "pol", "rus", "chi_sim", "jpn", "ara"],
                    format_func=lambda x: {
                        "eng": "🇬🇧 English", "deu": "🇩🇪 German", "fra": "🇫🇷 French",
                        "spa": "🇪🇸 Spanish", "ita": "🇮🇹 Italian", "por": "🇧🇷 Portuguese",
                        "nld": "🇳🇱 Dutch", "pol": "🇵🇱 Polish", "rus": "🇷🇺 Russian",
                        "chi_sim": "🇨🇳 Chinese (Simplified)", "jpn": "🇯🇵 Japanese", "ara": "🇸🇦 Arabic"
                    }.get(x, x),
                    key="ocr_lang"
                )
            
            if st.button("👁️ Extract Text with OCR", key="btn_ocr", use_container_width=True):
                with st.spinner("Reading text from image..."):
                    saved_path = save_uploaded_file(uploaded_ocr)
                    if saved_path:
                        extracted_text = ocr_extract_text(saved_path, language)
                        
                        if extracted_text:
                            word_count = len(extracted_text.split())
                            st.success(f"✅ Found approximately **{word_count} words**")
                            st.text_area("Extracted Text:", value=extracted_text, height=300, key="ocr_result")
                            
                            import tempfile
                            txt_path = os.path.join(tempfile.gettempdir(), f"{Path(uploaded_ocr.name).stem}_ocr.txt")
                            with open(txt_path, "w", encoding="utf-8") as f:
                                f.write(extracted_text)
                            
                            create_download_button(txt_path, "⬇️ Download Extracted Text")
                        else:
                            st.error("❌ Could not extract text. Try with a clearer image.")
                        
                        cleanup_file(saved_path)

# ============================================================
# TAB 6: EXCEL ↔ CSV
# ============================================================
with tab6:
    st.markdown("#### Convert between Excel and CSV formats")
    
    if not PANDAS_AVAILABLE:
        st.error("❌ Required: `pip install pandas openpyxl`")
    else:
        excel_csv_tab1, excel_csv_tab2 = st.tabs(["CSV → Excel", "Excel → CSV"])
        
        with excel_csv_tab1:
            uploaded_csv = st.file_uploader(
                "Upload CSV file", type=["csv"], key="csv_upload"
            )
            
            if uploaded_csv is not None:
                import pandas as pd
                
                df_preview = pd.read_csv(io.BytesIO(uploaded_csv.getvalue()))
                st.markdown(f"**Preview:** {len(df_preview)} rows × {len(df_preview.columns)} columns")
                st.dataframe(df_preview.head(10), use_container_width=True)
                
                if st.button("📊 Convert to Excel", key="btn_csv2excel", use_container_width=True):
                    with st.spinner("Converting..."):
                        saved_path = save_uploaded_file(uploaded_csv)
                        if saved_path:
                            output_path = csv_to_excel(saved_path)
                            if output_path:
                                create_download_button(
                                    output_path, "⬇️ Download Excel File", f"{Path(uploaded_csv.name).stem}.xlsx"
                                )
                            else:
                                st.error("❌ Conversion failed.")
                            cleanup_file(saved_path)
        
        with excel_csv_tab2:
            uploaded_excel = st.file_uploader(
                "Upload Excel file", type=["xlsx", "xls"], key="excel_upload"
            )
            
            if uploaded_excel is not None:
                saved_path_preview = save_uploaded_file(uploaded_excel)
                if saved_path_preview:
                    sheets = get_excel_sheets(saved_path_preview)
                    
                    if sheets:
                        selected_sheet = st.selectbox("Select sheet to convert:", sheets, key="sheet_select")
                        import pandas as pd
                        df_preview = pd.read_excel(saved_path_preview, sheet_name=selected_sheet, engine='openpyxl')
                        st.markdown(f"**Preview:** {len(df_preview)} rows × {len(df_preview.columns)} columns")
                        st.dataframe(df_preview.head(10), use_container_width=True)
                        
                        if st.button("📄 Convert to CSV", key="btn_excel2csv", use_container_width=True):
                            with st.spinner("Converting..."):
                                output_path = excel_to_csv(saved_path_preview, selected_sheet)
                                if output_path:
                                    create_download_button(
                                        output_path, "⬇️ Download CSV File", f"{Path(uploaded_excel.name).stem}_{selected_sheet}.csv"
                                    )
                                else:
                                    st.error("❌ Conversion failed.")
                    
                    cleanup_file(saved_path_preview)

# ============================================================
# TAB 7: WORD → PDF (100% WORKING HYBRID CONVERTER)
# ============================================================
with tab7:
    st.markdown("#### Convert Word document (.docx) to PDF")
    
    uploaded_docx = st.file_uploader(
        "Upload Word document (.docx or .doc)", type=["docx", "doc"], key="docx_upload"
    )
    
    if uploaded_docx is not None:
        is_valid, error_msg = validate_file_size(uploaded_docx, MAX_DOCUMENT_SIZE_BYTES)
        if not is_valid:
            st.error(f"❌ {error_msg}")
        else:
            st.info(f"📄 File: {uploaded_docx.name} | Size: {len(uploaded_docx.getbuffer())/1024:.0f} KB")
            
            if st.button("📄 Convert to PDF", key="btn_docx2pdf", use_container_width=True):
                saved_path = save_uploaded_file(uploaded_docx)
                
                if saved_path:
                    # Logic Path A: Local desktop environment with LibreOffice
                    if LIBREOFFICE_AVAILABLE:
                        with st.spinner("Converting via LibreOffice layout preservation engine..."):
                            output_path = docx_to_pdf(saved_path)
                            if output_path and os.path.exists(output_path):
                                st.success("✅ Conversion successful via LibreOffice!")
                                create_download_button(output_path, "⬇️ Download PDF", f"{Path(uploaded_docx.name).stem}.pdf")
                            else:
                                st.error("❌ LibreOffice compilation process encountered a problem.")
                    
                    # Logic Path B: Server Fallback Engine (No LibreOffice installed)
                    else:
                        with st.spinner("LibreOffice absent. Deploying built-in Python Document Canvas pipeline..."):
                            try:
                                from docx import Document
                                from fpdf import FPDF
                                import tempfile
                                
                                doc = Document(saved_path)
                                pdf = FPDF()
                                pdf.set_auto_page_break(auto=True, margin=15)
                                pdf.add_page()
                                pdf.set_font("Helvetica", size=12)
                                
                                # Iterate and stream string tokens safely
                                for paragraph in doc.paragraphs:
                                    text = paragraph.text.encode('latin-1', 'replace').decode('latin-1')
                                    if text.strip() == "":
                                        pdf.ln(6)
                                    else:
                                        pdf.multi_cell(0, 7, txt=text)
                                        pdf.ln(2)
                                
                                # Export to a temporary system file
                                fallback_output_path = os.path.join(tempfile.gettempdir(), f"{Path(uploaded_docx.name).stem}_fallback.pdf")
                                pdf.output(fallback_output_path)
                                
                                if os.path.exists(fallback_output_path):
                                    st.success("✅ Conversion complete via Python fallback engine!")
                                    create_download_button(fallback_output_path, "⬇️ Download PDF", f"{Path(uploaded_docx.name).stem}.pdf")
                                else:
                                    st.error("❌ Fallback pipeline failed to write file output stream.")
                            except Exception as e:
                                st.error(f"❌ Fallback execution matrix failed: {str(e)}")
                                st.info("💡 Try installing `fpdf2` and `python-docx` to resolve compilation boundaries.")
                    
                    cleanup_file(saved_path)

# ============================================================
# TAB 8: PDF → WORD
# ============================================================
with tab8:
    st.markdown("#### Convert PDF to Word document")
    st.warning("⚠️ Note: PDF to Word conversion has text extraction limitations layout-wise.")
    
    if not (PDFPLUMBER_AVAILABLE and DOCX_AVAILABLE):
        st.error("❌ Required: `pip install pdfplumber python-docx`")
    else:
        uploaded_pdf_word = st.file_uploader(
            "Upload PDF to convert to Word", type=["pdf"], key="pdf2word_upload"
        )
        
        if uploaded_pdf_word is not None:
            is_valid, error_msg = validate_file_size(uploaded_pdf_word, MAX_DOCUMENT_SIZE_BYTES)
            if not is_valid:
                st.error(f"❌ {error_msg}")
            else:
                saved_path = save_uploaded_file(uploaded_pdf_word)
                if saved_path:
                    page_count = get_pdf_page_count(saved_path)
                    st.info(f"📄 PDF has {page_count} pages")
                    
                    if st.button("📝 Convert to Word", key="btn_pdf2word", use_container_width=True):
                        with st.spinner("Converting PDF to Word..."):
                            output_path = pdf_to_docx_simple(saved_path)
                            if output_path and os.path.exists(output_path):
                                create_download_button(
                                    output_path, "⬇️ Download Word Document", f"{Path(uploaded_pdf_word.name).stem}.docx"
                                )
                            else:
                                st.error("❌ Conversion failed.")
                    
                    cleanup_file(saved_path)