# Core Pkg
import streamlit as st
import streamlit.components.v1 as stc

# EDA Pkgs
import pandas as pd

# Data Vis Pkgs
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib

matplotlib.use("Agg")

# Opening Files/Forensic MetaData Extraction
# For Images
from PIL import Image
import exifread
import os
from datetime import datetime
import base64

# For Audio
import mutagen

# For PDF
import fitz  # PyMuPDF
import threading
# HTML
metadata_wiki = """
Metadata is defined as the data providing information about one or more aspects of the data; it is used to summarize basic information about data which can make tracking and working with specific data easier
"""

HTML_BANNER = """
    <div style="background-color:#464e5f;padding:10px;border-radius:10px">
    <h1 style="color:white;text-align:center;">MetaData Extractor App </h1>
    </div>
    """

# Functions
def load_image(image_file):
    img = Image.open(image_file)
    return img


import time

timestr = time.strftime("%Y%m%d-%H%M%S")

# Fxn to Download
def make_downloadable(data):
    csvfile = data.to_csv(index=False)
    b64 = base64.b64encode(csvfile.encode()).decode()  # B64 encoding
    st.markdown("### ** Download CSV File ** ")
    new_filename = "metadata_result_{}.csv".format(timestr)
    href = f'<a href="data:file/csv;base64,{b64}" download="{new_filename}">Click Here!</a>'
    st.markdown(href, unsafe_allow_html=True)

