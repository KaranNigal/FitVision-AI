from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional
from datetime import datetime, date

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None
    user_id: Optional[int] = None


# --- User Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    full_name: str

class UserCreate(UserBase):
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None

class UserOut(UserBase):
    id: int
    profile_pic_url: Optional[str] = None
    streak_count: int
    last_workout_date: Optional[date] = None
    total_xp: int
    level: int
    created_at: datetime

    class Config:
        from_attributes = True


# --- Workout Exercise Schemas ---
class WorkoutExerciseBase(BaseModel):
    exercise_name: str
    variation: str
    total_reps: int
    valid_reps: int
    invalid_reps: int
    average_speed_seconds: float
    best_streak: int

class WorkoutExerciseCreate(WorkoutExerciseBase):
    pass

class WorkoutExerciseOut(WorkoutExerciseBase):
    id: int
    workout_id: int

    class Config:
        from_attributes = True


# --- Workout Schemas ---
class WorkoutBase(BaseModel):
    duration_seconds: int
    calories_burned: float
    score: int
    difficulty: str
    notes: Optional[str] = None
    video_url: Optional[str] = None

class WorkoutCreate(WorkoutBase):
    exercises: List[WorkoutExerciseCreate]

class WorkoutOut(WorkoutBase):
    id: int
    user_id: int
    date: datetime
    exercises: List[WorkoutExerciseOut]

    class Config:
        from_attributes = True


# --- Achievement Schemas ---
class AchievementBase(BaseModel):
    code: str
    title: str
    description: str
    xp_reward: int
    badge_icon: str

class AchievementOut(AchievementBase):
    id: int

    class Config:
        from_attributes = True

class UserAchievementOut(BaseModel):
    id: int
    user_id: int
    achievement: AchievementOut
    unlocked_at: datetime

    class Config:
        from_attributes = True


# --- Leaderboard Schemas ---
class LeaderboardOut(BaseModel):
    id: int
    user_id: int
    user_name: str = Field(..., validation_alias="full_name")  # Custom field to resolve user full name
    total_xp: int
    level: int
    rank: Optional[int] = None

    class Config:
        from_attributes = True


# --- Dashboard Analytics ---
class DailyCaloriesTrend(BaseModel):
    date: str
    calories: float

class ExerciseStats(BaseModel):
    exercise_name: str
    total_reps: int
    valid_reps: int
    invalid_reps: int
    accuracy: float

class DashboardStats(BaseModel):
    streak_count: int
    total_workouts: int
    total_xp: int
    level: int
    total_duration_minutes: float
    total_calories_burned: float
    recent_workouts: List[WorkoutOut]
    exercise_distribution: List[ExerciseStats]
    calories_trend: List[DailyCaloriesTrend]
