import os
import streamlit as st
import traceback
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

MAX_TRANSCRIPT_CHARS = 45_000

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
except StreamlitSecretNotFoundError:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("ANTHROPIC_API_KEY not found in secrets or environment.")
    st.stop()

# =========================================================
# HELPERS
# =========================================================

def extract_video_id(url: str) -> str | None:
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    if "youtu.be/" in url:
        return url.split("/")[-1].split("?")[0]
    if "shorts/" in url:
        return url.split("shorts/")[1].split("?")[0]
    return None


def get_full_transcript(video_id: str) -> str:
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    return " ".join(t["text"] for t in transcript)


def analyze_with_improved_claude(transcript: str, video_count: int) -> str:
    safe_transcript = transcript[:MAX_TRANSCRIPT_CHARS]
    saas_text = format_for_claude_prompt()

    system_prompt = f"""
You are an elite sponsorship strategist who closes brand deals for creators.

You do NOT summarize.
You SELL alignment and revenue.

ONLY use companies from this database:
{saas_text}

Rules:
- Be confident and decisive
- No generic language
- Tie insights to transcript evidence
- Weak matches must be called out

Output structure (mandatory):
1. CREATOR SNAPSHOT
2. TOP 3 SPONSOR MATCHES (ranked)
3. MONEY ANGLE
4. READY-TO-SEND OUTREACH EMAIL
"""

    client = Anthropic(api_key=api_key)

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-latest",
            max_tokens=7000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"""
Analyze these YouTube transcript(s) and generate a sponsorship pitch.

Videos analyzed: {video_count}
Transcript length (truncated): {len(safe_transcript):,} chars

TRANSCRIPT:
{safe_transcript}
"""
            }]
        )
    except Exception as e:
        raise RuntimeError(f"Claude API error: {e}")

    if not message.content:
        raise RuntimeError("Claude returned empty content")

    text_blocks = [
        block.text for block in message.content
        if hasattr(block, "text") and block.text
    ]

    if not text_blocks:
        raise RuntimeError("Claude response contained no readable text")

    return "\n\n".join(text_blocks)

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:
    st.markdown("## 🚀 Features")
    st.markdown("""
- 50+ SaaS companies  
- Multi-video analysis  
- Realistic pricing  
- Ready-to-send outreach emails  
""")

# =========================================================
# MAIN UI
# =========================================================

video_urls = st.text_area(
    "Paste YouTube video URLs (one per line)",
    height=120
)

show_debug = st.checkbox("Show debug info")

if st.button("🚀 Generate Sponsorship Pitch", use_container_width=True):

    urls = [u.strip() for u in video_urls.splitlines() if u.strip()]
    if not urls:
        st.error("Please enter at least one YouTube URL.")
        st.stop()

    valid_videos = []
    for url in urls:
        vid = extract_video_id(url)
        if vid:
            valid_videos.append(vid)
        else:
            st.warning(f"Invalid URL skipped: {url}")

    if not valid_videos:
        st.error("No valid YouTube URLs found.")
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

        status.text("🤖 Analyzing with Claude 3.5 Sonnet (20–40 seconds)…")
        progress.progress(0.9)

        pitch = analyze_with_improved_claude(
            combined_transcript,
            len(transcripts)
        )

        progress.progress(1.0)
        status.text("✅ Done")

        st.markdown("---")
        st.markdown("# 📊 Sponsorship Pitch")
        st.markdown(pitch)

        st.download_button(
            "📥 Download as Markdown",
            pitch,
            file_name="sponsorship_pitch.md",
            mime="text/markdown"
        )

        if show_debug:
            st.code(combined_transcript[:1000])

    except Exception as e:
        st.error(str(e))
        if show_debug:
            st.code(traceback.format_exc())
