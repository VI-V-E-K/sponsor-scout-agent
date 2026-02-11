from youtube_transcript_api import YouTubeTranscriptApi

def get_transcript(video_url):
    # Standard URL extraction
    if "watch?v=" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
    else:
        video_id = video_url.split("/")[-1]
    
    try:
        # Initialize the API object
        ytt_api = YouTubeTranscriptApi()
        
        # Fetch the transcript object
        transcript_obj = ytt_api.fetch(video_id)
        
        # 2026 FIX: Use .text because the snippet is an object, not a dictionary
        full_text = " ".join([item.text for item in transcript_obj])
        
        return full_text[:3000] 
    except Exception as e:
        return f"Error: {e}"

# Run the script
video_url = "https://www.youtube.com/watch?v=ssYt09bCgUY"
context = get_transcript(video_url)

with open("video_transcript.txt", "w", encoding="utf-8") as f:
    f.write(context)

print("✅ Success! Transcript saved to video_transcript.txt")