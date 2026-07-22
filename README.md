# ⚡ FitVision AI ⚡

<p align="center">
  <b>Biometrics Tracking & Fitness Analytics SaaS Platform</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB" alt="React" />
  <img src="https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/TypeScript-007ACC?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white" alt="TailwindCSS" />
  <img src="https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker" />
</p>

---

FitVision AI is a production-ready, enterprise-grade AI fitness monitoring SaaS platform. It leverages browser-based MediaPipe body landmark tracking to stream biomechanics telemetry over WebSockets to a Python FastAPI backend. The backend executes state machine tracking rules to detect exercises (specifically pushups and all their 9 variations), count repetitions, evaluate postures, and stream real-time coaching feedback.

---

## 📸 Project Showcase

Below are the interface previews showing the athlete dashboard, real-time biomechanics tracking, performance analytics, and account configuration.

<table align="center">
  <tr>
    <td align="center" width="50%">
      <b>🔒 Secure Authentication & Onboarding</b><br />
      <img src="images/1.png" alt="Login & Sign Up Pages" width="100%" />
    </td>
    <td align="center" width="50%">
      <b>📊 Athlete Dashboard & Progress Hub</b><br />
      <img src="images/2.png" alt="Main Dashboard Dashboard" width="100%" />
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>⚙️ Exercise Configuration & Settings</b><br />
      <img src="images/3.png" alt="Settings Page" width="100%" />
    </td>
    <td align="center" width="50%">
      <b>🏆 Gamified Community Leaderboard</b><br />
      <img src="images/4.png" alt="Leaderboard" width="100%" />
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <b>🎥 Real-Time Camera Pose Estimation</b><br />
      <img src="images/5.png" alt="MediaPipe Tracking" width="100%" />
    </td>
    <td align="center" width="50%">
      <b>📈 Interactive Analytics & Biometric Charts</b><br />
      <img src="images/6.png" alt="Analytics Graphs" width="100%" />
    </td>
  </tr>
  <tr>
    <td align="center" colspan="2">
      <b>📄 PDF & CSV Performance Report Generation</b><br />
      <img src="images/7.png" alt="Report Generation" width="100%" />
    </td>
  </tr>
</table>

---

## 🛠 Tech Stack

*   **Frontend**: React (Vite) + TypeScript + TailwindCSS + Recharts
*   **Backend**: FastAPI (Python 3.10) + SQLAlchemy + WebSockets + Uvicorn
*   **AI Engine**: MediaPipe Pose (Web SDK coordinate extraction) + Headless OpenCV
*   **Database**: PostgreSQL (Dockerized)
*   **Reporting**: ReportLab (PDF) + Pandas (Excel / CSV sheets exports)
*   **Deployment**: Docker + Docker Compose + GitHub Actions CI/CD pipeline

---

## 🏗 System Architecture Flow

```mermaid
sequenceDiagram
    autonumber
    actor Athlete as Athlete (Webcam)
    participant Client as React Client (MediaPipe)
    participant Server as FastAPI WebSocket Server
    participant DB as PostgreSQL DB
    
    Athlete->>Client: Capture Video Frames
    Client->>Client: Extract 33 Body Coordinates
    Client->>Server: Stream Coordinates (JSON WebSocket at 30 FPS)
    Server->>Server: Calculate Biometric Joint Angles
    Server->>Server: Run Exercise State Machines
    Server->>Client: Return Real-Time Coach Cues (rep increment, correction prompts)
    Client->>Athlete: TTS Voice Coaching & Hud Render
    Athlete->>Client: Press End Session
    Client->>Server: Post Workout Stats (reps count, score, duration)
    Server->>DB: Save Session Logs & Recalculate XP Streaks
    Server->>Client: Confetti Pop & Reward XP Upgrades
```

---

## 📊 Database Schema & ER Model

