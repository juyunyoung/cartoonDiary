import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';
import { User, LogOut, Trash2, RefreshCw, Loader2, Camera } from 'lucide-react';
import { useAlert } from '../context/AlertContext';
import { useLanguage } from '../context/LanguageContext';

export const UserProfileScreen: React.FC = () => {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const { showAlert, showConfirm } = useAlert();
  const { t } = useLanguage();
  const [formData, setFormData] = useState({
    username: '',
    // password field removed for simplicity unless required
  });

  useEffect(() => {
    if (!userId) {
      navigate('/signin');
      return;
    }
    loadUser();
  }, [userId]);

  const loadUser = async () => {
    try {
      const data = await api.getUser(userId!);
      setUser(data);
      setFormData({ username: data.username });
    } catch (error) {
      console.error("Failed to load user", error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async () => {
    if (!userId) return;
    try {
      await api.updateUser(userId, { username: formData.username });
      setIsEditing(false);
      loadUser();
    } catch (error) {
      console.error("Update failed", error);
      showAlert(t('update_failed'));
    }
  };

  const handleRegenerate = async () => {
    if (!userId || !user?.profile_prompt) return;
    setIsRegenerating(true);
    try {
      const { image_data } = await api.generateImage(user.profile_prompt);
      await api.saveProfileImage(userId, image_data, user.profile_prompt);
      await loadUser();
    } catch (error) {
      console.error("Regeneration failed", error);
      showAlert(t('regen_failed'));
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleWithdraw = async () => {
    if (!userId) return;
    const confirmed = await showConfirm(t('withdraw_confirm'));
    if (confirmed) {
      try {
        await api.deleteUser(userId);
        localStorage.clear();
        navigate('/');
      } catch (error) {
        console.error("Delete failed", error);
        showAlert(t('withdraw_failed'));
      }
    }
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/');
  };

  if (loading) {
    return (
      <AppShell>
        <TopBar title={t('profile_title')} showBack />
        <div className="flex justify-center items-center h-full p-10">{t('loading')}</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <TopBar title={t('profile_title')} showBack onBack={() => navigate('/home')} />
      <div className="p-6 flex flex-col items-center">
        {/* Profile Image */}
        <div className="relative group mb-6">
          <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-200 border-4 border-white shadow-lg relative">
            {user?.profile_image_url ? (
              <img src={user.profile_image_url} alt="Profile" className="w-full h-full object-cover" />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-400">
                <User size={48} />
              </div>
            )}

            {/* Regeneration Overlay (Visible in Edit Mode) */}
            {isEditing && user?.profile_prompt && (
              <button
                onClick={handleRegenerate}
                disabled={isRegenerating}
                className="absolute inset-0 bg-black/40 flex flex-col items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity disabled:opacity-100"
                title="Regenerate Character"
              >
                {isRegenerating ? (
                  <Loader2 className="text-white w-8 h-8 animate-spin" />
                ) : (
                  <>
                    <Camera className="text-white w-8 h-8 mb-1" />
                    <span className="text-white text-[10px] font-bold">REGENERATE</span>
                  </>
                )}
              </button>
            )}
          </div>

          {/* Prompt to edit character attributes */}
          {isEditing && (
            <button
              onClick={() => navigate('/character-create')}
              className="absolute -right-2 -bottom-2 p-2 bg-white dark:bg-gray-700 rounded-full shadow-md border border-gray-100 dark:border-gray-600 text-primary hover:text-primary/80 transition-transform active:scale-90"
              title="Change Character Settings"
            >
              <RefreshCw size={16} />
            </button>
          )}
        </div>

        {isEditing && user?.profile_prompt && (
          <div className="flex flex-col items-center gap-2 mb-6">
            <button
              onClick={handleRegenerate}
              disabled={isRegenerating}
              className="flex items-center gap-2 px-4 py-2 bg-secondary/20 hover:bg-secondary/30 text-primary text-xs font-bold rounded-full transition-colors disabled:opacity-50"
            >
              {isRegenerating ? (
                <Loader2 size={14} className="animate-spin" />
              ) : (
                <RefreshCw size={14} />
              )}
              {t('regen_image')}
            </button>
            <button
              onClick={() => navigate('/character-create')}
              className="text-[10px] text-gray-400 hover:text-primary underline"
            >
              {t('change_char_settings')}
            </button>
          </div>
        )}

        {/* User Info Form */}
        <div className="w-full max-w-sm space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('username')}</label>
            {isEditing ? (
              <input
                type="text"
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary focus:border-primary"
              />
            ) : (
              <div className="p-3 bg-gray-50 rounded-md border border-gray-100 text-gray-800 font-medium">
                {user?.username}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
            <div className="p-3 bg-gray-50 rounded-md border border-gray-100 text-gray-500">
              {user?.email || 'No email provided'}
            </div>
          </div>

          <div className="pt-6 space-y-3">
            {isEditing ? (
              <div className="flex gap-2">
                <button
                  onClick={() => setIsEditing(false)}
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg text-gray-700 font-medium hover:bg-gray-50"
                >
                  {t('cancel')}
                </button>
                <button
                  onClick={handleUpdate}
                  className="flex-1 px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary/90"
                >
                  {t('save')}
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="w-full px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 shadow-sm transition-transform active:scale-95"
              >
                {t('edit_profile')}
              </button>
            )}

            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 flex items-center justify-center gap-2"
            >
              <LogOut size={18} />
              {t('logout')}
            </button>

            <div className="mt-8 pt-6 border-t border-gray-200">
              <button
                onClick={handleWithdraw}
                className="w-full px-4 py-2 text-red-500 hover:bg-red-50 rounded-lg font-medium text-sm flex items-center justify-center gap-2"
              >
                <Trash2 size={16} />
                Withdraw (Delete Account)
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShell >
  );
};
