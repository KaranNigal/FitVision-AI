import React, { useRef, useState, useEffect } from 'react';
import { workoutsApi, getWebSocketUrl } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  Play, Square, Volume2, VolumeX, Camera, Check, AlertTriangle, RefreshCw, Award, Flame
} from 'lucide-react';
import confetti from 'canvas-confetti';

// Declare MediaPipe globals from global index.html
declare global {
  interface Window {
    Pose: any;
    Camera: any;
  }
}

const SUPPORTED_EXERCISES = [
  {
    name: 'Pushups',
    variations: ['Standard', 'Diamond', 'Wide', 'Pike', 'Hindu', 'Archer', 'Incline', 'Decline'],
    caloriesPerRep: 0.4
  },
  { name: 'Squats', variations: ['Standard'], caloriesPerRep: 0.32 },
  { name: 'Lunges', variations: ['Standard'], caloriesPerRep: 0.28 },
  { name: 'Plank', variations: ['Standard'], caloriesPerRep: 0.15 }, // calories per second
  { name: 'Pullups', variations: ['Standard'], caloriesPerRep: 0.5 },
  { name: 'Jumping Jacks', variations: ['Standard'], caloriesPerRep: 0.15 },
  { name: 'Mountain Climbers', variations: ['Standard'], caloriesPerRep: 0.1 },
  { name: 'Burpees', variations: ['Standard'], caloriesPerRep: 0.8 },
  { name: 'Situps', variations: ['Standard'], caloriesPerRep: 0.2 },
];

