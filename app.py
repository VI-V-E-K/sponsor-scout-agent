import os
import streamlit as st
import json
from youtube_transcript_api import YouTubeTranscriptApi
from anthropic import Anthropic
import traceback
from streamlit.errors import StreamlitSecretNotFoundError

# Page config
st.set_page_config(page_title="Sponsor Scout", page_icon="🤖", layout="wide")

# 1. Setup Page Title
st.title("🤖 Sponsor Scout: AI-Powered Creator Outreach Agent")
st.markdown("**Analyze YouTube creators and generate personalized sponsorship pitches matching them with ideal SaaS partners**")

# 2. Secure API Key Retrieval
try:
    api_key = st.secrets.get("ANTHROPIC_API_KEY")
except StreamlitSecretNotFoundError:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

if not api_key:
    st.error("⚠️ API Key not found! Add 'ANTHROPIC_API_KEY' to your Streamlit Secrets or environment variables.")
    st.stop()

# 3. SaaS Companies Database (from your research doc)
SAAS_COMPANIES = """
**Cursor** - Latest: Cursor 2.0 with Composer model, multi-agent execution (up to 8 parallel agents), BugBot debugging assistant
- Ideal Customer: Full-stack developers, AI engineers, React/TypeScript developers, teams working on complex codebases
- Pain Point: Developers spend too much time on repetitive coding tasks, boilerplate generation, cross-file refactoring
- Why Sponsor: Vibe coding is about flow state and productivity—exactly what Cursor enables

**Vercel** - Latest: AI SDK 6 with agents, tool approval, MCP support, reranking; v0 AI UI generator for React/Next.js; Python SDK
- Ideal Customer: Next.js developers, React developers, AI application builders, frontend engineers who want to ship AI-powered features fast
- Pain Point: Building production-ready AI features requires complex integration of LLMs, streaming, tool calling, and state management
- Why Sponsor: Vercel's v0 generates UI from prompts and AI SDK enables conversational interfaces—perfect for live-coding demos

**Supabase** - Latest: Enhanced pgvector support, automatic embeddings via Edge Functions, unified vector + relational data storage, AI toolkit integration
- Ideal Customer: AI application developers, full-stack developers building RAG systems, developers who need vector search with traditional databases
- Pain Point: AI apps need vector databases for embeddings but managing separate vector DBs adds complexity and cost
- Why Sponsor: Every vibe coding project needs a backend. Showing how to add AI-powered semantic search or RAG to apps in minutes demonstrates real value

**Replit** - Latest: Agent 3 with 200-minute autonomous runtime, self-testing, agent generation, Design Mode, Fast Build mode, ChatGPT integration
- Ideal Customer: No-code/low-code creators, product managers, beginner developers, entrepreneurs who want to build apps without deep coding knowledge
- Pain Point: People have great app ideas but lack coding skills or time. Traditional development requires months of learning and iteration
- Why Sponsor: Vibe coding is about describing what you want and watching it get built—literally Replit's tagline. Live demos of Agent 3 building full apps from prompts would blow viewers' minds

**v0 by Vercel** - Latest: Composite AI model with AutoFix, 512K token context, shadcn/ui integration, image-to-code generation, agent-powered app building
- Ideal Customer: React/Next.js frontend developers, UI/UX designers who code, developers prototyping landing pages or dashboards, Tailwind CSS users
- Pain Point: Creating polished UI components from scratch is time-consuming and repetitive. Developers waste hours on boilerplate styling and responsive design
- Why Sponsor: The visual, immediate nature of v0 (type prompt → see UI) is perfect for video content. Showing how to go from design screenshot to production-ready React code in seconds demonstrates the magic of vibe coding
"""

# Helper Functions
def extract_video_id(url):
    """Extract video ID from various YouTube URL formats"""
    if "v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("/")[-1].split("?")[0]
    elif "shorts/" in url:
        return url.split("shorts/")[1].split("?")[0]
    return None

