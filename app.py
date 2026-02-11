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
    st.error("API Key not found! Add 'ANTHROPIC_API_KEY' to your Streamlit Secrets.")
    st.stop()

# 3. Input UI
video_url = st.text_input("Paste YouTube Video URL", placeholder="https://www.youtube.com/watch?v=...")

if st.button("Generate Pitch"):
    try:
        # A. Video ID Extraction
        video_id = None
        if "v=" in video_url:
            video_id = video_url.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_url:
            video_id = video_url.split("/")[-1].split("?")[0]
        
        if not video_id:
            st.error("Invalid Video ID. Please check your link.")
            st.stop()

        # B. THE SESSION FIX: Load Cookies Manually
        session = requests.Session()
        # Set custom headers to look more like a real browser
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        
        # Load your youtube_cookies.txt (Netscape/Mozilla format)
        try:
            cj = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
            cj.load(ignore_discard=True, ignore_expires=True)
            session.cookies = cj
        except FileNotFoundError:
            st.error("Error: 'youtube_cookies.txt' not found in your GitHub repo.")
            st.stop()
        
        # C. Fetch Transcript using the HTTP Client
        ytt_api = YouTubeTranscriptApi(http_client=session)
        fetched_obj = ytt_api.fetch(video_id)
        
        # Convert to raw data to ensure it is subscriptable
        transcript_data = fetched_obj.to_raw_data()
        context = " ".join([item['text'] for item in transcript_data])[:6000]

        # D. Run Claude Agent with NEW 2026 Model ID
        client = Anthropic(api_key=api_key)
        # Note: 'claude-3-5-sonnet-20240620' is retired. Use 'claude-sonnet-4-5'
        response = client.messages.create(
            model="claude-sonnet-4-5", 
            max_tokens=1500,
            system="You are a Talent Manager. Create a professional sponsorship pitch.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        st.success("Pitch Generated!")
        st.markdown("---")
        st.markdown(response.content[0].text)
        
    except Exception as e:
        if "404" in str(e):
            st.error("Model Error: Your model ID is retired. Ensure you use 'claude-sonnet-4-5'.")
        elif "youtube_cookies" in str(e).lower():
            st.error("Cookie Error: YouTube is blocking your cloud IP. Your cookies may be expired.")
        else:
            st.error(f"Error: {e}")
