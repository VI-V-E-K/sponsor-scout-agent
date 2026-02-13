import os
import streamlit as st
import traceback
import requests
import http.cookiejar
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import RequestBlocked, TranscriptsDisabled, NoTranscriptFound
from anthropic import Anthropic
from streamlit.errors import StreamlitSecretNotFoundError

from saas_database import SAAS_DATABASE, format_for_claude_prompt

# =========================================================
# CONFIG
# =========================================================

st.set_page_config(
    page_title="Sponsor Scout Pro",
    page_icon="🤖",
    layout="wide"
)

# Increased for 2026 long-context models (approx 200k tokens)
MAX_TRANSCRIPT_CHARS = 800_000

# =========================================================
# STYLES
# =========================================================

st.markdown("""
<style>
.main-header {
    font-size: 2.5rem;
    font-weight: bold;
    background: linear-gradient(135deg, #667eea, #764ba2);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.subtitle {
    color: #6c757d;
    margin-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================

st.markdown('<div class="main-header">🤖 Sponsor Scout Pro</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI-powered creator sponsorship pitch generator</div>', unsafe_allow_html=True)

# =========================================================
# API KEY
# =========================================================

try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except (StreamlitSecretNotFoundError, KeyError):
    api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY not found in secrets or environment.")
    st.stop()

# =========================================================
# HELPERS
# =========================================================

def extract_video_id(url: str) -> str | None:
    # Regex for universal support (Shorts, mobile, desktop)
    video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id_match.group(1) if video_id_match else None


def get_full_transcript(video_id: str) -> str:
    """Fetches transcript using a browser-emulated session to bypass IP blocks."""
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    })
    
    # Load Netscape-format cookies to bypass cloud IP bans
    try:
        cj = http.cookiejar.MozillaCookieJar('youtube_cookies.txt')
        cj.load(ignore_discard=True, ignore_expires=True)
        session.cookies = cj
    except FileNotFoundError:
        pass

    # FIX: Call list_transcripts as a Class Method
    try:
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id, http_client=session)
        try:
            transcript = transcript_list.find_transcript(['en'])
        except:
            # Fallback to translation if English is not original
            first = next(iter(transcript_list))
            transcript = first.translate('en')
            
        data = transcript.fetch()
        return " ".join(t["text"] for t in data)
    except Exception as e:
        raise RuntimeError(f"Could not fetch transcript for {video_id}: {str(e)}")


def analyze_with_improved_claude(transcript: str, video_count: int) -> str:
    safe_transcript = transcript[:MAX_TRANSCRIPT_CHARS]
    saas_text = format_for_claude_prompt()

    system_prompt = f"""
You are an elite sponsorship strategist.
Analyze the full transcript provided within <transcript> tags.

ONLY use companies from this database:
{saas_text}

Output structure:
1. CREATOR SNAPSHOT
2. TOP 3 SPONSOR MATCHES (ranked)
3. MONEY ANGLE
4. READY-TO-SEND OUTREACH EMAIL
"""

    client = Anthropic(api_key=api_key)

    try:
        # Using 2026 stable model ID for long-context support
        message = client.messages.create(
            model="claude-sonnet-4-5",
            max_tokens=4000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"Analyze these {video_count} videos.\n\n<transcript>{safe_transcript}</transcript>"
            }]
        )
        return message.content[0].text
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")

# =========================================================
# MAIN UI
# =========================================================

video_urls = st.text_area("Paste YouTube video URLs (one per line)", height=120)
show_debug = st.checkbox("Show debug info")

if st.button("🚀 Generate Sponsorship Pitch", use_container_width=True):
    urls = [u.strip() for u in video_urls.splitlines() if u.strip()]
    if not urls:
        st.error("Please enter at least one YouTube URL.")
        st.stop()

    valid_videos = [vid for url in urls if (vid := extract_video_id(url))]
    
    if not valid_videos:
        st.error("No valid YouTube IDs found.")
        st.stop()

    progress = st.progress(0)
    status = st.empty()
    transcripts = []

    try:
        for i, vid in enumerate(valid_videos):
            status.text(f"Fetching transcript {i+1}/{len(valid_videos)}")
            progress.progress((i + 1) / (len(valid_videos) + 1))
            transcripts.append(get_full_transcript(vid))

        combined_transcript = "\n\n".join(transcripts)

        status.text("🧠 Analyzing with Claude (Long Context Mode)...")
        progress.progress(0.9)

        pitch = analyze_with_improved_claude(combined_transcript, len(transcripts))

        progress.progress(1.0)
        status.text("✅ Done")

        st.markdown("---")
        st.markdown("# 📊 Sponsorship Pitch")
        st.markdown(pitch)

        st.download_button(
            "📥 Download Pitch",
            pitch,
            file_name="pitch.md",
            mime="text/markdown"
        )

        if show_debug:
            st.code(combined_transcript[:1000])

    except Exception as e:
        st.error(str(e))
        if show_debug:
            st.code(traceback.format_exc())
