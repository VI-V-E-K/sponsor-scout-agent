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
try:
    api_key = st.secrets["ANTHROPIC_API_KEY"]
except KeyError:
    st.error("API Key not found in Secrets.")
    st.stop()

# 3. Input URL
video_url = st.text_input("Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate Pitch"):
    try:
        # Robust Video ID Extraction
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        elif "/shorts/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        
        if not video_id:
            st.error("Invalid Video ID.")
            st.stop()

        # --- THE FIX: Pass cookies to the constructor, not fetch() ---
        # 1. Initialize with the cookie file path
        ytt_api = YouTubeTranscriptApi(cookie_path='youtube_cookies.txt')
        
        # 2. Call fetch() without the cookies argument
        transcript_data = ytt_api.fetch(video_id)
        context = " ".join([item['text'] for item in transcript_data])[:4000]

        # B. Run Claude Agent
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="You are a Talent Manager. Match the video content to a tech sponsor.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        st.success("Pitch Generated!")
        st.markdown(response.content[0].text)
        
    except Exception as e:
        if "credit balance" in str(e).lower():
            st.error("Error: Your Anthropic account balance is $0.")
        else:
            st.error(f"Error: {e}")