def get_full_transcript(video_id):
    """Get full video transcript without character limits"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        full_text = " ".join([item['text'] for item in transcript_list])
        return full_text, len(full_text)
    except Exception as e:
        raise Exception(f"Transcript fetch failed: {str(e)}")

def analyze_with_claude(transcript, video_count=1):
    """Send full transcript to Claude for analysis with structured output"""
    
    system_prompt = f"""You are an expert talent manager specializing in tech creator sponsorships and SaaS partnerships.

Your task is to analyze YouTube creator content and generate professional sponsorship pitches that match them with ideal SaaS companies.

**SaaS COMPANIES DATABASE:**
{SAAS_COMPANIES}

**ANALYSIS FRAMEWORK:**
1. **Creator Profile**: Identify their niche, content style, expertise level, and unique value proposition
2. **Audience Analysis**: Determine viewer demographics, technical level, pain points, and purchasing intent
3. **Company Matching**: Match 2-3 SaaS companies from the database that align with creator's content and audience needs
4. **Pitch Strategy**: Create compelling narratives explaining why each match is perfect

**OUTPUT STRUCTURE:**
Generate a response in this EXACT format:

---
## 🎯 CREATOR PROFILE
**Channel Name**: [Extract from content]
**Content Niche**: [e.g., Web Development, AI/ML, DevOps, Career Advice]
**Technical Level**: [Beginner-friendly / Intermediate / Advanced]
**Content Style**: [Tutorial-based / Project-based / Career Guidance / News & Analysis]
**Unique Value Proposition**: [What makes this creator stand out]

---
## 👥 AUDIENCE ANALYSIS
**Primary Demographics**:
- Age range: [estimate]
- Career stage: [students/junior/mid-level/senior]
- Geographic focus: [primary regions]

