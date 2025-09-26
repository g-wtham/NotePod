# filename: backend/models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    # In a real app, store a hashed password
    hashed_password = Column(String)

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    youtube_url = Column(String)
    # The real transcript will be fetched and stored here
    transcript = Column(Text, nullable=False)
    order = Column(Integer, unique=True, nullable=False) # To maintain lesson order

class LessonStatus(Base):
    __tablename__ = "lesson_statuses"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    video_id = Column(Integer, ForeignKey("videos.id"))
    is_completed = Column(Boolean, default=False)