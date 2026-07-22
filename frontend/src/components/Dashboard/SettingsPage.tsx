import React, { useState } from 'react';
import { useAuth } from '../../context/AuthContext';
import { usersApi } from '../../services/api';
import { Settings, User, Key, Camera, Check, AlertCircle } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const { user, updateUser } = useAuth();
  
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [avatarFile, setAvatarFile] = useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = useState<string | null>(null);
  
  const [statusMsg, setStatusMsg] = useState<{type: 'success' | 'error', text: string} | null>(null);
  const [loading, setLoading] = useState(false);

  const handleAvatarChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setAvatarFile(file);
      setAvatarPreview(URL.createObjectURL(file));
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatusMsg(null);
    setLoading(true);

    if (password && password !== confirmPassword) {
      setStatusMsg({ type: 'error', text: 'Passwords do not match' });
      setLoading(false);
      return;
    }

    try {
      // 1. Update basic information
      const updatePayload: any = { full_name: fullName, email };
      if (password) {
        updatePayload.password = password;
      }
      
      let updatedUser = await usersApi.updateMe(updatePayload);

      // 2. Update avatar if changed
      if (avatarFile) {
        const formData = new FormData();
        formData.append('file', avatarFile);
        updatedUser = await usersApi.uploadAvatar(formData);
      }

      updateUser(updatedUser);
      setStatusMsg({ type: 'success', text: 'Settings updated successfully!' });
      setPassword('');
      setConfirmPassword('');
      setAvatarFile(null);
    } catch (err: any) {
      console.error(err);
      setStatusMsg({
        type: 'error',
        text: err.response?.data?.detail || 'Failed to save changes. Please try again.'
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-4xl mx-auto space-y-8 bg-gradient-mesh min-h-screen text-slate-100 pb-16">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-white flex items-center gap-2">
          <Settings className="h-8 w-8 text-brand-accent" />
          Account Settings
        </h1>
        <p className="text-slate-400 mt-1">Configure profile details, change security passwords, and manage avatars.</p>
      </div>

      <div className="glass-card p-8 rounded-2xl">
        <form onSubmit={handleProfileSubmit} className="space-y-6">
          
          {/* Status Message */}
          {statusMsg && (
            <div className={`p-4 rounded-xl flex items-center gap-3 text-sm font-semibold border ${
              statusMsg.type === 'success' 
                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-400' 
                : 'bg-red-500/10 border-red-500/20 text-red-400'
            }`}>
              {statusMsg.type === 'success' ? <Check className="h-5 w-5" /> : <AlertCircle className="h-5 w-5" />}
              <span>{statusMsg.text}</span>
            </div>
          )}

          {/* Avatar Upload Grid */}
          <div className="flex flex-col sm:flex-row items-center gap-6 pb-6 border-b border-slate-800">
            <div className="relative h-24 w-24 rounded-full overflow-hidden border-4 border-brand-accent/30 bg-slate-800 flex items-center justify-center">
              {avatarPreview ? (
                <img src={avatarPreview} alt="Preview" className="h-full w-full object-cover" />
              ) : user?.profile_pic_url ? (
                <img 
                  src={`${(import.meta as any).env.VITE_API_URL || 'http://localhost:8000'}${user.profile_pic_url}`} 
                  alt="Avatar" 
                  className="h-full w-full object-cover" 
                />
              ) : (
                <span className="font-bold text-white text-3xl">{user?.full_name.charAt(0)}</span>
              )}
              
              <label 
                htmlFor="avatar-upload" 
                className="absolute inset-0 bg-black/50 opacity-0 hover:opacity-100 flex items-center justify-center text-white cursor-pointer transition-all duration-150"
              >
                <Camera className="h-6 w-6" />
              </label>
              <input 
                id="avatar-upload" 
                type="file" 
                accept="image/*" 
                onChange={handleAvatarChange} 
                className="hidden" 
              />
            </div>
            
            <div className="text-center sm:text-left">
              <h3 className="font-bold text-white text-base">Profile Photo</h3>
              <p className="text-xs text-slate-500 mt-1">Allowed formats: PNG, JPG or JPEG. Max size 2MB.</p>
              <label 
                htmlFor="avatar-upload"
                className="mt-3 inline-block bg-slate-800 hover:bg-slate-700 border border-slate-700 text-white font-bold text-xs px-4 py-2 rounded-xl cursor-pointer transition-all"
              >
                Choose Photo
              </label>
            </div>
          </div>

          {/* Form Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <User className="h-3.5 w-3.5" />
                Full Name
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-accent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                Email Address
              </label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white focus:outline-none focus:border-brand-accent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                <Key className="h-3.5 w-3.5" />
                New Password (Optional)
              </label>
              <input
                type="password"
                placeholder="Leave blank to keep same"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-brand-accent transition-all"
              />
            </div>

            <div className="space-y-2">
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                placeholder="Leave blank to keep same"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-brand-accent transition-all"
              />
            </div>
          </div>

          <div className="pt-4 flex justify-end">
            <button
              type="submit"
              disabled={loading}
              className="bg-gradient-to-r from-brand-accent to-brand-secondary hover:opacity-90 font-bold text-sm text-white px-8 py-3 rounded-xl shadow-lg shadow-brand-accent/20 transition-all duration-200"
            >
              {loading ? 'Saving Changes...' : 'Save Settings'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
