from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Dict, Any
from datetime import datetime, date, timedelta
import math

from app.database import get_db
from app.models.models import User, Workout, WorkoutExercise, Achievement, UserAchievement, Leaderboard
from app.schemas.schemas import WorkoutCreate, WorkoutOut, DashboardStats, LeaderboardOut
from app.routers.auth import get_current_user
from app.services.report_service import generate_workout_csv, generate_workout_excel, generate_workout_pdf

router = APIRouter(prefix="/workouts", tags=["workouts"])

# Helper function to seed achievements if they don't exist
def ensure_achievements_exist(db: Session):
    default_achievements = [
        {"code": "FIRST_WORKOUT", "title": "First Step", "description": "Logged your first workout session!", "xp_reward": 100, "badge_icon": "Award"},
        {"code": "REPS_50", "title": "Half Century", "description": "Completed 50 total valid repetitions!", "xp_reward": 200, "badge_icon": "Zap"},
        {"code": "STREAK_5", "title": "High Five", "description": "Maintained a 5-day workout streak!", "xp_reward": 300, "badge_icon": "Flame"},
        {"code": "FORM_MASTER", "title": "Form Master", "description": "Achieved a workout form score of 95% or higher!", "xp_reward": 250, "badge_icon": "ShieldCheck"},
    ]
    for ach in default_achievements:
        exists = db.query(Achievement).filter(Achievement.code == ach["code"]).first()
        if not exists:
            db.add(Achievement(**ach))
    db.commit()

@router.post("/", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
def create_workout(workout_in: WorkoutCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_achievements_exist(db)
    
    # 1. Create Workout record
    new_workout = Workout(
        user_id=current_user.id,
        duration_seconds=workout_in.duration_seconds,
        calories_burned=workout_in.calories_burned,
        score=workout_in.score,
        difficulty=workout_in.difficulty,
        notes=workout_in.notes,
        video_url=workout_in.video_url
    )
    db.add(new_workout)
    db.commit()
    db.refresh(new_workout)
    
    # 2. Add Exercises details & Calculate totals
    total_valid_reps = 0
    for ex in workout_in.exercises:
        total_valid_reps += ex.valid_reps
        db_exercise = WorkoutExercise(
            workout_id=new_workout.id,
            exercise_name=ex.exercise_name,
            variation=ex.variation,
            total_reps=ex.total_reps,
            valid_reps=ex.valid_reps,
            invalid_reps=ex.invalid_reps,
            average_speed_seconds=ex.average_speed_seconds,
            best_streak=ex.best_streak
        )
        db.add(db_exercise)
    
    # 3. Calculate Gamification: XP and Level-up
    # Formula: 100 XP base, + 10 XP per valid rep
    xp_gained = 100 + (total_valid_reps * 10)
    current_user.total_xp += xp_gained
    
    # Level-up Formula: Level = 1 + floor(sqrt(XP / 100))
    new_level = 1 + int(math.floor(math.sqrt(current_user.total_xp / 100.0)))
    level_up = False
    if new_level > current_user.level:
        current_user.level = new_level
        level_up = True
        
    # 4. Streaks logic
    today = date.today()
    if current_user.last_workout_date:
        diff = (today - current_user.last_workout_date).days
        if diff == 1:
            current_user.streak_count += 1
        elif diff > 1:
            current_user.streak_count = 1
    else:
        current_user.streak_count = 1
    
    current_user.last_workout_date = today
    db.commit()

    # 5. Check and unlock Achievements
    unlocked_achievements = []
    
    # FIRST_WORKOUT
    first_ach = db.query(Achievement).filter(Achievement.code == "FIRST_WORKOUT").first()
    if first_ach:
        already_has = db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id,
            UserAchievement.achievement_id == first_ach.id
        ).first()
        if not already_has:
            ua = UserAchievement(user_id=current_user.id, achievement_id=first_ach.id)
            db.add(ua)
            current_user.total_xp += first_ach.xp_reward
            unlocked_achievements.append(first_ach)

    # REPS_50
    reps_ach = db.query(Achievement).filter(Achievement.code == "REPS_50").first()
    if reps_ach:
        total_reps_done = db.query(func.sum(WorkoutExercise.valid_reps)).join(Workout).filter(
            Workout.user_id == current_user.id
        ).scalar() or 0
        if total_reps_done >= 50:
            already_has = db.query(UserAchievement).filter(
                UserAchievement.user_id == current_user.id,
                UserAchievement.achievement_id == reps_ach.id
            ).first()
            if not already_has:
                ua = UserAchievement(user_id=current_user.id, achievement_id=reps_ach.id)
                db.add(ua)
                current_user.total_xp += reps_ach.xp_reward
                unlocked_achievements.append(reps_ach)

    # STREAK_5
    streak_ach = db.query(Achievement).filter(Achievement.code == "STREAK_5").first()
    if streak_ach and current_user.streak_count >= 5:
        already_has = db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id,
            UserAchievement.achievement_id == streak_ach.id
        ).first()
        if not already_has:
            ua = UserAchievement(user_id=current_user.id, achievement_id=streak_ach.id)
            db.add(ua)
            current_user.total_xp += streak_ach.xp_reward
            unlocked_achievements.append(streak_ach)

    # FORM_MASTER
    form_ach = db.query(Achievement).filter(Achievement.code == "FORM_MASTER").first()
    if form_ach and new_workout.score >= 95:
        already_has = db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id,
            UserAchievement.achievement_id == form_ach.id
        ).first()
        if not already_has:
            ua = UserAchievement(user_id=current_user.id, achievement_id=form_ach.id)
            db.add(ua)
            current_user.total_xp += form_ach.xp_reward
            unlocked_achievements.append(form_ach)

    db.commit()

    # Update leaderboard standing
    leaderboard_entry = db.query(Leaderboard).filter(Leaderboard.user_id == current_user.id).first()
    if leaderboard_entry:
        leaderboard_entry.total_xp = current_user.total_xp
        leaderboard_entry.level = current_user.level
    else:
        leaderboard_entry = Leaderboard(
            user_id=current_user.id,
            total_xp=current_user.total_xp,
            level=current_user.level
        )
        db.add(leaderboard_entry)
    db.commit()

    # Refresh user to reflect any achievement XP updates
    db.refresh(current_user)
    
    return new_workout