def save_uploaded_file(uploaded_file):
    """
    Save an uploaded file and return the saved file's path.
    """
    with open(uploaded_file.name, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return uploaded_file.name

# DB Management
from db_fxns import *

# Utils
from app_utils import *


# App Structure
def main():
    """Meta Data Extraction App"""
    stc.html(HTML_BANNER)

    menu = ["Home", "Image", "Audio", "DocumentFiles", "Analytics", "About"]
    choice = st.sidebar.selectbox("Menu", menu)
    
    # Utilizza threading per creare la tabella
    if choice == "Home":
        thread = threading.Thread(target=create_uploaded_filetable)
        thread.start()
        st.subheader("Home")
        # Image
        st.image(load_image("images/metadataextraction_app_jcharistech.png"))
        # Description

        st.write(metadata_wiki)

        # Expanders & Columns
        col1, col2, col3 = st.columns(3)
        with col1:
            with st.expander("Get Image Metadata 📷"):
                st.info("Image Metadata")
                st.markdown("📷")
                st.text("Upload JPEG, JPG, PNG Images")

        with col2:
            with st.expander("Get Audio Metadata 🔉"):
                st.info("Audio Metadata")
                st.markdown("🔉")
                st.text("Upload Mp3, Ogg")

        with col3:
            with st.expander("Get Document Metadata 📄📁"):
                st.info("Document Files Metadata")
                st.markdown("📄📁")
                st.text("Upload PDF, Docx")

    elif choice == "Image":
        st.subheader("Image MetaData Extraction")
        image_file = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
        if image_file is not None:
            with st.expander("File Stats"):
                file_details = {
                    "FileName": image_file.name,
                    "FileSize": image_file.size,
                    "FileType": image_file.type,
                }
                st.write(file_details)

                statinfo = os.stat(image_file.readable())
                st.write(statinfo)
                stats_details = {
                    "Accessed_Time": get_readable_time(statinfo.st_atime),
                    "Creation_Time": get_readable_time(statinfo.st_ctime),
                    "Modified_Time": get_readable_time(statinfo.st_mtime),
                }
                st.write(stats_details)

                # Combine All Details
                file_details_combined = {
                    "FileName": image_file.name,
                    "FileSize": image_file.size,
                    "FileType": image_file.type,
                    "Accessed_Time": get_readable_time(statinfo.st_atime),
                    "Creation_Time": get_readable_time(statinfo.st_ctime),
                    "Modified_Time": get_readable_time(statinfo.st_mtime),
                }

                # Convert to DataFrame
                df_file_details = pd.DataFrame(
                    list(file_details_combined.items()), columns=["Meta Tags", "Value"]
                )

                st.dataframe(df_file_details)

                # Track Details
                add_file_details(
                    image_file.name, image_file.type, image_file.size, datetime.now()
                )

            # Layouts
            c1, c2 = st.columns(2)
            with c1:
                with st.expander("View Image"):
                    img = load_image(image_file)
                    st.image(img, width=250, caption="Image caption")

            with c2:
                with st.expander("Default(JPEG)"):
                    st.info("Using PILLOW")
                    img = load_image(image_file)
                    img_details = {
                        "format": img.format,
                        "format_desc": img.format_description,
                        "filename": img.filename,
                        "size": img.size,
                        "height": img.height,
                        "width": img.width,
                        "info": img.info,
                    }
                    df_img_details_default = pd.DataFrame(
                        list(img_details.items()), columns=["Meta Tags", "Value"]
                    )
                    st.dataframe(df_img_details_default)

            # Layouts For Forensic
            fcol1, fcol2 = st.columns(2)

            with fcol1:
                with st.expander("Exifread Tool"):
                    meta_tags = exifread.process_file(image_file)
                    df_img_details_exifread = pd.DataFrame(
                        list(meta_tags.items()), columns=["Meta Tags", "Value"]
                    )
                    st.dataframe(df_img_details_exifread)

            with fcol2:
                with st.expander("Image Geo-Coordinates"):
                    img_details_with_exif = get_exif(image_file)
                    try:
                        gpg_info = img_details_with_exif
                    except:
                        gpg_info = "None Found"

                    img_coordinates = get_decimal_coordinates(gpg_info)
                    st.write(img_coordinates)

            with st.expander("Download Results"):
                final_df = pd.concat(
                    [df_file_details, df_img_details_default, df_img_details_exifread]
                )
                st.dataframe(final_df)
                make_downloadable(final_df)

    elif choice == "Audio":
        st.subheader("Audio MetaData Extraction")
        # File Upload
        audio_file = st.file_uploader("Upload Audio", type=["mp3", "ogg"])

        if audio_file is not None:

            # Layouts
            col1, col2 = st.columns(2)

            with col1:
                st.audio(audio_file.read())

            with col2:
                with st.expander("File Stats"):
                    file_details = {
                        "FileName": audio_file.name,
                        "FileSize": audio_file.size,
                        "FileType": audio_file.type,
                    }
                    st.write(file_details)

                    statinfo = os.stat(audio_file.readable())
                    # st.write(statinfo)
                    stats_details = {
                        "Accessed_Time": get_readable_time(statinfo.st_atime),
                        "Creation_Time": get_readable_time(statinfo.st_ctime),
                        "Modified_Time": get_readable_time(statinfo.st_mtime),
                    }
                    st.write(stats_details)

                    # Combine All Details
                    file_details_combined = {
                        "FileName": audio_file.name,
                        "FileSize": audio_file.size,
                        "FileType": audio_file.type,
                        "Accessed_Time": get_readable_time(statinfo.st_atime),
                        "Creation_Time": get_readable_time(statinfo.st_ctime),
                        "Modified_Time": get_readable_time(statinfo.st_mtime),
                    }

                    # Convert to DataFrame
                    df_file_details = pd.DataFrame(
                        list(file_details_combined.items()),
                        columns=["Meta Tags", "Value"],
                    )
                    st.dataframe(df_file_details)

                    # Track Details
                    add_file_details(
                        audio_file.name,
                        audio_file.type,
                        audio_file.size,
                        datetime.now(),
                    )
            # Extraction Process using mutagen

            with st.expander("Metadata with Mutagen"):
                meta_tags = mutagen.File(audio_file)
                df_audio_details_with_mutagen = pd.DataFrame(
                    list(meta_tags.items()), columns=["Meta Tags", "Value"]
                )

                # Aggiungi la conversione della colonna Value
                df_audio_details_with_mutagen["Value"] = df_audio_details_with_mutagen["Value"].apply(str)

                st.dataframe(df_audio_details_with_mutagen)

            with st.expander("Download Results"):
                final_df = pd.concat([df_file_details, df_audio_details_with_mutagen])
                st.dataframe(final_df)
                make_downloadable(final_df)

    
   # ...

    elif choice == "DocumentFiles":
        st.subheader("DocumentFiles MetaData Extraction")

        # FIle Upload
        text_file = st.file_uploader("Upload File", type=["PDF"])
        if text_file is not None:
            dcol1, dcol2 = st.columns([1, 2])

            with dcol1:
                with st.expander("File Stats"):
                    file_details = {
                        "FileName": text_file.name,
                        "FileSize": text_file.size,
                        "FileType": text_file.type,
                    }
                    st.write(file_details)

                    statinfo = os.stat(text_file.readable())

                    stats_details = {
                        "Accessed_Time": get_readable_time(statinfo.st_atime),
                        "Creation_Time": get_readable_time(statinfo.st_ctime),
                        "Modified_Time": get_readable_time(statinfo.st_mtime),
                    }
                    st.write(stats_details)

                    # Combine All Details
                    file_details_combined = {
                        "FileName": text_file.name,
                        "FileSize": text_file.size,
                        "FileType": text_file.type,
                        "Accessed_Time": get_readable_time(statinfo.st_atime),
                        "Creation_Time": get_readable_time(statinfo.st_ctime),
                        "Modified_Time": get_readable_time(statinfo.st_mtime),
                    }

                    # Convert to DataFrame
                    df_file_details = pd.DataFrame(
                        list(file_details_combined.items()),
                        columns=["Meta Tags", "Value"],
                    )

                    # st.dataframe(df_file_details)
                    # Track Details
                    add_file_details(
                        text_file.name, text_file.type, text_file.size, datetime.now()
                    )

            # Estrai il percorso del file e apri il file con PyMuPDF
            with dcol2:
                with st.expander("Metadata"):
                    pdf_file_path = save_uploaded_file(text_file)
                    pdf_file = fitz.open(pdf_file_path)
                    pdf_info = pdf_file.metadata
                    # st.write(pdf_info)
                    # Convert to DataFrame
                    df_file_details_with_pdf = pd.DataFrame(
                        list(pdf_info.items()), columns=["Meta Tags", "Value"]
                    )

                    st.dataframe(df_file_details_with_pdf)

            # Download
            with st.expander("Download Results"):
                final_df = pd.concat([df_file_details, df_file_details_with_pdf])
                st.dataframe(final_df)
                make_downloadable(final_df)


    elif choice == "Analytics":
        st.subheader("Analytics")
        all_uploaded_files = view_all_data()
        df = pd.DataFrame(
            all_uploaded_files,
            columns=["FileName", "FileType", "FileSize", "Upload_Time"],
        )

        # Monitor All Uploads
        with st.expander("Monitor"):
            st.success("View All Uploaded Files")
            st.dataframe(df)

        # Stats of Uploaded Files
        with st.expander("Distribution of FileTypes"):
            fig = plt.figure()
            sns.countplot(df["FileType"])
            st.pyplot(fig)

    else:
        st.subheader("About")
        # Image
        st.image(load_image("images/metadataextraction_app_jcharistech.png"))


if __name__ == "__main__":
    main()
