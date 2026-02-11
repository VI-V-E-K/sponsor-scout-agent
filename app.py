import logging
import os
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic

# Forces errors to the log console for debugging
logging.basicConfig(level=logging.DEBUG)
os.write(1, b"APP STARTING...\n") 

# 1. Setup Page Title
st.title("🤖 Sponsor Scout: Creator Outreach Agent")
st.subheader("Turn YouTube videos into high-value brand pitches in seconds.")

# 2. Secure API Key Retrieval
# This pulls directly from "Advanced Settings > Secrets"
# No sidebar or code-level key storage is required.
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("API Key not found! Please add ANTHROPIC_API_KEY to your Streamlit Advanced Settings.")
    st.stop()

# 3. Input URL
video_url = st.text_input("Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate Pitch"):
    try:
        # --- Robust Video ID Extraction ---
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        elif "/shorts/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]

        if not video_id:
            st.error("Could not find a valid Video ID. Please check the URL.")
            st.stop()

        # --- THE SOLUTION: Initialize and use .fetch() ---
        try:
            # 1. Initialize the API object
            ytt_api = YouTubeTranscriptApi()

            # 2. Use .fetch() instead of .get_transcript()
            # This also supports your cookies for bypassing blocks
            context_list = ytt_api.fetch(
                video_id,
                cookies='youtube_cookies.txt'
            )

            # 3. Join the text as before
            context = " ".join([item['text'] for item in context_list])[:4000]

        except AttributeError:
            # Fallback for older versions if fetch() isn't recognized
            context_list = YouTubeTranscriptApi.get_transcript(video_id, cookies='youtube_cookies.txt')
            context = " ".join([item['text'] for item in context_list])[:4000]

        # B. Run Claude 3.5 Agent
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="You are a Talent Manager. Match the video content to a tech sponsor.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        # C. Display Result
        st.success("Pitch Generated!")
        st.markdown(response.content[0].text)

    except Exception as e:
        if "list index out of range" in str(e).lower():
            st.error("Error: URL format not recognized. Please use a standard YouTube link.")
        elif "credit balance" in str(e).lower():
            st.error("Error: Your Anthropic account balance is $0. Please add $5 to your console.")
        else:
            st.error(f"Error: {e}")