@router.get("/history", response_model=List[WorkoutOut])
def get_workout_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Workout).filter(Workout.user_id == current_user.id).order_by(desc(Workout.date)).all()

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    workouts = db.query(Workout).filter(Workout.user_id == current_user.id).order_by(desc(Workout.date)).all()
    
    total_workouts = len(workouts)
    total_duration_minutes = sum(w.duration_seconds for w in workouts) / 60.0
    total_calories_burned = sum(w.calories_burned for w in workouts)
    
    # Get recent workouts (up to 5)
    recent_workouts = workouts[:5]
    
    # Calculate Exercise Distribution & aggregations
    exercises_query = db.query(
        WorkoutExercise.exercise_name,
        func.sum(WorkoutExercise.total_reps).label("total_reps"),
        func.sum(WorkoutExercise.valid_reps).label("valid_reps"),
        func.sum(WorkoutExercise.invalid_reps).label("invalid_reps")
    ).join(Workout).filter(Workout.user_id == current_user.id).group_by(WorkoutExercise.exercise_name).all()
    
    exercise_distribution = []
    for ex in exercises_query:
        accuracy = (ex.valid_reps / ex.total_reps * 100) if ex.total_reps > 0 else 0.0
        exercise_distribution.append({
            "exercise_name": ex.exercise_name,
            "total_reps": int(ex.total_reps),
            "valid_reps": int(ex.valid_reps),
            "invalid_reps": int(ex.invalid_reps),
            "accuracy": round(accuracy, 1)
        })

    # Calories trend (last 7 workouts or days)
    # We can group by date
    calories_trend_query = db.query(
        func.date(Workout.date).label("w_date"),
        func.sum(Workout.calories_burned).label("calories")
    ).filter(Workout.user_id == current_user.id).group_by(func.date(Workout.date)).order_by(func.date(Workout.date)).all()
    
    calories_trend = []
    for row in calories_trend_query:
        if isinstance(row.w_date, str):
            date_str = row.w_date
        elif hasattr(row.w_date, "strftime"):
            date_str = row.w_date.strftime("%Y-%m-%d")
        else:
            date_str = str(row.w_date)
            
        calories_trend.append({
            "date": date_str,
            "calories": float(row.calories)
        })
    
    return {
        "streak_count": current_user.streak_count,
        "total_workouts": total_workouts,
        "total_xp": current_user.total_xp,
        "level": current_user.level,
        "total_duration_minutes": round(total_duration_minutes, 1),
        "total_calories_burned": round(total_calories_burned, 1),
        "recent_workouts": recent_workouts,
        "exercise_distribution": exercise_distribution,
        "calories_trend": calories_trend
    }

@router.get("/export")
def export_workout_report(
    format: str = Query(..., regex="^(csv|excel|pdf)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    workouts = db.query(Workout).filter(Workout.user_id == current_user.id).order_by(desc(Workout.date)).all()
    
    if format == "csv":
        csv_bytes = generate_workout_csv(workouts)
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=fitvision_report_{current_user.id}.csv"}
        )
    elif format == "excel":
        excel_bytes = generate_workout_excel(workouts)
        return Response(
            content=excel_bytes,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename=fitvision_report_{current_user.id}.xlsx"}
        )
    elif format == "pdf":
        pdf_bytes = generate_workout_pdf(current_user.full_name, workouts)
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=fitvision_report_{current_user.id}.pdf"}
        )

@router.get("/leaderboard", response_model=List[LeaderboardOut])
def get_global_leaderboard(db: Session = Depends(get_db)):
    leaderboard_records = db.query(
        Leaderboard.id,
        Leaderboard.user_id,
        Leaderboard.total_xp,
        Leaderboard.level,
        User.full_name
    ).join(User, Leaderboard.user_id == User.id).order_by(desc(Leaderboard.total_xp)).limit(10).all()
    
    results = []
    for rank, rec in enumerate(leaderboard_records, 1):
        results.append({
            "id": rec.id,
            "user_id": rec.user_id,
            "full_name": rec.full_name,
            "total_xp": rec.total_xp,
            "level": rec.level,
            "rank": rank
        })
    return results

@router.get("/achievements", response_model=List[Dict[str, Any]])
def get_achievements(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_achievements_exist(db)
    
    achievements = db.query(Achievement).all()
    unlocked_ids = {
        ua.achievement_id for ua in db.query(UserAchievement).filter(
            UserAchievement.user_id == current_user.id
        ).all()
    }
    
    results = []
    for ach in achievements:
        results.append({
            "id": ach.id,
            "code": ach.code,
            "title": ach.title,
            "description": ach.description,
            "xp_reward": ach.xp_reward,
            "badge_icon": ach.badge_icon,
            "unlocked": ach.id in unlocked_ids
        })
        
    return results
