# filename: backend/schemas.py
from pydantic import BaseModel
from typing import List, Optional

# Schema for creating a new video (Teacher Portal)
class VideoCreate(BaseModel):
    title: str
    youtube_url: str

# Schema for the AI's strict JSON output
class AIEvaluationResponse(BaseModel):
    combined_score: int
    is_approved: bool
    feedback: str
    quiz_score: Optional[int] = None
    notes_score: Optional[int] = None

# Schema for quiz submission from the frontend
class QuizAnswer(BaseModel):
    question: str
    selected_answer: str

class QuizSubmission(BaseModel):
    answers: List[QuizAnswer]