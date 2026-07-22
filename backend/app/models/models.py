from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date, JSON, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    profile_pic_url = Column(String, nullable=True)
    
    # Gamification and Stats
    streak_count = Column(Integer, default=0, nullable=False)
    last_workout_date = Column(Date, nullable=True)
    total_xp = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    user_achievements = relationship("UserAchievement", back_populates="user", cascade="all, delete-orphan")
    leaderboard_entry = relationship("Leaderboard", back_populates="user", uselist=False, cascade="all, delete-orphan")


class Workout(Base):
    __tablename__ = "workouts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    duration_seconds = Column(Integer, nullable=False)  # Total workout length
    calories_burned = Column(Float, nullable=False)
    score = Column(Integer, nullable=False)  # Form-based workout quality score (0-100)
    difficulty = Column(String, nullable=False)  # Easy, Medium, Hard
    notes = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    
    date = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="workouts")
    exercises = relationship("WorkoutExercise", back_populates="workout", cascade="all, delete-orphan")


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey("workouts.id", ondelete="CASCADE"), nullable=False)
    
    exercise_name = Column(String, nullable=False, index=True)  # e.g., "Push-ups", "Squats"
    variation = Column(String, nullable=False)  # e.g., "Standard", "Diamond", "Wide"
    
    total_reps = Column(Integer, nullable=False, default=0)
    valid_reps = Column(Integer, nullable=False, default=0)
    invalid_reps = Column(Integer, nullable=False, default=0)
    
    average_speed_seconds = Column(Float, nullable=False, default=0.0)
    best_streak = Column(Integer, nullable=False, default=0)

    # Relationships
    workout = relationship("Workout", back_populates="exercises")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)  # e.g., "FIRST_PUSHUP"
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    xp_reward = Column(Integer, nullable=False, default=100)
    badge_icon = Column(String, nullable=False)  # Name of icon / asset name

    # Relationships
    user_achievements = relationship("UserAchievement", back_populates="achievement", cascade="all, delete-orphan")


class UserAchievement(Base):
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id", ondelete="CASCADE"), nullable=False)
    unlocked_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")


class Leaderboard(Base):
    __tablename__ = "leaderboard"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    total_xp = Column(Integer, nullable=False, default=0)
    level = Column(Integer, nullable=False, default=1)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="leaderboard_entry")
