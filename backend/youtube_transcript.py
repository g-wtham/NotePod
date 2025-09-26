from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from a standard video URL or short URL."""
    if "watch?v=" in url:
        return url.split("v=")[1].split("&")[0]
    elif "youtu.be/" in url:
        return url.split("/")[-1].split("?")[0]
    elif "embed/" in url:
        return url.split("/")[-1].split("?")[0]
    return None


def get_youtube_transcript(video_url: str):
    video_id = extract_video_id(video_url)
    if not video_id:
        print("Could not extract video ID from URL.")
        return

    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(video_id, languages=['en'])

        transcript_text = " ".join([snippet.text for snippet in transcript])
        print("\n--- Transcript ---\n")
        print(transcript_text)
    except NoTranscriptFound:
        print("No transcript available for this video.")
    except Exception as e:
        print(f"Error fetching transcript: {e}")


if __name__ == "__main__":
    url = "https://www.youtube.com/watch?v=NTKC-LExZlI"
    get_youtube_transcript(url)
