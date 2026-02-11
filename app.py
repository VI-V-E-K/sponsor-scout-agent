import streamlit as st
import requests
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic
import http.cookiejar

# 1. Setup Page Title
st.title("🤖 Sponsor Scout: Creator Outreach Agent")

# 2. Secure API Key Retrieval (Pulls from Streamlit Advanced Settings)
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

        # B. Fetch Transcript with Session & Cookies
        session = requests.Session()
        # Ensure 'youtube_cookies.txt' is uploaded to your GitHub repo
        cj = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
        cj.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cj
        
        ytt_api = YouTubeTranscriptApi(http_client=session)
        fetched_obj = ytt_api.fetch(video_id)
        
        # --- THE UNIVERSAL FIX for subscriptable error ---
        # Converts the 2026 'FetchedTranscript' object back to a standard list of dictionaries
        transcript_data = fetched_obj.to_raw_data()
        context = " ".join([item['text'] for item in transcript_data])[:6000]
        # --------------------------------------------------------------

        # C. Run Claude Agent with UPDATED Model ID
        client = Anthropic(api_key=api_key)
        # Model 'claude-3-5-sonnet-20240620' is retired; use 'claude-sonnet-4-5'
        response = client.messages.create(
            model="claude-sonnet-4-5", 
            max_tokens=1500,
            system="You are a Talent Manager. Create a sponsorship pitch for this video.",
            messages=[{"role": "user", "content": f"Video Transcript: {context}"}]
        )

        st.success("Pitch Generated!")
        st.markdown("---")
        st.markdown(response.content[0].text)
        
    except Exception as e:
        # Specific help for common 2026 errors
        if "404" in str(e):
            st.error("Model Error: Ensure you are using 'claude-sonnet-4-5' as the model name.")
        elif "youtube_cookies.txt" in str(e):
            st.error("Cookie Error: Please ensure 'youtube_cookies.txt' is uploaded to GitHub.")
        else:
            st.error(f"Error: {e}")
