import logging
import os

# This forces errors to the log console
logging.basicConfig(level=logging.DEBUG)
os.write(1, b"APP STARTING...\n") 

import streamlit as st
# Rest of your code...import streamlit as st
import os
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic

# 1. Setup Page Title
st.title("🤖 Sponsor Scout: Creator Outreach Agent")
st.subheader("Turn YouTube videos into high-value brand pitches in seconds.")

# 2. Sidebar for API Key
with st.sidebar:
    api_key = st.text_input("Anthropic API Key", type="password")
    "[Get your key at console.anthropic.com](https://console.anthropic.com/)"

# 3. Input URL
video_url = st.text_input("Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate Pitch") and api_key:
    try:
        # A. Fetch Transcript
        video_id = video_url.split("v=")[1].split("&")[0]
        ytt_api = YouTubeTranscriptApi()
        transcript_obj = ytt_api.fetch(video_id)
        context = " ".join([item.text for item in transcript_obj])[:4000] # Limit context

        # B. Run Claude 4.6 Agent
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=1024,
            system="You are a Talent Manager. Match the video content to a tech sponsor like Cursor or Vercel.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        # C. Display Result
        st.success("Pitch Generated!")
        st.markdown(response.content[0].text)
        
    except Exception as e:
        st.error(f"Error: {e}")