```mermaid
erDiagram
    USERS {
        int id PK
        string email "UK"
        string hashed_password
        string full_name
        string profile_pic_url
        int streak_count
        date last_workout_date
        int total_xp
        int level
        datetime created_at
    }
    WORKOUTS {
        int id PK
        int user_id FK
        int duration_seconds
        float calories_burned
        int score
        string difficulty
        string notes
        string video_url
        datetime date
    }
    WORKOUT_EXERCISES {
        int id PK
        int workout_id FK
        string exercise_name
        string variation
        int total_reps
        int valid_reps
        int invalid_reps
        float average_speed_seconds
        int best_streak
    }
    ACHIEVEMENTS {
        int id PK
        string code "UK"
        string title
        string description
        int xp_reward
        string badge_icon
    }
    USER_ACHIEVEMENTS {
        int id PK
        int user_id FK
        int achievement_id FK
        datetime unlocked_at
    }
    LEADERBOARD {
        int id PK
        int user_id FK "UK"
        int total_xp
        int level
        datetime updated_at
    }
    
    USERS ||--o{ WORKOUTS : logs
    USERS ||--o{ USER_ACHIEVEMENTS : unlocks
    USERS ||--|| LEADERBOARD : ranks
    WORKOUTS ||--o{ WORKOUT_EXERCISES : contains
    ACHIEVEMENTS ||--o{ USER_ACHIEVEMENTS : unlocked_by
```

---

## ⚡ Real-Time Tracking State Rules (Biometrics Engine)

Our AI rules engine in `ai_service.py` evaluates joint angles to track repetitions:
*   **Push-ups**: Monitors left/right elbow angle (Shoulder-Elbow-Wrist). Rep begins when angles drop from >150° to <90° (down stage), and increments when returning to >145° (up stage).
    *   *Diamond Push-ups*: Wrists horizontal distance is < 40% of shoulder width.
    *   *Wide Push-ups*: Wrists horizontal distance is > 140% of shoulder width.
    *   *Pike Push-ups*: Hips angle is bent (< 120°) throughout the movement.
*   **Squats**: Evaluates knee angle (Hip-Knee-Ankle). Rep triggers down when knee drops < 100°, and completes when knees straighten > 160°.
*   **Plank**: Validates static hold straightness (Shoulder-Hip-Ankle angle > 155°). Counts hold time in seconds.

---

## 🚀 Installation & Local Running

### Running with Docker Compose (Recommended)

1.  Clone the repository and locate the root workspace folder:
    ```bash
    cd FitVisionAI
    ```
2.  Duplicate `.env.example` as `.env` and fill values:
    *   **On Windows (cmd/PowerShell):**
        ```powershell
        copy .env.example .env
        ```
    *   **On macOS/Linux:**
        ```bash
        cp .env.example .env
        ```
3.  Launch the Docker containers:
    ```bash
    docker-compose up --build
    ```
4.  Open the web browser:
    *   **Frontend Client**: [http://localhost:5173](http://localhost:5173)
    *   **Backend OpenAPI Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

### Running Locally (Without Docker)

#### 1. Setup Database
Ensure you have a PostgreSQL server running locally, create a database named `fitvision`, and update the `DATABASE_URL` in your `.env` file.

#### 2. Run Backend
1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Initialize virtual environment and install requirements:
    ```bash
    python -m venv venv
    
    # On Windows:
    .\venv\Scripts\activate
    
    # On macOS/Linux:
    source venv/bin/activate
    
    pip install -r requirements.txt
    ```
3.  Launch the FastAPI server:
    ```bash
    uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
    ```

#### 3. Run Frontend
1.  Navigate to the frontend directory:
    ```bash
    cd ../frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Launch Vite:
    ```bash
    npm run dev
    ```

---

## 🧪 Testing

We use Pytest to run isolated API and unit tests mock-loading SQLite in memory.
1.  Enter backend directory:
    ```bash
    cd backend
    ```
2.  Run Pytest suite:
    ```bash
    pytest
    ```

