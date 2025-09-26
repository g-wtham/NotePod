# filename: backend/main.py
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import json

import crud, models, schemas, ai_service
from database import SessionLocal, engine, get_db

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# CORS Middleware to allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins, change to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- DUMMY DATA SETUP ---
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    # Check if videos exist to avoid re-populating
    if crud.get_video(db, 1) is None:
        print("Populating database with initial data...")
        videos_to_add = [
            {"title": "Introduction to Big O Notation", "youtube_url": "https://www.youtube.com/embed/v4cd1O4zkGw"},
            {"title": "Arrays & Hashing For Beginners", "youtube_url": "https://www.youtube.com/embed/gVgmo-qMV7Q"},
            {"title": "Two Pointers Technique", "youtube_url": "https://www.youtube.com/embed/M9Yhk35S_aY"},
            {"title": "Sliding Window Algorithm", "youtube_url": "https://www.youtube.com/embed/3i3p_I_MWY0"},
            {"title": "Binary Search Explained", "youtube_url": "https://www.youtube.com/embed/P3YID7liBug"},
        ]
        for video_data in videos_to_add:
            crud.create_video(db, schemas.VideoCreate(**video_data))
    
    crud.get_or_create_dummy_user(db)
    print("Database is ready.")
    db.close()


# --- STUDENT PORTAL API ---

# Hardcoding user_id=1 for this MVP
@app.get("/api/lessons")
def get_all_lessons(db: Session = Depends(get_db)):
    """Get the full list of lessons and their status for the sidebar."""
    user_id = 1 
    return crud.get_videos_with_status(db, user_id)

@app.get("/api/lessons/{lesson_id}")
def get_lesson_details(lesson_id: int, db: Session = Depends(get_db)):
    """Get a single lesson's data and generate a quiz for it."""
    video = crud.get_video(db, video_id=lesson_id)
    if not video:
        raise HTTPException(status_code=404, detail="Lesson not found")

    quiz_questions = ai_service.generate_quiz(video.transcript)
    
    return {
        "id": video.id,
        "title": video.title,
        "youtube_url": video.youtube_url,
        "quiz": quiz_questions
    }

@app.post("/api/lessons/{lesson_id}/submit")
async def submit_lesson(
    lesson_id: int,
    notes_file: UploadFile = File(...),
    quiz_answers_json: str = Form(...),
    db: Session = Depends(get_db)
):
    """Submit notes and quiz answers for evaluation."""
    user_id = 1
    video = crud.get_video(db, video_id=lesson_id)
    if not video:
        raise HTTPException(status_code=404, detail="Lesson not found")

    # ✅ Read notes file
    notes_bytes = await notes_file.read()
    notes_content_type = notes_file.content_type  # "application/pdf" | "image/png" | etc.

    # ✅ Parse quiz answers
    quiz_answers = json.loads(quiz_answers_json)

    # ✅ Call AI service with correct params
    evaluation = ai_service.evaluate_submission(
        transcript=video.transcript,
        notes_bytes=notes_bytes,
        notes_content_type=notes_content_type,
        quiz_answers=quiz_answers
    )
    
    # ✅ Update lesson status in DB if approved
    if evaluation.get("is_approved"):
        crud.update_lesson_status(db, user_id=user_id, video_id=lesson_id, is_completed=True)
    
    return evaluation


# --- TEACHER PORTAL API ---

@app.post("/api/teacher/videos")
def add_new_video(video: schemas.VideoCreate, db: Session = Depends(get_db)):
    """Allows a teacher to add a new video lesson."""
    return crud.create_video(db, video)

@app.get("/api/teacher/progress")
def get_student_progress(db: Session = Depends(get_db)):
    """A simplified endpoint to show student progress."""
    user_id = 1
    progress = crud.get_videos_with_status(db, user_id=user_id)
    total = len(progress)
    completed = sum(1 for p in progress if p['is_completed'])
    return {"student": "student1", "completed_lessons": completed, "total_lessons": total}
