import numpy as np
import time
from typing import Dict, Any, List, Tuple, Optional

def calculate_angle(a: Tuple[float, float, float], b: Tuple[float, float, float], c: Tuple[float, float, float]) -> float:
    """
    Calculate the 2D angle (in degrees) formed by points a, b (vertex), and c in the XY plane.
    """
    a_arr = np.array([a[0], a[1]])
    b_arr = np.array([b[0], b[1]])
    c_arr = np.array([c[0], c[1]])
    
    ba = a_arr - b_arr
    bc = c_arr - b_arr
    
    cosine_angle = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-6)
    angle = np.arccos(np.clip(cosine_angle, -1.0, 1.0))
    return float(np.degrees(angle))

class ExerciseTracker:
    def __init__(self, exercise_name: str, target_variation: str = "Standard"):
        self.exercise_name = exercise_name.lower().strip()
        self.target_variation = target_variation
        
        # Rep counters
        self.rep_count = 0
        self.valid_reps = 0
        self.invalid_reps = 0
        
        # State machine variables
        self.stage = "up"  # "up" or "down" (or "open"/"closed" for jumping jacks)
        self.rep_started = False
        self.rep_start_time = 0.0
        self.rep_durations = []
        self.current_rep_valid = True
        self.current_rep_errors = []
        
        # Form analysis and scores
        self.streak = 0
        self.best_streak = 0
        self.form_scores = []
        self.feedback = "Get ready!"
        self.average_speed = 0.0
        
        # Plank specific variables
        self.plank_start_time = None
        self.plank_duration = 0.0
        
        # Burpee sequence state: "standing", "squatting", "plank", "pushup_down", "pushup_up", "jump"
        self.burpee_state = "standing"
        
        # Hindu pushup state sequence: "start_pike", "dip_down", "cobra_up"
        self.hindu_state = "start_pike"

    def process_landmarks(self, landmarks: List[Dict[str, float]]) -> Dict[str, Any]:
        """
        Process incoming landmarks.
        landmarks list is index-aligned with MediaPipe Pose Landmarks:
        11: L_shoulder, 12: R_shoulder
        13: L_elbow, 14: R_elbow
        15: L_wrist, 16: R_wrist
        23: L_hip, 24: R_hip
        25: L_knee, 26: R_knee
        27: L_ankle, 28: R_ankle
        """
        if len(landmarks) < 33:
            return {"error": "Insufficient landmarks detected"}

        # Helper to retrieve coords as tuple (x, y, z)
        def get_coords(idx: int) -> Tuple[float, float, float]:
            l = landmarks[idx]
            return (l.get("x", 0.0), l.get("y", 0.0), l.get("z", 0.0))

        # Core Landmarks
        l_shoulder, r_shoulder = get_coords(11), get_coords(12)
        l_elbow, r_elbow = get_coords(13), get_coords(14)
        l_wrist, r_wrist = get_coords(15), get_coords(16)
        l_hip, r_hip = get_coords(23), get_coords(24)
        l_knee, r_knee = get_coords(25), get_coords(26)
        l_ankle, r_ankle = get_coords(27), get_coords(28)

        # Compute Angles
        l_elbow_angle = calculate_angle(l_shoulder, l_elbow, l_wrist)
        r_elbow_angle = calculate_angle(r_shoulder, r_elbow, r_wrist)
        avg_elbow_angle = (l_elbow_angle + r_elbow_angle) / 2.0

        l_knee_angle = calculate_angle(l_hip, l_knee, l_ankle)
        r_knee_angle = calculate_angle(r_hip, r_knee, r_ankle)
        avg_knee_angle = (l_knee_angle + r_knee_angle) / 2.0

        l_hip_angle = calculate_angle(l_shoulder, l_hip, l_knee)
        r_hip_angle = calculate_angle(r_shoulder, r_hip, r_knee)
        avg_hip_angle = (l_hip_angle + r_hip_angle) / 2.0

        # Back / Trunk posture check (shoulder-hip-ankle line straightness)
        l_back_angle = calculate_angle(l_shoulder, l_hip, l_ankle)
        r_back_angle = calculate_angle(r_shoulder, r_hip, r_ankle)
        avg_back_angle = (l_back_angle + r_back_angle) / 2.0

        # Exercise Logic Router
        if self.exercise_name == "push-ups" or self.exercise_name == "pushups" or self.exercise_name == "pushup":
            self._track_pushups(
                avg_elbow_angle, avg_back_angle, avg_hip_angle,
                l_shoulder, r_shoulder, l_wrist, r_wrist, l_ankle, r_ankle,
                l_elbow_angle, r_elbow_angle
            )
        elif self.exercise_name == "squats" or self.exercise_name == "squat":
            self._track_squats(avg_knee_angle, avg_back_angle, avg_hip_angle)
        elif self.exercise_name == "lunges" or self.exercise_name == "lunge":
            self._track_lunges(l_knee_angle, r_knee_angle, avg_back_angle)
        elif self.exercise_name == "plank":
            self._track_plank(avg_back_angle, avg_hip_angle, l_shoulder, l_elbow)
        elif self.exercise_name == "pull-ups" or self.exercise_name == "pullups" or self.exercise_name == "pullup":
            self._track_pullups(avg_elbow_angle, l_shoulder, r_shoulder, l_wrist, r_wrist)
        elif self.exercise_name == "jumping jacks" or self.exercise_name == "jumpingjacks" or self.exercise_name == "jumping_jacks":
            self._track_jumping_jacks(l_wrist, r_wrist, l_ankle, r_ankle, l_shoulder, r_shoulder)
        elif self.exercise_name == "mountain climbers" or self.exercise_name == "mountainclimbers":
            self._track_mountain_climbers(l_hip_angle, r_hip_angle, avg_back_angle)
        elif self.exercise_name == "burpees" or self.exercise_name == "burpee":
            self._track_burpees(avg_elbow_angle, avg_knee_angle, avg_back_angle, l_shoulder, l_ankle)
        elif self.exercise_name == "sit-ups" or self.exercise_name == "situps" or self.exercise_name == "situp":
            self._track_situps(avg_hip_angle, avg_knee_angle)
        else:
            self.feedback = f"Unknown exercise: {self.exercise_name}"

        # Calculate live stats
        form_score = 100
        if self.current_rep_errors:
            form_score = max(40, 100 - (len(self.current_rep_errors) * 20))
        
        avg_score = int(np.mean(self.form_scores)) if self.form_scores else 100
        
        # Difficulty rating
        difficulty = "Medium"
        if self.exercise_name in ["plank", "jumping jacks", "squats"]:
            difficulty = "Easy"
        elif self.exercise_name in ["pull-ups", "burpees"]:
            difficulty = "Hard"

        return {
            "exercise_name": self.exercise_name.title(),
            "variation": self.target_variation,
            "rep_count": self.rep_count,
            "valid_reps": self.valid_reps,
            "invalid_reps": self.invalid_reps,
            "streak": self.streak,
            "best_streak": self.best_streak,
            "feedback": self.feedback,
            "current_stage": self.stage,
            "form_score": form_score,
            "average_score": avg_score,
            "average_speed": round(self.average_speed, 2),
            "difficulty": difficulty,
            "plank_duration": round(self.plank_duration, 1),
            "angles": {
                "elbow": round(avg_elbow_angle, 1),
                "knee": round(avg_knee_angle, 1),
                "hip": round(avg_hip_angle, 1),
                "back": round(avg_back_angle, 1)
            }
        }

    # --- PUSHUP TRACKING ---
    def _track_pushups(self, elbow_angle: float, back_angle: float, hip_angle: float,
                       l_sh: Tuple[float,float,float], r_sh: Tuple[float,float,float],
                       l_wr: Tuple[float,float,float], r_wr: Tuple[float,float,float],
                       l_ank: Tuple[float,float,float], r_ank: Tuple[float,float,float],
                       l_elb: float, r_elb: float):
        
        # Verify Pushup Variation
        detected_variation = self._detect_pushup_variation(l_sh, r_sh, l_wr, r_wr, hip_angle, l_sh, l_ank)
        
        # Let user's selected variation govern scoring / checking
        variation = self.target_variation

        # Core posture check: body should be relatively straight (except for Pike or Hindu)
        is_back_straight = back_angle > 155 and hip_angle > 155
        if variation in ["Pike", "Hindu"]:
            is_back_straight = True  # Pike and Hindu naturally bend hips

        # Start rep detection
        if not self.rep_started and elbow_angle > 150:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        # State transitions
        if self.stage == "up":
            # Down threshold
            down_threshold = 95
            if variation == "Wide":
                down_threshold = 100
            elif variation == "Diamond":
                down_threshold = 85

            if elbow_angle < down_threshold:
                self.stage = "down"
                self.feedback = "Push back up!"
                # Check posture on the way down
                if not is_back_straight:
                    self.current_rep_valid = False
                    if "Straighten your back" not in self.current_rep_errors:
                        self.current_rep_errors.append("Straighten your back")
        
        elif self.stage == "down":
            # Up threshold
            if elbow_angle > 145:
                self.stage = "up"
                self.rep_count += 1
                
                # Check depth
                if elbow_angle > 110 and variation not in ["Archer"]:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Go deeper")
                
                # Check individual variations rules
                if variation == "Archer":
                    # One arm bends, other straight
                    arm_diff = abs(l_elb - r_elb)
                    if arm_diff < 40:
                        self.current_rep_valid = False
                        self.current_rep_errors.append("Extend one arm fully")

                # Rep timing
                rep_end_time = time.time()
                rep_duration = rep_end_time - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)

                if rep_duration > 6.0:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Slow down / Speed up")

                # Handle Rep Outcome
                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Good Form! Perfect rep."
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    score = max(40, 100 - (len(self.current_rep_errors) * 20))
                    self.form_scores.append(score)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"

                # Reset for next rep
                self.rep_started = False

    def _detect_pushup_variation(self, l_sh, r_sh, l_wr, r_wr, hip_angle, l_shoulder, l_ankle) -> str:
        # Distance calculation helpers
        sh_width = abs(l_sh[0] - r_sh[0])
        wr_width = abs(l_wr[0] - r_wr[0])
        
        ratio = wr_width / (sh_width + 1e-6)
        
        if hip_angle < 120:
            return "Pike"
        elif ratio < 0.45:
            return "Diamond"
        elif ratio > 1.45:
            return "Wide"
        elif l_shoulder[1] < l_ankle[1] * 0.4:
            return "Decline"
        elif l_shoulder[1] > l_ankle[1] * 0.9:
            return "Incline"
        else:
            return "Standard"

    # --- SQUAT TRACKING ---
    def _track_squats(self, knee_angle: float, back_angle: float, hip_angle: float):
        # Standing posture: knees straight (>160°)
        if not self.rep_started and knee_angle > 160:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        if self.stage == "up":
            # Going down
            if knee_angle < 120:
                self.stage = "down"
                self.feedback = "Go lower to parallel!"
                
                # Check back alignment
                if back_angle < 130:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Straighten your back")

        elif self.stage == "down":
            # Rising up
            if knee_angle > 155:
                self.stage = "up"
                self.rep_count += 1

                # Check depth: knee angle at bottom should be < 100 degrees
                if knee_angle > 105:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Go deeper")

                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)

                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Good Form! Deep squat."
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    score = max(40, 100 - (len(self.current_rep_errors) * 20))
                    self.form_scores.append(score)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"

                self.rep_started = False

    # --- LUNGES TRACKING ---
    def _track_lunges(self, l_knee: float, r_knee: float, back_angle: float):
        # Rep starts standing
        if not self.rep_started and l_knee > 160 and r_knee > 160:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        active_knee = min(l_knee, r_knee)
        if self.stage == "up":
            if active_knee < 120:
                self.stage = "down"
                self.feedback = "Lower hips straight down!"
                if back_angle < 135:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Keep torso upright")
        
        elif self.stage == "down":
            if l_knee > 150 and r_knee > 150:
                self.stage = "up"
                self.rep_count += 1
                
                # Verify depth: active knee went below 95°
                if active_knee > 100:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Go deeper")
                
                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)

                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Perfect Lunge!"
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    self.form_scores.append(60)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"

                self.rep_started = False

    # --- PLANK TRACKING ---
    def _track_plank(self, back_angle: float, hip_angle: float, l_shoulder: Tuple[float,float,float], l_elbow: Tuple[float,float,float]):
        # Plank checks body straightness and forearm position
        # Body straightness (160° - 180° for back and hips)
        is_straight = back_angle > 155 and hip_angle > 155
        
        # Check if shoulders are aligned vertically above elbow (for forearm plank)
        is_aligned = abs(l_shoulder[0] - l_elbow[0]) < 0.15

        if is_straight and is_aligned:
            if self.plank_start_time is None:
                self.plank_start_time = time.time()
                self.feedback = "Plank active. Keep holding!"
            else:
                self.plank_duration = time.time() - self.plank_start_time
                self.feedback = f"✔ Good Form. Duration: {int(self.plank_duration)}s"
                self.form_scores.append(100)
        else:
            self.plank_start_time = None
            if not is_straight:
                self.feedback = "Keep hips level. Straighten back!"
                self.form_scores.append(60)
            elif not is_aligned:
                self.feedback = "Keep elbows directly below shoulders!"
                self.form_scores.append(70)

    # --- PULLUPS TRACKING ---
    def _track_pullups(self, elbow_angle: float, l_sh: Tuple[float,float,float], r_sh: Tuple[float,float,float],
                        l_wr: Tuple[float,float,float], r_wr: Tuple[float,float,float]):
        # Starts hanging (elbows straight)
        if not self.rep_started and elbow_angle > 150:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        if self.stage == "up":
            # Moving upwards
            if elbow_angle < 110:
                self.stage = "down"
                self.feedback = "Pull chin above the wrists!"
        
        elif self.stage == "down":
            # Back to hang
            if elbow_angle > 145:
                self.stage = "up"
                self.rep_count += 1
                
                # Check height reached: shoulders should go above wrist coordinates
                # In canvas, top is 0, bottom is 1. So Y of shoulder should be > Y of wrist (which means shoulder is lower than wrist). Wait!
                # Actually, if hanging, wrists are higher up than shoulders. So wrist.y is SMALLER than shoulder.y (e.g. wrist.y = 0.2, shoulder.y = 0.4).
                # When pulling up, shoulder.y goes up towards wrist.y, so shoulder.y becomes smaller than wrist.y (shoulder.y = 0.2, wrist.y = 0.3).
                # Thus, for a successful rep, shoulder.y must be less than wrist.y.
                avg_sh_y = (l_sh[1] + r_sh[1]) / 2.0
                avg_wr_y = (l_wr[1] + r_wr[1]) / 2.0
                
                if avg_sh_y > avg_wr_y: # Shoulders below wrists
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Pull higher (chin over bar)")

                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)

                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Excellent Pull Up!"
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    self.form_scores.append(60)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"

                self.rep_started = False

    # --- JUMPING JACKS ---
    def _track_jumping_jacks(self, l_wr, r_wr, l_ank, r_ank, l_sh, r_sh):
        # Check coordinates distance
        wrist_dist = abs(l_wr[0] - r_wr[0])
        ankle_dist = abs(l_ank[0] - r_ank[0])
        sh_width = abs(l_sh[0] - r_sh[0])

        if not self.rep_started:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True

        if self.stage == "closed":
            # Rep opens (arms up, feet wide)
            if wrist_dist > sh_width * 1.5 and ankle_dist > sh_width * 1.2:
                self.stage = "open"
                self.feedback = "Bring arms and legs back in!"
        
        elif self.stage == "open":
            # Rep closes (arms down, feet together)
            if wrist_dist < sh_width * 0.8 and ankle_dist < sh_width * 0.8:
                self.stage = "closed"
                self.rep_count += 1
                self.valid_reps += 1
                self.streak += 1
                self.best_streak = max(self.best_streak, self.streak)
                self.form_scores.append(100)
                self.feedback = "✔ Good Jack!"
                
                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)
                self.rep_started = False
                
        # Default start state
        if self.stage not in ["open", "closed"]:
            self.stage = "closed"

    # --- MOUNTAIN CLIMBERS ---
    def _track_mountain_climbers(self, l_hip: float, r_hip: float, back_angle: float):
        # Alternating knee drives in plank position
        # One hip angle becomes small (flexion, knee driven forward)
        active_hip = min(l_hip, r_hip)
        
        if not self.rep_started and l_hip > 130 and r_hip > 130:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        if self.stage == "up": # Standing / starting position
            if active_hip < 90:
                self.stage = "down" # Driven knee forward
                self.feedback = "Drive the other leg!"
                if back_angle < 140:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Keep hips down")
                    
        elif self.stage == "down":
            if l_hip > 125 and r_hip > 125:
                self.stage = "up"
                self.rep_count += 1
                
                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)
                
                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Great drive!"
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    self.form_scores.append(70)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"
                self.rep_started = False

    # --- BURPEES ---
    def _track_burpees(self, elbow_angle: float, knee_angle: float, back_angle: float, l_sh, l_ank):
        # State transitions: "standing" -> "squatting" -> "plank" -> "pushup_down" -> "jump"
        # 1. Standing: knee straight >160°, vertical alignment
        # 2. Squatting: knee bent < 100°
        # 3. Plank/Pushup: body horizontal (shoulder-ankle y-diff is small), elbow straight
        # 4. Pushup down: elbow bent < 95°
        # 5. Jump: feet off floor, hands raised
        
        # Simplify to a robust state tracking:
        if self.burpee_state == "standing":
            if knee_angle < 110:
                self.burpee_state = "squatting"
                self.feedback = "Drop to plank!"
        
        elif self.burpee_state == "squatting":
            # If body layout becomes horizontal (shoulder Y close to ankle Y)
            y_diff = abs(l_sh[1] - l_ank[1])
            if y_diff < 0.3:
                self.burpee_state = "plank"
                self.feedback = "Do a pushup!"
            elif knee_angle > 150: # Stood up prematurely
                self.burpee_state = "standing"
                
        elif self.burpee_state == "plank":
            if elbow_angle < 100:
                self.burpee_state = "pushup_down"
                self.feedback = "Push up and jump!"
            # Skip pushup if they just jump
            elif l_sh[1] < l_ank[1] * 0.6 and y_diff > 0.4:
                self.burpee_state = "jump"
                
        elif self.burpee_state == "pushup_down":
            if elbow_angle > 140:
                self.burpee_state = "jump"
                self.feedback = "Up and jump!"
                
        elif self.burpee_state == "jump":
            # Jump transition back to standing
            if knee_angle > 155:
                self.rep_count += 1
                self.valid_reps += 1
                self.streak += 1
                self.best_streak = max(self.best_streak, self.streak)
                self.form_scores.append(100)
                self.feedback = "✔ Burpee Complete!"
                self.burpee_state = "standing"

    # --- SITUPS TRACKING ---
    def _track_situps(self, hip_angle: float, knee_angle: float):
        # Lie down: hip_angle > 140°
        if not self.rep_started and hip_angle > 135:
            self.rep_started = True
            self.rep_start_time = time.time()
            self.current_rep_valid = True
            self.current_rep_errors = []

        if self.stage == "up": # Lie down state
            if hip_angle > 135:
                self.stage = "down" # lying down
                self.feedback = "Sit up!"
                
        elif self.stage == "down": # Sitting up state
            if hip_angle < 75:
                self.stage = "up"
                self.rep_count += 1
                
                # Check knees: knees should remain bent (around 90° - 120°)
                if knee_angle > 135:
                    self.current_rep_valid = False
                    self.current_rep_errors.append("Keep knees bent")
                
                rep_duration = time.time() - self.rep_start_time
                self.rep_durations.append(rep_duration)
                self.average_speed = np.mean(self.rep_durations)

                if self.current_rep_valid:
                    self.valid_reps += 1
                    self.streak += 1
                    self.best_streak = max(self.best_streak, self.streak)
                    self.form_scores.append(100)
                    self.feedback = "✔ Good Sit-up!"
                else:
                    self.invalid_reps += 1
                    self.streak = 0
                    self.form_scores.append(70)
                    self.feedback = f"❌ {', '.join(self.current_rep_errors)}"
                self.rep_started = False
