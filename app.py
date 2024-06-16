import streamlit as st
import cv2
import requests
import numpy as np
from PIL import Image
from urllib.parse import urlparse, parse_qs
import stability_sdk.interfaces.gooseai.generation.generation_pb2 as generation
from stability_sdk import client
import io
import os

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

# Function to generate the output filename
def generate_output_filename(video_url):
    parsed_url = urlparse(video_url)
    video_filename = os.path.basename(parsed_url.path)
    base_name = os.path.splitext(video_filename)[0]
    return f"{base_name}_last-frame.jpg"

# Function to convert image to PNG bytes
def image_to_png_bytes(image):
    buf = io.BytesIO()
    image.save(buf, format='PNG')
    buf.seek(0)
    return buf.getvalue()

# Function to upscale an image using Stability AI
def upscale_image(image, api_key):
    stability_api = client.StabilityInference(
        key=api_key,
        verbose=True,
    )
    
    img_byte_arr = image_to_png_bytes(image)
    
    answers = stability_api.upscale(
        init_image=img_byte_arr,
        width=image.width * 2,  # upscale by 2x
        height=image.height * 2,  # upscale by 2x
        steps=50,  # optional
    )

    for resp in answers:
        for artifact in resp.artifacts:
            if artifact.finish_reason == generation.FILTER:
                raise Exception("Your request activated the API's safety filters and could not be processed.")
            if artifact.type == generation.ARTIFACT_IMAGE:
                upscaled_image = Image.open(io.BytesIO(artifact.binary))
                return upscaled_image
    return None

# Streamlit app interface
st.title("Video Last Frame Extractor")

# Get the URL parameter
default_url = get_url_params()

# Input field for video URL with default value from URL parameter
video_url = st.text_input("Enter the video URL (mp4):", value=default_url)

# Input field for API key for upscaling
api_key = st.text_input("Enter your Stability AI API key (optional for upscaling):")

def process_video(url, api_key=None):
    video_file_name = "downloaded_video.mp4"
    output_file_name = generate_output_filename(url)

    st.write("Downloading video...")
    download_video(url, video_file_name)
    st.write("Video downloaded successfully.")

    st.write("Extracting last frame...")
    frame = extract_last_frame(video_file_name)

    if frame is not None:
        st.write("Last frame extracted successfully.")
        # Convert frame to an image
        frame_image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        
        if api_key:
            st.write("Upscaling image...")
            frame_image = upscale_image(frame_image, api_key)
            st.write("Image upscaled successfully.")

        frame_image.save(output_file_name)

        # Display the image
        st.image(frame_image, caption="Last Frame", use_column_width=True)

        # Provide download link for the last frame
        with open(output_file_name, "rb") as file:
            btn = st.download_button(
                label="Download Last Frame as JPG",
                data=file,
                file_name=output_file_name,
                mime="image/jpeg"
            )
    else:
        st.write("Failed to extract the last frame.")

# Check if URL parameter is present and process the video automatically
if default_url:
    process_video(default_url, api_key)

if st.button("Download and Extract Last Frame"):
    if video_url:
        process_video(video_url, api_key)
    else:
        st.write("Please enter a valid video URL.")
