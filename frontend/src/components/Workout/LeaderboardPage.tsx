import React, { useEffect, useState } from 'react';
import { workoutsApi } from '../../services/api';
import { useAuth } from '../../context/AuthContext';
import { Trophy, Award, Zap, ShieldCheck, Flame, User } from 'lucide-react';

export const LeaderboardPage: React.FC = () => {
  const { user } = useAuth();
  const [leaderboard, setLeaderboard] = useState<any[]>([]);
  const [achievements, setAchievements] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const lbData = await workoutsApi.getLeaderboard();
        setLeaderboard(lbData);
        
        const achData = await workoutsApi.getAchievements();
        setAchievements(achData);
      } catch (err) {
        console.error("Failed to load gamification data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const getBadgeIcon = (name: string) => {
    switch (name) {
      case 'Award': return <Award className="h-6 w-6" />;
      case 'Zap': return <Zap className="h-6 w-6" />;
      case 'Flame': return <Flame className="h-6 w-6" />;
      case 'ShieldCheck': return <ShieldCheck className="h-6 w-6" />;
      default: return <Award className="h-6 w-6" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen bg-[#030712]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-brand-accent"></div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-7xl mx-auto space-y-8 bg-gradient-mesh min-h-screen text-slate-100 pb-16">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          <Trophy className="h-8 w-8 text-yellow-500 fill-yellow-500/10" />
          Gamification & Standings
        </h1>
        <p className="text-slate-400 mt-1">Unlock badges, accumulate XP, and rank against the global fitness board.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        {/* Leaderboard Section */}
        <div className="lg:col-span-7 glass-card rounded-2xl overflow-hidden">
          <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/40">
            <h3 className="text-lg font-bold text-white">Global Leaderboard</h3>
            <span className="text-xs text-brand-accent font-semibold uppercase tracking-wider">Top Athletes</span>
          </div>

          <div className="divide-y divide-slate-800">
            {leaderboard.length > 0 ? (
              leaderboard.map((item) => {
                const isCurrentUser = item.user_id === user?.id;
                return (
                  <div 
                    key={item.id} 
                    className={`flex items-center justify-between p-5 transition-all duration-150 ${
                      isCurrentUser ? 'bg-brand-accent/10 border-l-4 border-brand-accent' : 'hover:bg-slate-900/30'
                    }`}
                  >
                    <div className="flex items-center gap-4">
                      {/* Rank Indicator */}
                      <span className={`w-6 text-center font-black text-sm ${
                        item.rank === 1 ? 'text-yellow-400 text-lg' :
                        item.rank === 2 ? 'text-slate-300' :
                        item.rank === 3 ? 'text-amber-600' : 'text-slate-500'
                      }`}>
                        #{item.rank}
                      </span>
                      
                      {/* Athlete Details */}
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-slate-800 flex items-center justify-center text-slate-300 text-xs font-bold uppercase">
                          {item.full_name?.charAt(0) || <User className="h-4 w-4" />}
                        </div>
                        <div>
                          <h4 className="text-sm font-bold text-white flex items-center gap-2">
                            {item.full_name}
                            {isCurrentUser && <span className="text-[10px] bg-brand-accent text-white px-2 py-0.5 rounded-full font-bold">You</span>}
                          </h4>
                          <span className="text-[11px] text-slate-500">Level {item.level} Athlete</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="text-sm font-black text-white">{item.total_xp} XP</span>
                      <p className="text-[10px] text-slate-500 font-medium">Power rating</p>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-8 text-center text-slate-500 text-sm">
                Leaderboard is currently empty. Start logging to rank!
              </div>
            )}
          </div>
        </div>

        {/* Achievements Grid */}
        <div className="lg:col-span-5 space-y-6">
          <div className="glass-card p-6 rounded-2xl space-y-6">
            <div>
              <h3 className="text-lg font-bold text-white">Trophies & Badges</h3>
              <p className="text-xs text-slate-400">Unlock these performance goals for bonus XP.</p>
            </div>

            <div className="grid grid-cols-1 gap-4">
              {achievements.map((ach) => (
                <div 
                  key={ach.id} 
                  className={`flex items-start gap-4 p-4 rounded-xl border transition-all duration-200 ${
                    ach.unlocked 
                      ? 'bg-slate-900/60 border-slate-800 text-slate-200' 
                      : 'bg-slate-950/40 border-slate-900 text-slate-500 opacity-60'
                  }`}
                >
                  <div className={`h-11 w-11 rounded-xl flex items-center justify-center shrink-0 border ${
                    ach.unlocked 
                      ? 'bg-yellow-500/10 border-yellow-500/30 text-yellow-400' 
                      : 'bg-slate-900 border-slate-800 text-slate-600'
                  }`}>
                    {getBadgeIcon(ach.badge_icon)}
                  </div>
                  
                  <div className="overflow-hidden">
                    <h4 className={`text-sm font-bold truncate ${ach.unlocked ? 'text-white' : 'text-slate-500'}`}>
                      {ach.title}
                    </h4>
                    <p className="text-xs text-slate-500 mt-0.5 leading-relaxed">
                      {ach.description}
                    </p>
                    <div className="flex items-center gap-1.5 mt-2 text-[10px] font-bold uppercase tracking-wider text-brand-accent">
                      <Zap className="h-3.5 w-3.5 fill-brand-accent/10" />
                      <span>+{ach.xp_reward} XP</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