export const WorkoutPage: React.FC = () => {
  const { checkAuth } = useAuth();
  
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const cameraRef = useRef<any>(null);
  const poseTrackerRef = useRef<any>(null);

  const [selectedExercise, setSelectedExercise] = useState(SUPPORTED_EXERCISES[0]);
  const [selectedVariation, setSelectedVariation] = useState('Standard');
  const [isActive, setIsActive] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // Real-time metrics from WebSocket
  const [metrics, setMetrics] = useState<any>({
    rep_count: 0,
    valid_reps: 0,
    invalid_reps: 0,
    streak: 0,
    feedback: 'Select an exercise and press Start.',
    current_stage: 'up',
    form_score: 100,
    average_speed: 0.0,
    plank_duration: 0.0
  });

  const lastFeedbackRef = useRef<string>('');
  const metricsRef = useRef<any>(metrics);

  useEffect(() => {
    metricsRef.current = metrics;
  }, [metrics]);

  // AI Voice Coach (Text to Speech)
  const speakFeedback = (text: string) => {
    if (isMuted || !text) return;
    
    // Clean prefix icons
    const cleanText = text.replace(/[✔❌]/g, '').trim();
    if (cleanText === lastFeedbackRef.current) return;
    
    lastFeedbackRef.current = cleanText;
    
    if ('speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(cleanText);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);
    }
  };

  // Draw landmarks and links on Canvas
  const drawSkeleton = (ctx: CanvasRenderingContext2D, landmarks: any[]) => {
    const width = canvasRef.current?.width || 640;
    const height = canvasRef.current?.height || 480;
    
    ctx.clearRect(0, 0, width, height);

    // Render joint points
    landmarks.forEach((pt: any) => {
      if (pt.visibility && pt.visibility < 0.5) return;
      ctx.beginPath();
      ctx.arc(pt.x * width, pt.y * height, 5, 0, 2 * Math.PI);
      ctx.fillStyle = '#06b6d4'; // neon cyan
      ctx.fill();
    });

    // Bone links helper
    const drawBone = (idx1: number, idx2: number) => {
      const p1 = landmarks[idx1];
      const p2 = landmarks[idx2];
      if (!p1 || !p2 || (p1.visibility && p1.visibility < 0.5) || (p2.visibility && p2.visibility < 0.5)) return;

      ctx.beginPath();
      ctx.moveTo(p1.x * width, p1.y * height);
      ctx.lineTo(p2.x * width, p2.y * height);
      ctx.strokeStyle = '#8b5cf6'; // neon purple
      ctx.lineWidth = 3;
      ctx.stroke();
    };

    // Draw Skeletal outlines
    // Torso/Shoulders
    drawBone(11, 12);
    drawBone(11, 23);
    drawBone(12, 24);
    drawBone(23, 24);
    // Arms
    drawBone(11, 13);
    drawBone(13, 15);
    drawBone(12, 14);
    drawBone(14, 16);
    // Legs
    drawBone(23, 25);
    drawBone(25, 27);
    drawBone(24, 26);
    drawBone(26, 28);
  };

  // Start Workout Loop
  const startSession = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    setCameraError(null);

    // Initialize WebSocket connection
    const wsUrl = getWebSocketUrl(selectedExercise.name, selectedVariation);
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WS Connection established');
      setIsActive(true);
      setMetrics({
        rep_count: 0,
        valid_reps: 0,
        invalid_reps: 0,
        streak: 0,
        feedback: 'Ready! Position yourself in front of the camera.',
        current_stage: 'up',
        form_score: 100,
        average_speed: 0.0,
        plank_duration: 0.0
      });
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.error) {
        console.error(data.error);
        return;
      }
      setMetrics(data);
      speakFeedback(data.feedback);
    };

    ws.onerror = (err) => {
      console.error('WebSocket Error:', err);
    };

    ws.onclose = () => {
      console.log('WS Closed');
    };

    // Setup client-side MediaPipe Pose
    if (!window.Pose) {
      setCameraError('MediaPipe Pose failed to initialize. Please check your network connection.');
      ws.close();
      return;
    }

    const pose = new window.Pose({
      locateFile: (file: string) => `https://cdn.jsdelivr.net/npm/@mediapipe/pose/${file}`
    });

    pose.setOptions({
      modelComplexity: 1,
      smoothLandmarks: true,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5
    });

    pose.onResults((results: any) => {
      if (!canvasRef.current || !isActive) return;
      const ctx = canvasRef.current.getContext('2d');
      if (!ctx) return;

      if (results.poseLandmarks) {
        // Draw Skeleton overlay
        drawSkeleton(ctx, results.poseLandmarks);

        // Stream coordinates array over WebSocket
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ landmarks: results.poseLandmarks }));
        }
      }
    });

    poseTrackerRef.current = pose;

    // Hook up browser Webcam
    try {
      const camera = new window.Camera(videoRef.current, {
        onFrame: async () => {
          if (videoRef.current && isActive) {
            await pose.send({ image: videoRef.current });
          }
        },
        width: 640,
        height: 480
      });
      camera.start();
      cameraRef.current = camera;
    } catch (err: any) {
      setCameraError('Camera access denied. Please allow camera permissions and try again.');
      ws.close();
    }
  };

  // Stop / Finish Workout Loop
  const stopSession = async () => {
    setIsActive(false);

    // Stop MediaPipe Camera and trackers
    if (cameraRef.current) {
      cameraRef.current.stop();
    }
    if (poseTrackerRef.current) {
      poseTrackerRef.current.close();
    }

    // Close WebSocket
    if (wsRef.current) {
      wsRef.current.close();
    }

    // Clear Canvas
    if (canvasRef.current) {
      const ctx = canvasRef.current.getContext('2d');
      ctx?.clearRect(0, 0, canvasRef.current.width, canvasRef.current.height);
    }

    const currentMetrics = metricsRef.current;
    
    // Save workout results if any rep / hold occurred
    const totalUnits = selectedExercise.name.toLowerCase() === 'plank' 
      ? currentMetrics.plank_duration 
      : currentMetrics.rep_count;

    if (totalUnits > 0) {
      try {
        // Calculate dynamic MET calories
        const workoutDuration = selectedExercise.name.toLowerCase() === 'plank' 
          ? currentMetrics.plank_duration 
          : currentMetrics.rep_count * 3.0; // Estimate 3 seconds per rep

        const calories = selectedExercise.name.toLowerCase() === 'plank'
          ? currentMetrics.plank_duration * selectedExercise.caloriesPerRep
          : currentMetrics.valid_reps * selectedExercise.caloriesPerRep;

        // Post workout logs to DB
        await workoutsApi.create({
          duration_seconds: Math.round(workoutDuration) || 5,
          calories_burned: round(calories, 1),
          score: currentMetrics.average_score || 90,
          difficulty: selectedExercise.name.toLowerCase() === 'burpees' ? 'Hard' : 
                      selectedExercise.name.toLowerCase() === 'plank' ? 'Easy' : 'Medium',
          notes: `Completed ${selectedExercise.name} (${selectedVariation}) session.`,
          exercises: [{
            exercise_name: selectedExercise.name,
            variation: selectedVariation,
            total_reps: currentMetrics.rep_count,
            valid_reps: currentMetrics.valid_reps,
            invalid_reps: currentMetrics.invalid_reps,
            average_speed_seconds: currentMetrics.average_speed || 2.5,
            best_streak: currentMetrics.streak
          }]
        });

        // Trigger Congrats Confetti if form is clean
        if (currentMetrics.valid_reps > 0 || currentMetrics.plank_duration > 10) {
          confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
          });
        }
        
        // Refresh User profile stats
        checkAuth();
      } catch (err) {
        console.error('Failed to log workout session details:', err);
      }
    }
  };

  const handleExerciseChange = (name: string) => {
    const exObj = SUPPORTED_EXERCISES.find(e => e.name === name) || SUPPORTED_EXERCISES[0];
    setSelectedExercise(exObj);
    setSelectedVariation(exObj.variations[0]);
  };

  const round = (num: number, decimal: number) => {
    const factor = Math.pow(10, decimal);
    return Math.round(num * factor) / factor;
  };

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-gradient-mesh min-h-screen text-slate-100 pb-16">
      {/* Header title */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
            <Camera className="h-7 w-7 text-brand-accent animate-pulse" />
            AI Workout Arena
          </h1>
          <p className="text-slate-400 mt-1">Configure options, toggle your camera, and perform movements to track metrics in real time.</p>
        </div>
        
        {/* Voice Toggle */}
        <button
          onClick={() => setIsMuted(!isMuted)}
          className={`flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all duration-200 ${
            isMuted 
              ? 'bg-red-500/10 border-red-500/20 text-red-400' 
              : 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400'
          }`}
        >
          {isMuted ? <VolumeX className="h-4 w-4" /> : <Volume2 className="h-4 w-4" />}
          <span>{isMuted ? 'Voice Coach Muted' : 'Voice Coach Active'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Left webcam and visual area */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="relative aspect-video rounded-2xl overflow-hidden bg-slate-950 border border-slate-800 shadow-2xl flex items-center justify-center">
            {/* Real webcam device video output (hidden coordinates map) */}
            <video 
              ref={videoRef}
              className="absolute inset-0 w-full h-full object-cover hidden"
              playsInline
              muted
            />
            {/* Visual canvas overlays */}
            <canvas 
              ref={canvasRef}
              width={640}
              height={480}
              className="absolute inset-0 w-full h-full object-cover z-10 transform scale-x-[-1]"
            />

            {!isActive && (
              <div className="z-20 text-center space-y-4 max-w-sm px-6">
                <div className="h-16 w-16 bg-brand-accent/10 border border-brand-accent/20 rounded-2xl flex items-center justify-center mx-auto text-brand-accent">
                  <Play className="h-8 w-8 fill-brand-accent/10" />
                </div>
                <h3 className="text-lg font-bold text-white">Interactive Tracking Off</h3>
                <p className="text-slate-400 text-xs leading-relaxed">
                  Select your exercise, align your body within the camera frame, and press Start.
                </p>
              </div>
            )}
            
            {cameraError && (
              <div className="z-20 absolute inset-0 bg-slate-950/90 flex flex-col items-center justify-center p-6 text-center space-y-4">
                <AlertTriangle className="h-12 w-12 text-red-500" />
                <h3 className="text-lg font-bold text-white">Camera Config Error</h3>
                <p className="text-slate-400 text-xs max-w-xs">{cameraError}</p>
                <button
                  onClick={startSession}
                  className="bg-slate-800 text-white border border-slate-700 px-4 py-2 rounded-xl text-xs font-bold flex items-center gap-1.5"
                >
                  <RefreshCw className="h-3.5 w-3.5" />
                  Try Again
                </button>
              </div>
            )}
          </div>

          {/* Configuration Panels */}
          <div className="glass-card p-6 rounded-2xl grid grid-cols-1 md:grid-cols-2 gap-6">
            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">Exercise Select</label>
              <select
                disabled={isActive}
                value={selectedExercise.name}
                onChange={(e) => handleExerciseChange(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-accent transition-all"
              >
                {SUPPORTED_EXERCISES.map(ex => (
                  <option key={ex.name} value={ex.name}>{ex.name}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="text-xs font-bold text-slate-500 uppercase tracking-wider block mb-2">Variation Select</label>
              <select
                disabled={isActive || selectedExercise.variations.length <= 1}
                value={selectedVariation}
                onChange={(e) => setSelectedVariation(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-accent transition-all"
              >
                {selectedExercise.variations.map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>

            <div className="md:col-span-2">
              {!isActive ? (
                <button
                  onClick={startSession}
                  className="w-full py-4 bg-gradient-to-r from-brand-accent to-brand-secondary hover:opacity-90 font-bold text-white rounded-xl shadow-lg shadow-brand-accent/20 flex items-center justify-center gap-2 transition-all"
                >
                  <Play className="h-5 w-5 fill-white/10" />
                  Start Workout Tracker
                </button>
              ) : (
                <button
                  onClick={stopSession}
                  className="w-full py-4 bg-red-600 hover:bg-red-500 font-bold text-white rounded-xl flex items-center justify-center gap-2 transition-all"
                >
                  <Square className="h-5 w-5 fill-white/10" />
                  Finish Workout Session
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Right dashboard HUD metrics */}
        <div className="lg:col-span-4 space-y-6">
          {/* Main Rep Counter / Timer HUD */}
          <div className="glass-card p-6 rounded-2xl text-center space-y-6 relative overflow-hidden border border-brand-accent/10">
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Performance Activity</span>
            
            {selectedExercise.name.toLowerCase() === 'plank' ? (
              <div>
                <h2 className="text-6xl font-black text-white">{Math.round(metrics.plank_duration)}s</h2>
                <p className="text-xs text-slate-400 mt-2 font-medium">Accumulated Hold Time</p>
              </div>
            ) : (
              <div className="flex justify-around items-center">
                <div>
                  <h2 className="text-6xl font-black text-white">{metrics.valid_reps}</h2>
                  <p className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-0.5 justify-center mt-1">
                    <Check className="h-3.5 w-3.5" />
                    Valid Reps
                  </p>
                </div>
                <div className="h-12 w-[1px] bg-slate-800" />
                <div>
                  <h2 className="text-6xl font-black text-slate-500">{metrics.invalid_reps}</h2>
                  <p className="text-[10px] text-rose-500 font-bold uppercase tracking-wider flex items-center gap-0.5 justify-center mt-1">
                    <AlertTriangle className="h-3.5 w-3.5" />
                    Failed Reps
                  </p>
                </div>
              </div>
            )}

            {/* Streak metrics */}
            <div className="flex items-center gap-1.5 justify-center py-2 bg-slate-900/60 rounded-xl max-w-[160px] mx-auto text-xs font-semibold text-amber-500">
              <Flame className="h-4 w-4 fill-amber-500/10" />
              <span>Streak: {metrics.streak} reps</span>
            </div>
          </div>

          {/* Real-time coaching prompts */}
          <div className="glass-card p-6 rounded-2xl space-y-4">
            <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider">Live Coaching prompts</h4>
            <div className="p-4 bg-slate-900 border border-slate-800 rounded-xl flex items-start gap-3">
              <div className={`h-6 w-6 rounded-md flex items-center justify-center text-xs shrink-0 mt-0.5 ${
                metrics.feedback.includes('❌') 
                  ? 'bg-rose-500/10 text-rose-400' 
                  : metrics.feedback.includes('✔') 
                  ? 'bg-emerald-500/10 text-emerald-400' 
                  : 'bg-violet-500/10 text-violet-400'
              }`}>
                {metrics.feedback.includes('❌') ? <AlertTriangle className="h-4 w-4" /> : <Award className="h-4 w-4" />}
              </div>
              <p className="text-sm font-semibold leading-relaxed text-slate-200">
                {metrics.feedback}
              </p>
            </div>
          </div>

          {/* Accuracy & Speed Biometrics HUD */}
          <div className="glass-card p-6 rounded-2xl grid grid-cols-2 gap-4">
            <div className="bg-slate-950/40 p-4 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Form Accuracy</span>
              <h4 className="text-xl font-black text-white mt-1">{metrics.form_score}%</h4>
            </div>
            <div className="bg-slate-950/40 p-4 rounded-xl text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider">Rep Speed</span>
              <h4 className="text-xl font-black text-white mt-1">{round(metrics.average_speed, 1)}s</h4>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
