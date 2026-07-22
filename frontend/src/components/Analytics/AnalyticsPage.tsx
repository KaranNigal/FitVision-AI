import React, { useEffect, useState } from 'react';
import { workoutsApi } from '../../services/api';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, 
  LineChart, Line, AreaChart, Area, Legend
} from 'recharts';
import { Flame, Target, Dumbbell, Activity } from 'lucide-react';
const Fire = Flame;

export const AnalyticsPage: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedChart, setSelectedChart] = useState<'volume' | 'calories' | 'speed'>('volume');

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const data = await workoutsApi.getHistory();
        setHistory(data);
      } catch (err) {
        console.error("Failed to load workout history:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#030712]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-accent"></div>
      </div>
    );
  }

  // Aggregate stats
  const totalWorkouts = history.length;
  const totalReps = history.reduce((sum, w) => sum + (w.exercises?.[0]?.total_reps || 0), 0);
  const avgScore = totalWorkouts > 0 
    ? Math.round(history.reduce((sum, w) => sum + w.score, 0) / totalWorkouts) 
    : 0;
  const totalKcal = Math.round(history.reduce((sum, w) => sum + w.calories_burned, 0));

  // Transform data for charts (Chronological order)
  const chartData = [...history].reverse().map(w => ({
    date: new Date(w.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    reps: w.exercises?.[0]?.valid_reps || 0,
    calories: Math.round(w.calories_burned),
    speed: w.exercises?.[0]?.average_speed_seconds || 0,
    score: w.score
  }));

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-gradient-mesh min-h-screen text-slate-100 pb-16">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white">Fitness Analytics</h1>
        <p className="text-slate-400 mt-1">Review historical trends, volume metrics, and movement speeds.</p>
      </div>

      {/* Aggregate Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="glass-card p-5 rounded-2xl flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
            <Dumbbell className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Sessions Logs</span>
            <h4 className="text-xl font-black text-white mt-0.5">{totalWorkouts} Workouts</h4>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Volume Done</span>
            <h4 className="text-xl font-black text-white mt-0.5">{totalReps} Total Reps</h4>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
            <Target className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Average Accuracy</span>
            <h4 className="text-xl font-black text-white mt-0.5">{avgScore}% Score</h4>
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl flex items-center gap-4">
          <div className="h-10 w-10 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <Fire className="h-5 w-5" />
          </div>
          <div>
            <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Energy Burned</span>
            <h4 className="text-xl font-black text-white mt-0.5">{totalKcal} kcal</h4>
          </div>
        </div>
      </div>

      {/* Main Charts Filter and Container */}
      <div className="glass-card p-6 rounded-2xl space-y-6">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
          <div>
            <h3 className="text-lg font-bold text-white">Historical Progress</h3>
            <p className="text-xs text-slate-400">Visualize form ratings, reps, or speed over time.</p>
          </div>
          
          <div className="flex gap-1.5 p-1 bg-slate-900 border border-slate-800 rounded-xl">
            <button
              onClick={() => setSelectedChart('volume')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedChart === 'volume' ? 'bg-brand-accent text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Reps Volume
            </button>
            <button
              onClick={() => setSelectedChart('calories')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedChart === 'calories' ? 'bg-brand-accent text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Calories Burn
            </button>
            <button
              onClick={() => setSelectedChart('speed')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
                selectedChart === 'speed' ? 'bg-brand-accent text-white shadow' : 'text-slate-400 hover:text-white'
              }`}
            >
              Speed & Quality
            </button>
          </div>
        </div>

        <div className="h-80 w-full">
          {totalWorkouts > 0 ? (
            <ResponsiveContainer width="100%" height="100%">
              {selectedChart === 'volume' ? (
                <BarChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937' }} />
                  <Bar dataKey="reps" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                </BarChart>
              ) : selectedChart === 'calories' ? (
                <AreaChart data={chartData}>
                  <defs>
                    <linearGradient id="colorCalories2" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#ec4899" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#ec4899" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                  <YAxis stroke="#64748b" fontSize={11} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937' }} />
                  <Area type="monotone" dataKey="calories" stroke="#ec4899" fillOpacity={1} fill="url(#colorCalories2)" />
                </AreaChart>
              ) : (
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={11} />
                  <YAxis yAxisId="left" stroke="#64748b" fontSize={11} axisLine={false} />
                  <YAxis yAxisId="right" orientation="right" stroke="#64748b" fontSize={11} axisLine={false} />
                  <Tooltip contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937' }} />
                  <Legend />
                  <Line yAxisId="left" type="monotone" dataKey="speed" name="Speed (sec/rep)" stroke="#06b6d4" strokeWidth={2} activeDot={{ r: 8 }} />
                  <Line yAxisId="right" type="monotone" dataKey="score" name="Form Score (%)" stroke="#10b981" strokeWidth={2} />
                </LineChart>
              )}
            </ResponsiveContainer>
          ) : (
            <div className="flex items-center justify-center h-full text-slate-500 text-sm">
              Log workouts to populate charts.
            </div>
          )}
        </div>
      </div>

      {/* Workout Logs Spreadsheet */}
      <div className="glass-card rounded-2xl overflow-hidden">
        <div className="p-6 border-b border-slate-800">
          <h3 className="text-lg font-bold text-white">Workout Logs</h3>
          <p className="text-xs text-slate-400">Complete raw history profile sheet of all exercises logged.</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-900 border-b border-slate-800 text-slate-400 text-xs font-bold uppercase tracking-wider">
                <th className="p-4 pl-6">Date</th>
                <th className="p-4">Exercise Name</th>
                <th className="p-4">Variation</th>
                <th className="p-4">Duration</th>
                <th className="p-4 text-center">Reps (Valid / Total)</th>
                <th className="p-4 text-center">Form Score</th>
                <th className="p-4 text-right pr-6">Calories</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 text-sm text-slate-300">
              {history.length > 0 ? (
                history.map((w) => {
                  const ex = w.exercises?.[0];
                  return (
                    <tr key={w.id} className="hover:bg-slate-900/30">
                      <td className="p-4 pl-6 font-medium text-slate-400">
                        {new Date(w.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </td>
                      <td className="p-4 font-bold text-white">{ex?.exercise_name || 'General'}</td>
                      <td className="p-4"><span className="bg-slate-800 text-slate-400 text-xs font-semibold px-2 py-1 rounded">{ex?.variation || 'N/A'}</span></td>
                      <td className="p-4">{Math.round(w.duration_seconds / 60)} Mins</td>
                      <td className="p-4 text-center font-bold">
                        <span className="text-white">{ex?.valid_reps || 0}</span>
                        <span className="text-slate-500 font-normal"> / {ex?.total_reps || 0}</span>
                      </td>
                      <td className="p-4 text-center">
                        <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${
                          w.score >= 90 ? 'bg-emerald-500/10 text-emerald-400' :
                          w.score >= 70 ? 'bg-amber-500/10 text-amber-400' : 'bg-red-500/10 text-red-400'
                        }`}>
                          {w.score}%
                        </span>
                      </td>
                      <td className="p-4 text-right pr-6 font-extrabold text-white">{Math.round(w.calories_burned)} kcal</td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan={7} className="p-8 text-center text-slate-500 text-sm">
                    No workout sessions logged yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
