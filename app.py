import logging
import os

# This forces errors to the log console
logging.basicConfig(level=logging.DEBUG)
os.write(1, b"APP STARTING...\n") 

import streamlit as st
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
        
        # CHANGED: Added cookie support to bypass YouTube blocking
        # Ensure 'youtube_cookies.txt' is uploaded to your GitHub repo
        context_list = YouTubeTranscriptApi.get_transcript(video_id, cookies='youtube_cookies.txt')
        context = " ".join([item['text'] for item in context_list])[:4000] # Limit context

        # B. Run Claude 3.5 Agent
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1024,
            system="You are a Talent Manager. Match the video content to a tech sponsor like Cursor or Vercel.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        # C. Display Result
        st.success("Pitch Generated!")
        st.markdown(response.content[0].text)
        
    except Exception as e:
        # Added specific billing error check to help you know when to add credits
        if "credit balance" in str(e).lower():
            st.error("Error: Your Anthropic account balance is $0. Please add $5 to your console.")
        else:
            st.error(f"Error: {e}")
