import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic
import http.cookiejar

# 1. Setup Page Title
st.title("🤖 Sponsor Scout: Creator Outreach Agent")

# 2. Secure API Key Retrieval
api_key = st.secrets.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("API Key not found in Secrets!")
    st.stop()

# 3. Input URL
video_url = st.text_input("Paste YouTube Video URL")

if st.button("Generate Pitch"):
    try:
        # A. Robust Video ID Extraction
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        
        # --- THE FIX: Create a Session and Load Cookies Manually ---
        session = requests.Session()
        cj = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
        cj.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cj
        
        # Pass the session with cookies to the API
        ytt_api = YouTubeTranscriptApi(http_client=session)
        transcript_data = ytt_api.fetch(video_id)
        context = " ".join([item.text for item in transcript_data])[:4000] 
        # ---------------------------------------------------------------------------

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
        st.error(f"Error: {e}")

