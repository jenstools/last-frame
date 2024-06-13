import streamlit as st
import cv2
import requests
import numpy as np
from PIL import Image
from urllib.parse import urlparse, parse_qs

# Function to download video from URL
def download_video(url, file_name):
    response = requests.get(url, stream=True)
    with open(file_name, 'wb') as video_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                video_file.write(chunk)

# Function to extract the last frame of the video
def extract_last_frame(video_path):
    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames - 1)
    ret, frame = cap.read()
    cap.release()
    if ret:
        return frame
    else:
        return None

# Function to get URL parameters
def get_url_params():
    query_params = st.experimental_get_query_params()
    if 'url' in query_params:
        return query_params['url'][0]
    return ""

# Streamlit app interface
st.title("Video Last Frame Extractor")

# Get the URL parameter
default_url = get_url_params()

# Input field for video URL with default value from URL parameter
video_url = st.text_input("Enter the video URL (mp4):", value=default_url)

if st.button("Download and Extract Last Frame"):
    if video_url:
        video_file_name = "downloaded_video.mp4"
        last_frame_image_name = "last_frame.jpg"

        st.write("Downloading video...")
        download_video(video_url, video_file_name)
        st.write("Video downloaded successfully.")

        st.write("Extracting last frame...")
        frame = extract_last_frame(video_file_name)

        if frame is not None:
            st.write("Last frame extracted successfully.")
            # Convert frame to an image
            frame_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            frame_image.save(last_frame_image_name)

            # Display the image
            st.image(frame_image, caption="Last Frame", use_column_width=True)

            # Provide download link for the last frame
            with open(last_frame_image_name, "rb") as file:
                btn = st.download_button(
                    label="Download Last Frame as JPG",
                    data=file,
                    file_name=last_frame_image_name,
                    mime="image/jpeg"
                )
        else:
            st.write("Failed to extract the last frame.")
    else:
        st.write("Please enter a valid video URL.")
