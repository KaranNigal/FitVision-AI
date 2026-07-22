import sys
import os
from datetime import datetime, timedelta

# Adjust path to import backend
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.database import engine, Base, SessionLocal
from app.models.models import User, Workout, WorkoutExercise, Leaderboard, Achievement, UserAchievement

def seed_athlete_data(email: str):
    db = SessionLocal()
    try:
        # 1. Fetch the user
        user = db.query(User).filter(User.email == email).first()
        if not user:
            print(f"Error: User with email '{email}' not found. Please sign up in the browser first!")
            return
            
        print(f"Seeding 7 days of training history for {user.full_name} ({user.email})...")

        # Clean old workouts to avoid duplicate seeding
        # SQLAlchemy cascading rules automatically delete related WorkoutExercise entries
        db.query(Workout).filter(Workout.user_id == user.id).delete(synchronize_session=False)
        db.query(UserAchievement).filter(UserAchievement.user_id == user.id).delete(synchronize_session=False)
        db.commit()

        # Seed achievements check
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

        # Workout scenarios
        scenarios = [
            {"days_ago": 6, "exercise": "Squats", "var": "Standard", "total": 20, "val": 18, "inval": 2, "sec": 120, "kcal": 80, "score": 90},
            {"days_ago": 5, "exercise": "Pushups", "var": "Standard", "total": 15, "val": 12, "inval": 3, "sec": 90, "kcal": 95, "score": 80},
            {"days_ago": 4, "exercise": "Jumping Jacks", "var": "Standard", "total": 40, "val": 40, "inval": 0, "sec": 180, "kcal": 110, "score": 100},
            {"days_ago": 3, "exercise": "Squats", "var": "Standard", "total": 30, "val": 28, "inval": 2, "sec": 150, "kcal": 130, "score": 93},
            {"days_ago": 2, "exercise": "Pushups", "var": "Wide", "total": 20, "val": 19, "inval": 1, "sec": 110, "kcal": 140, "score": 95},
            {"days_ago": 1, "exercise": "Lunges", "var": "Standard", "total": 24, "val": 22, "inval": 2, "sec": 160, "kcal": 125, "score": 91},
            {"days_ago": 0, "exercise": "Pushups", "var": "Diamond", "total": 25, "val": 24, "inval": 1, "sec": 140, "kcal": 160, "score": 96},
        ]

        total_xp = 0
        total_valid = 0

        # Loop to insert history
        for s in scenarios:
            target_date = datetime.now() - timedelta(days=s["days_ago"])
            
            workout = Workout(
                user_id=user.id,
                duration_seconds=s["sec"],
                calories_burned=s["kcal"],
                score=s["score"],
                difficulty="Medium",
                notes=f"Seeded session of {s['exercise']}.",
                date=target_date
            )
            db.add(workout)
            db.commit()
            db.refresh(workout)

            ex = WorkoutExercise(
                workout_id=workout.id,
                exercise_name=s["exercise"],
                variation=s["var"],
                total_reps=s["total"],
                valid_reps=s["val"],
                invalid_reps=s["inval"],
                average_speed_seconds=2.4,
                best_streak=10
            )
            db.add(ex)
            db.commit()

            total_valid += s["val"]
            # Accumulate XP: 100 per workout + 10 per valid rep
            total_xp += 100 + (s["val"] * 10)

        # Unlock Achievements
        unlocked = []
        first_ach = db.query(Achievement).filter(Achievement.code == "FIRST_WORKOUT").first()
        reps_ach = db.query(Achievement).filter(Achievement.code == "REPS_50").first()
        streak_ach = db.query(Achievement).filter(Achievement.code == "STREAK_5").first()
        form_ach = db.query(Achievement).filter(Achievement.code == "FORM_MASTER").first()

        if first_ach:
            db.add(UserAchievement(user_id=user.id, achievement_id=first_ach.id))
            total_xp += first_ach.xp_reward
        if reps_ach and total_valid >= 50:
            db.add(UserAchievement(user_id=user.id, achievement_id=reps_ach.id))
            total_xp += reps_ach.xp_reward
        if streak_ach:
            db.add(UserAchievement(user_id=user.id, achievement_id=streak_ach.id))
            total_xp += streak_ach.xp_reward
        if form_ach:
            db.add(UserAchievement(user_id=user.id, achievement_id=form_ach.id))
            total_xp += form_ach.xp_reward
        db.commit()

        # Update User level & XP
        import math
        user.total_xp = total_xp
        user.level = 1 + int(math.floor(math.sqrt(total_xp / 100.0)))
        user.streak_count = 7
        user.last_workout_date = datetime.now().date()
        db.commit()

        # Sync Leaderboard
        lb = db.query(Leaderboard).filter(Leaderboard.user_id == user.id).first()
        if lb:
            lb.total_xp = total_xp
            lb.level = user.level
        else:
            lb = Leaderboard(user_id=user.id, total_xp=total_xp, level=user.level)
            db.add(lb)
        db.commit()

        print("SUCCESS: 7 days of training history successfully seeded!")
        print(f"Athlete Level updated to: Level {user.level}")
        print(f"Total XP: {user.total_xp}")
        print(f"Streak: {user.streak_count} Days")

    except Exception as e:
        print(f"Error seeding: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    email_arg = sys.argv[1] if len(sys.argv) > 1 else "karannigal16@gmail.com"
    seed_athlete_data(email_arg)
