import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic
import http.cookiejar

st.title("🤖 Sponsor Scout: Creator Outreach Agent")

# 1. Secure API Key Retrieval from Advanced Settings
api_key = st.secrets.get("ANTHROPIC_API_KEY")
if not api_key:
    st.error("API Key not found in Secrets! Add it to Advanced Settings.")
    st.stop()

video_url = st.text_input("Paste YouTube Video URL")

if st.button("Generate Pitch"):
    try:
        # 2. Robust Video ID Extraction
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        
        if not video_id:
            st.error("Invalid Video ID.")
            st.stop()

        # 3. Fetch Transcript with Session & Cookies
        session = requests.Session()
        cj = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
        cj.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cj
        
        # Initialize and fetch using the modern 2026 API structure
        ytt_api = YouTubeTranscriptApi(http_client=session)
        transcript_data = ytt_api.fetch(video_id)
        
        # 4. Join Text using Attribute Access to fix 'subscriptable' error
        try:
            context = " ".join([item.text for item in transcript_data])[:4000]
        except (AttributeError, TypeError):
            context = " ".join([item['text'] for item in transcript_data])[:4000]

        # 5. Run Claude Agent
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
