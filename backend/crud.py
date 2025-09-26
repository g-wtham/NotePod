# filename: backend/crud.py
from sqlalchemy.orm import Session
from youtube_transcript_api import YouTubeTranscriptApi
import models, schemas

def extract_video_id(url: str):
    """Extracts the YouTube video ID from various URL formats."""
    try:
        if "embed" in url:
            return url.split("/")[-1].split("?")[0]
        elif "watch" in url:
            return url.split("v=")[1].split("&")[0]
        elif "youtu.be" in url:
            return url.split("/")[-1].split("?")[0]
    except (IndexError, AttributeError):
        return None
    return None

def get_transcript(video_id: str):
    """Fetches and formats a transcript for a given YouTube video ID."""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        return " ".join([item['text'] for item in transcript_list])
    except Exception as e:
        print(f"Could not fetch transcript for video ID {video_id}: {e}")
        return "Transcript not available for this video."

def get_or_create_dummy_user(db: Session):
    user = db.query(models.User).filter(models.User.id == 1).first()
    if not user:
        user = models.User(id=1, username="student1", hashed_password="fake_password")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def get_videos_with_status(db: Session, user_id: int):
    videos = db.query(models.Video).order_by(models.Video.order).all()
    statuses = db.query(models.LessonStatus).filter(models.LessonStatus.user_id == user_id).all()
    status_map = {status.video_id: status.is_completed for status in statuses}
    
    result = []
    first_uncompleted_found = False
    for video in videos:
        is_completed = status_map.get(video.id, False)
        is_locked = True

        if is_completed or not first_uncompleted_found:
            is_locked = False
        
        if not is_completed and not first_uncompleted_found:
            first_uncompleted_found = True

        result.append({
            "id": video.id,
            "title": video.title,
            "is_completed": is_completed,
            "is_locked": is_locked
        })
        
    return result

def get_video(db: Session, video_id: int):
    return db.query(models.Video).filter(models.Video.id == video_id).first()

def create_video(db: Session, video: schemas.VideoCreate):
    max_order = db.query(models.Video).count()
    
    # Fetch real transcript when a video is created
    video_id = extract_video_id(video.youtube_url)
    transcript_text = "Placeholder transcript..."
    if video_id:
        print(f"Fetching transcript for video ID: {video_id}")
        transcript_text = get_transcript(video_id)
    else:
        print(f"Could not extract video ID from URL: {video.youtube_url}")

    db_video = models.Video(
        title=video.title,
        youtube_url=video.youtube_url,
        transcript=transcript_text,
        order=max_order + 1
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)
    return db_video
    
def update_lesson_status(db: Session, user_id: int, video_id: int, is_completed: bool):
    status = db.query(models.LessonStatus).filter_by(user_id=user_id, video_id=video_id).first()
    if not status:
        status = models.LessonStatus(user_id=user_id, video_id=video_id)
        db.add(status)
    status.is_completed = is_completed
    db.commit()
    return status