import React, { useEffect, useState } from 'react';
import { workoutsApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { 
  Flame, Trophy, Clock, Target, Award, Download, ArrowRight, Activity, Plus, Dumbbell
} from 'lucide-react';

const Fire = Flame;
import { Link } from 'react-router-dom';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

export const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const statsData = await workoutsApi.getStats();
        setStats(statsData);
        
        const achData = await workoutsApi.getAchievements();
        setAchievements(achData.filter((a: any) => a.unlocked).slice(0, 3));
      } catch (err) {
        console.error("Failed to load dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExport = async (format: 'csv' | 'excel' | 'pdf') => {
    try {
      setExporting(format);
      const data = await workoutsApi.exportReport(format);
      const blob = new Blob([data], { 
        type: format === 'pdf' ? 'application/pdf' : 
              format === 'excel' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'text/csv' 
      });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `fitvision_report_${new Date().toISOString().slice(0, 10)}.${format === 'excel' ? 'xlsx' : format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error(`Export to ${format} failed:`, err);
    } finally {
      setExporting(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#030712]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-accent"></div>
      </div>
    );
  }

  // Fallback if stats are empty
  const hasWorkouts = stats && stats.total_workouts > 0;
  
  const chartColors = ['#8b5cf6', '#ec4899', '#06b6d4', '#10b981', '#f59e0b', '#3b82f6'];

  // Formulate Pie Chart Data
  const pieData = stats?.exercise_distribution.map((item: any) => ({
    name: item.exercise_name,
    value: item.total_reps
  })) || [];

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-gradient-mesh min-h-screen text-slate-100 pb-16">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold text-white tracking-tight">Welcome Back, {user?.full_name}!</h1>
          <p className="text-slate-400 mt-1">Real-time biomechanics analysis and exercise monitoring dashboard.</p>
        </div>
        
        {/* Export Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting !== null}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-xl text-sm font-semibold border border-slate-700 transition-all duration-200"
          >
            <Download className="h-4 w-4" />
            {exporting === 'pdf' ? 'Exporting PDF...' : 'PDF'}
          </button>
          <button
            onClick={() => handleExport('excel')}
            disabled={exporting !== null}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-xl text-sm font-semibold border border-slate-700 transition-all duration-200"
          >
            <Download className="h-4 w-4" />
            {exporting === 'excel' ? 'Exporting Excel...' : 'Excel'}
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting !== null}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-xl text-sm font-semibold border border-slate-700 transition-all duration-200"
          >
            <Download className="h-4 w-4" />
            {exporting === 'csv' ? 'Exporting CSV...' : 'CSV'}
          </button>
          
          <Link
            to="/workout"
            className="flex items-center gap-2 bg-gradient-to-r from-brand-accent to-brand-secondary hover:opacity-90 text-white px-4 py-2 rounded-xl text-sm font-bold shadow-lg shadow-brand-accent/20 transition-all duration-200"
          >
            <Plus className="h-4 w-4" />
            New Workout
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Level Card */}
        <div className="glass-card p-6 rounded-2xl flex items-center gap-4 relative overflow-hidden">
          <div className="absolute right-0 bottom-0 translate-y-4 translate-x-4 opacity-5">
            <Trophy className="h-32 w-32" />
          </div>
          <div className="h-12 w-12 rounded-xl bg-violet-500/10 border border-violet-500/20 flex items-center justify-center text-violet-400">
            <Trophy className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Athlete Level</span>
            <h3 className="text-2xl font-black text-white mt-1">Level {stats?.level || 1}</h3>
            <span className="text-xs text-slate-400 font-medium">{stats?.total_xp || 0} XP accumulated</span>
          </div>
        </div>

        {/* Streak Card */}
        <div className="glass-card p-6 rounded-2xl flex items-center gap-4 relative overflow-hidden">
          <div className="absolute right-0 bottom-0 translate-y-4 translate-x-4 opacity-5">
            <Flame className="h-32 w-32" />
          </div>
          <div className="h-12 w-12 rounded-xl bg-orange-500/10 border border-orange-500/20 flex items-center justify-center text-orange-400">
            <Flame className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Workout Streak</span>
            <h3 className="text-2xl font-black text-white mt-1">{stats?.streak_count || 0} Days</h3>
            <span className="text-xs text-slate-400 font-medium">Keep moving tomorrow!</span>
          </div>
        </div>

        {/* Calories Card */}
        <div className="glass-card p-6 rounded-2xl flex items-center gap-4 relative overflow-hidden">
          <div className="absolute right-0 bottom-0 translate-y-4 translate-x-4 opacity-5">
            <Fire className="h-32 w-32" />
          </div>
          <div className="h-12 w-12 rounded-xl bg-rose-500/10 border border-rose-500/20 flex items-center justify-center text-rose-400">
            <Fire className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Calories Burned</span>
            <h3 className="text-2xl font-black text-white mt-1">{Math.round(stats?.total_calories_burned || 0)} kcal</h3>
            <span className="text-xs text-slate-400 font-medium">Calculated metabolic cost</span>
          </div>
        </div>

        {/* Active Time Card */}
        <div className="glass-card p-6 rounded-2xl flex items-center gap-4 relative overflow-hidden">
          <div className="absolute right-0 bottom-0 translate-y-4 translate-x-4 opacity-5">
            <Clock className="h-32 w-32" />
          </div>
          <div className="h-12 w-12 rounded-xl bg-cyan-500/10 border border-cyan-500/20 flex items-center justify-center text-cyan-400">
            <Clock className="h-6 w-6" />
          </div>
          <div>
            <span className="text-xs text-slate-500 font-bold uppercase tracking-wider">Active Duration</span>
            <h3 className="text-2xl font-black text-white mt-1">{Math.round(stats?.total_duration_minutes || 0)} Mins</h3>
            <span className="text-xs text-slate-400 font-medium">Total time logged</span>
          </div>
        </div>
      </div>

      {/* Main Charts & Analytics Block */}
      {hasWorkouts ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Daily Calories Trend Chart */}
          <div className="glass-card p-6 rounded-2xl lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h3 className="text-lg font-bold text-white">Daily Calories Burned</h3>
                <p className="text-xs text-slate-400">Tracking calorie expenditure over recent workouts.</p>
              </div>
              <Activity className="h-5 w-5 text-brand-accent" />
            </div>
            
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stats.calories_trend}>
                  <defs>
                    <linearGradient id="colorCalories" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" vertical={false} />
                  <XAxis dataKey="date" stroke="#64748b" fontSize={10} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} />
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937', color: '#f1f5f9' }}
                    labelStyle={{ color: '#94a3b8', fontSize: 11 }}
                  />
                  <Area type="monotone" dataKey="calories" stroke="#8b5cf6" strokeWidth={2} fillOpacity={1} fill="url(#colorCalories)" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Exercise Distribution Pie */}
          <div className="glass-card p-6 rounded-2xl flex flex-col justify-between">
            <div>
              <h3 className="text-lg font-bold text-white">Exercise Breakdown</h3>
              <p className="text-xs text-slate-400">Distribution of total repetitions performed.</p>
            </div>
            
            <div className="h-56 relative flex items-center justify-center">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {pieData.map((_entry: any, index: number) => (
                      <Cell key={`cell-${index}`} fill={chartColors[index % chartColors.length]} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ backgroundColor: '#111827', borderColor: '#1f2937', color: '#f1f5f9' }}
                    itemStyle={{ fontSize: 12 }}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            
            {/* Legend indicators */}
            <div className="grid grid-cols-2 gap-2 mt-4">
              {pieData.map((item: any, index: number) => (
                <div key={item.name} className="flex items-center gap-2">
                  <div className="h-2.5 w-2.5 rounded-full" style={{ backgroundColor: chartColors[index % chartColors.length] }} />
                  <span className="text-xs text-slate-400 truncate">{item.name} ({item.value})</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="glass-card p-12 rounded-2xl text-center space-y-6 flex flex-col items-center justify-center">
          <Dumbbell className="h-16 w-16 text-brand-accent animate-pulse" />
          <div>
            <h3 className="text-xl font-bold text-white">No workouts recorded yet</h3>
            <p className="text-slate-400 max-w-sm mt-1 mx-auto text-sm">Start your first exercise session in our live workout arena to view AI analytics, charts, streaks, and milestones!</p>
          </div>
          <Link
            to="/workout"
            className="flex items-center gap-2 bg-gradient-to-r from-brand-accent to-brand-secondary text-white px-6 py-3 rounded-xl font-bold hover:opacity-90 shadow-lg shadow-brand-accent/20 transition-all duration-200"
          >
            Go to Workout Area
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}

      {/* Lower Row: Recent Workouts & Achievements */}
      {hasWorkouts && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* History List */}
          <div className="glass-card p-6 rounded-2xl lg:col-span-2 space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-bold text-white">Recent Sessions</h3>
              <Link to="/analytics" className="text-xs text-brand-accent font-semibold flex items-center gap-1 hover:underline">
                View All History
                <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>

            <div className="divide-y divide-slate-800 space-y-4">
              {stats.recent_workouts.map((w: any) => (
                <div key={w.id} className="flex items-center justify-between pt-4 first:pt-0">
                  <div className="flex items-center gap-4">
                    <div className="h-10 w-10 rounded-xl bg-slate-800 flex items-center justify-center text-slate-400 font-bold">
                      {w.exercises[0]?.exercise_name.charAt(0) || 'W'}
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">
                        {w.exercises[0]?.exercise_name || 'General Workout'} 
                        {w.exercises[0]?.variation ? ` (${w.exercises[0].variation})` : ''}
                      </h4>
                      <p className="text-xs text-slate-500 mt-0.5">
                        {new Date(w.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })} | {Math.round(w.duration_seconds / 60)} Mins
                      </p>
                    </div>
                  </div>
                  
                  <div className="text-right">
                    <span className="text-sm font-black text-white">{w.exercises[0]?.valid_reps || 0} reps</span>
                    <div className="flex items-center gap-1.5 justify-end text-[10px] font-semibold text-emerald-400 mt-0.5">
                      <Target className="h-3 w-3" />
                      <span>{w.score}% Form Score</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Milestones / Achievements */}
          <div className="glass-card p-6 rounded-2xl space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white">Unlocked Milestones</h3>
              <p className="text-xs text-slate-400">Your gamified achievements and levels.</p>
            </div>

            <div className="space-y-4">
              {achievements.length > 0 ? (
                achievements.map((ach) => (
                  <div key={ach.id} className="flex items-center gap-3.5 p-3 rounded-xl bg-slate-900 border border-slate-800">
                    <div className="h-10 w-10 rounded-lg bg-yellow-500/10 border border-yellow-500/30 flex items-center justify-center text-yellow-400">
                      <Award className="h-5 w-5" />
                    </div>
                    <div>
                      <h4 className="text-sm font-bold text-white">{ach.title}</h4>
                      <p className="text-[11px] text-slate-500 mt-0.5">{ach.description}</p>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-6 text-slate-500 text-sm">
                  No achievements unlocked yet.
                </div>
              )}
            </div>
            
            <Link
              to="/leaderboard"
              className="flex items-center justify-center gap-2 w-full py-3 bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white rounded-xl text-xs font-bold transition-all duration-200"
            >
              <Trophy className="h-3.5 w-3.5 text-yellow-500" />
              View Global Leaderboard
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};