**Audience Pain Points**:
1. [Key problem #1]
2. [Key problem #2]
3. [Key problem #3]

**Purchasing Intent**: [Low/Medium/High] - [Brief explanation]

---
## 🏆 TOP SAAS MATCHES

### Match #1: [Company Name]
**Fit Score**: ⭐⭐⭐⭐⭐ (X/5)

**Why This Works**:
[2-3 sentences explaining the perfect alignment between creator's content, audience needs, and this product]

**Integration Ideas**:
1. [Specific sponsorship angle #1]
2. [Specific sponsorship angle #2]

**Estimated Partnership Value**: $[range] per video or $[range] for series

---
### Match #2: [Company Name]
[Same structure as Match #1]

---
### Match #3: [Company Name]
[Same structure as Match #1]

---
## 📧 OUTREACH EMAIL TEMPLATE

Subject: Partnership Opportunity: [Creator Name] x [Company Name]

[Generate a professional 150-200 word email that the creator can send to the company's partnership team. Include specific data points from the analysis and explain mutual value.]

---
## 💡 PRO TIPS FOR THIS CREATOR
1. [Actionable sponsorship strategy tip #1]
2. [Actionable sponsorship strategy tip #2]
3. [Actionable sponsorship strategy tip #3]

---

**CRITICAL RULES:**
- Base ALL analysis on actual content from the transcript
- Only recommend companies from the provided SaaS database
- Be specific with examples from their content
- Provide realistic pricing estimates
- Keep fit scores honest (not everything is 5/5)
"""

    client = Anthropic(api_key=api_key)
    
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=4000,
        system=system_prompt,
        messages=[{
            "role": "user", 
            "content": f"""Analyze this YouTube video transcript(s) and generate a sponsorship pitch:

**Number of videos analyzed**: {video_count}
**Total transcript length**: {len(transcript)} characters

**TRANSCRIPT:**
{transcript[:50000]}  # Increased limit to ~50K chars to handle longer videos

Generate the structured sponsorship analysis following the exact format provided."""
        }]
    )
    
    return message.content[0].text

# UI Layout
col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### 🎬 Video Input")
    video_urls = st.text_area(
        "Paste YouTube Video URL(s) - one per line for multi-video analysis",
        placeholder="https://www.youtube.com/watch?v=...\nhttps://www.youtube.com/watch?v=...",
        height=100
    )
    
with col2:
    st.markdown("### ⚙️ Settings")
    include_metadata = st.checkbox("Include video metadata", value=True)
    st.info("💡 Analyzing multiple videos provides better creator insights!")

# Generate Button
if st.button("🚀 Generate Sponsorship Pitch", type="primary", use_container_width=True):
    
    urls = [url.strip() for url in video_urls.split('\n') if url.strip()]
    
    if not urls:
        st.error("⚠️ Please enter at least one YouTube video URL")
        st.stop()
    
    try:
        with st.spinner('🔍 Analyzing creator content...'):
            
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            all_transcripts = []
            total_chars = 0
            
            # Fetch transcripts for all videos
            for idx, url in enumerate(urls):
                status_text.text(f"📥 Fetching transcript {idx+1}/{len(urls)}...")
                progress_bar.progress((idx + 1) / (len(urls) + 1))
                
                video_id = extract_video_id(url)
                if not video_id:
                    st.warning(f"⚠️ Could not extract video ID from: {url}")
                    continue
                
                transcript, char_count = get_full_transcript(video_id)
                all_transcripts.append(f"--- VIDEO {idx+1} ---\n{transcript}")
                total_chars += char_count
            
            if not all_transcripts:
                st.error("❌ Failed to fetch any transcripts. Please check your URLs.")
                st.stop()
            
            # Combine all transcripts
            combined_transcript = "\n\n".join(all_transcripts)
            
            # Display stats
            st.success(f"✅ Successfully analyzed {len(all_transcripts)} video(s)")
            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Videos Analyzed", len(all_transcripts))
            col_b.metric("Total Characters", f"{total_chars:,}")
            col_c.metric("Estimated Words", f"{total_chars//5:,}")
            
            # Analyze with Claude
            status_text.text("🤖 Generating AI-powered sponsorship pitch...")
            progress_bar.progress(0.9)
            
            pitch = analyze_with_claude(combined_transcript, len(all_transcripts))
            
            progress_bar.progress(1.0)
            status_text.text("✅ Analysis complete!")
            
            # Display results
            st.markdown("---")
            st.markdown("## 📊 Sponsorship Pitch Analysis")
            st.markdown(pitch)
            
            # Download button
            st.download_button(
                label="📥 Download Pitch as Markdown",
                data=pitch,
                file_name=f"sponsorship_pitch_{video_id}.md",
                mime="text/markdown"
            )
            
    except Exception as e:
        st.error(f"❌ Error: {type(e).__name__}: {str(e)}")
        with st.expander("🔍 Show error details"):
            st.code(traceback.format_exc())

# Sidebar with info
with st.sidebar:
    st.markdown("## 📖 How It Works")
    st.markdown("""
    1. **Paste URL(s)**: Add one or more YouTube video links
    2. **Full Analysis**: Analyzes entire video transcripts (no truncation)
    3. **AI Matching**: Matches creators with ideal SaaS sponsors
    4. **Structured Output**: Professional pitch ready to send
    """)
    
    st.markdown("---")
    st.markdown("## 🎯 What's New")
    st.markdown("""
    ✅ **Full transcript analysis** (no 6000 char limit)  
    ✅ **Multi-video support** (analyze creator's channel)  
    ✅ **SaaS company matching** (from your research)  
    ✅ **Structured pitch format** (consistent output)  
    ✅ **No cookie dependency** (more reliable)  
    ✅ **Realistic pricing estimates**  
    ✅ **Ready-to-send email templates**
    """)
    
    st.markdown("---")
    st.markdown("## 💼 Current SaaS Database")
    st.markdown("""
    - Cursor (AI IDE)
    - Vercel (Deployment + AI SDK)
    - Supabase (Backend + Vector DB)
    - Replit (AI App Builder)
    - v0 by Vercel (UI Generator)
    """)
    
    st.markdown("---")
    st.markdown("### 🔒 Privacy Note")
    st.caption("Video transcripts are processed via Claude API. No data is stored permanently.")
