from youtube_transcript_api import YouTubeTranscriptApi
import requests

def get_transcript(video_url, proxy: str = None):
    # Standard URL extraction
    if "watch?v=" in video_url:
        video_id = video_url.split("v=")[1].split("&")[0]
    else:
        video_id = video_url.split("/")[-1]
    
    try:
        # Prepare an HTTP session; optionally configure proxy
        session = requests.Session()
        if proxy:
            session.proxies.update({"http": proxy, "https": proxy})

        # Use an instance and fetch(), which returns a FetchedTranscript
        ytt = YouTubeTranscriptApi(http_client=session)
        fetched = ytt.fetch(video_id)

        # Convert to raw data (list of dicts) and join texts
        if hasattr(fetched, "to_raw_data"):
            transcript_list = fetched.to_raw_data()
        else:
            transcript_list = list(fetched)

        full_text = " ".join([item['text'] for item in transcript_list])

        return full_text[:3000]
    except Exception as e:
        return f"Error: {type(e).__name__}: {e}"

# Run the script
if __name__ == "__main__":
    video_url = "https://www.youtube.com/watch?v=ssYt09bCgUY"
    context = get_transcript(video_url)

    with open("video_transcript.txt", "w", encoding="utf-8") as f:
        f.write(context)

    print("✅ Success! Transcript saved to video_transcript.txt")

    print("✅ Success! Transcript saved to video_transcript.txt")