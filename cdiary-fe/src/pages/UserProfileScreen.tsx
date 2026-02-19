import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';
import { User, LogOut, Trash2 } from 'lucide-react';

export const UserProfileScreen: React.FC = () => {
  const navigate = useNavigate();
  const userId = localStorage.getItem('userId');
  const [user, setUser] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);
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
      await api.updateUser(userId, { name: formData.username });
      setIsEditing(false);
      loadUser();
      alert('Profile updated successfully!');
    } catch (error) {
      console.error("Update failed", error);
      alert('Failed to update profile.');
    }
  };

  const handleWithdraw = async () => {
    if (!userId) return;
    if (window.confirm('Are you sure you want to delete your account? This action cannot be undone.')) {
      try {
        await api.deleteUser(userId);
        localStorage.clear();
        navigate('/');
      } catch (error) {
        console.error("Delete failed", error);
        alert('Failed to delete account.');
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
        <TopBar title="Profile" showBack />
        <div className="flex justify-center items-center h-full p-10">Loading...</div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <TopBar title="User Profile" showBack />
      <div className="p-6 flex flex-col items-center">
        {/* Profile Image */}
        <div className="w-32 h-32 rounded-full overflow-hidden bg-gray-200 mb-6 border-4 border-white shadow-lg relative group">
          {user?.profile_image_url ? (
            <img src={user.profile_image_url} alt="Profile" className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-400">
              <User size={48} />
            </div>
          )}
          {/* Optional: Add image upload overlay here if needed */}
        </div>

        {/* User Info Form */}
        <div className="w-full max-w-sm space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Username</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
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
                  Cancel
                </button>
                <button
                  onClick={handleUpdate}
                  className="flex-1 px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary/90"
                >
                  Save
                </button>
              </div>
            ) : (
              <button
                onClick={() => setIsEditing(true)}
                className="w-full px-4 py-2 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 shadow-sm transition-transform active:scale-95"
              >
                Edit Profile
              </button>
            )}

            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 flex items-center justify-center gap-2"
            >
              <LogOut size={18} />
              Log Out
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
    </AppShell>
  );
};
