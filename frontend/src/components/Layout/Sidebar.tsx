import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { 
  LayoutDashboard, Dumbbell, BarChart3, Trophy, Settings, LogOut, Flame
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const location = useLocation();

  const links = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Workout Area', path: '/workout', icon: Dumbbell },
    { name: 'Analytics', path: '/analytics', icon: BarChart3 },
    { name: 'Leaderboard', path: '/leaderboard', icon: Trophy },
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  // Calculate XP percentage for level progress bar
  const currentLevelXp = user ? (user.level - 1) ** 2 * 100 : 0;
  const nextLevelXp = user ? user.level ** 2 * 100 : 100;
  const xpInCurrentLevel = user ? user.total_xp - currentLevelXp : 0;
  const levelXpRequirement = nextLevelXp - currentLevelXp;
  const xpPercent = Math.min(100, Math.max(0, (xpInCurrentLevel / (levelXpRequirement || 100)) * 100));

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen fixed left-0 top-0 text-slate-300">
      {/* Brand Header */}
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-tr from-brand-accent to-brand-secondary flex items-center justify-center text-white font-extrabold text-xl shadow-lg shadow-brand-accent/20">
          FV
        </div>
        <div>
          <h1 className="font-extrabold text-white text-lg tracking-wide leading-none">FitVision AI</h1>
          <span className="text-xs text-slate-500 font-medium">Enterprise Core</span>
        </div>
      </div>

      {/* User Quick Profile Info */}
      {user && (
        <div className="p-5 border-b border-slate-800 bg-slate-950/40">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-12 w-12 rounded-full overflow-hidden border-2 border-brand-accent/40 bg-slate-800 flex items-center justify-center">
              {user.profile_pic_url ? (
                <img 
                  src={`${(import.meta as any).env.VITE_API_URL || 'http://localhost:8000'}${user.profile_pic_url}`} 
                  alt="avatar" 
                  className="h-full w-full object-cover"
                />
              ) : (
                <span className="font-bold text-white text-lg">{user.full_name.charAt(0)}</span>
              )}
            </div>
            <div className="overflow-hidden">
              <h2 className="font-bold text-white text-sm truncate">{user.full_name}</h2>
              <div className="flex items-center gap-1.5 text-xs font-semibold text-amber-500 mt-0.5">
                <Flame className="h-3.5 w-3.5 fill-amber-500/10" />
                <span>{user.streak_count} Day Streak</span>
              </div>
            </div>
          </div>

          {/* Level Progress */}
          <div>
            <div className="flex justify-between items-center text-xs mb-1">
              <span className="font-semibold text-brand-accent">LEVEL {user.level}</span>
              <span className="text-slate-500 font-medium">{user.total_xp} Total XP</span>
            </div>
            <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
              <div 
                className="bg-gradient-to-r from-brand-accent to-brand-secondary h-full rounded-full transition-all duration-500" 
                style={{ width: `${xpPercent}%` }}
              />
            </div>
            <div className="flex justify-between text-[10px] text-slate-500 mt-1">
              <span>{Math.round(xpInCurrentLevel)} XP</span>
              <span>{Math.round(levelXpRequirement)} XP Next</span>
            </div>
          </div>
        </div>
      )}

      {/* Main Navigation Links */}
      <nav className="flex-1 px-4 py-6 space-y-1">
        {links.map((link) => {
          const Icon = link.icon;
          const isActive = location.pathname === link.path;
          return (
            <Link
              key={link.path}
              to={link.path}
              className={`flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                isActive 
                  ? 'bg-gradient-to-r from-brand-accent to-brand-accent/80 text-white shadow-lg shadow-brand-accent/15'
                  : 'hover:bg-slate-800/60 hover:text-white'
              }`}
            >
              <Icon className={`h-4.5 w-4.5 ${isActive ? 'text-white' : 'text-slate-400 group-hover:text-white'}`} />
              <span>{link.name}</span>
            </Link>
          );
        })}
      </nav>

      {/* Log out Footer */}
      <div className="p-4 border-t border-slate-800">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium hover:bg-red-500/10 text-slate-400 hover:text-red-400 transition-all duration-200"
        >
          <LogOut className="h-4.5 w-4.5" />
          <span>Sign Out</span>
        </button>
      </div>
    </aside>
  );
};
