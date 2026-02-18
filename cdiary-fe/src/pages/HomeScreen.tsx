import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus } from 'lucide-react';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';
import { ArtifactSummary } from '../types';

export const HomeScreen: React.FC = () => {
  const navigate = useNavigate();
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<{ profile_image_url?: string } | null>(null);

  useEffect(() => {
    loadArtifacts();
    loadUserProfile();
  }, []);

  const loadUserProfile = async () => {
    const userId = localStorage.getItem('userId');
    if (userId) {
      try {
        const user = await api.getUser(userId);
        setUserProfile(user);
      } catch (error) {
        console.error("Failed to load user profile", error);
      }
    }
  };

  const loadArtifacts = async () => {
    try {
      const data = await api.getArtifacts();
      setArtifacts(data.items);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <TopBar
        title="Cartoon Diary"
        rightAction={
          <button
            onClick={() => navigate('/write')}
            className="p-2 -mr-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-primary"
          >
            <Plus className="w-6 h-6" />
          </button>
        }
      />

      <main className="flex-1 p-4 overflow-y-auto">
        {loading ? (
          <div className="text-center py-10 text-gray-500">Loading diaries...</div>
        ) : artifacts.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-gray-500">
            {userProfile?.profile_image_url ? (
              <>
                <img
                  src={userProfile.profile_image_url}
                  alt="My Character"
                  className="w-32 h-32 rounded-full object-cover mb-4 shadow-lg border-4 border-white dark:border-gray-700"
                />
                <p className="mb-4">No diaries yet.</p>
              </>
            ) : (
              <>
                <p className="mb-4">No diaries yet.</p>
                <button
                  onClick={() => navigate('/character-create')}
                  className="text-primary font-medium hover:underline text-lg font-bold"
                >
                  첫번째로 당신의 캐릭터를 만드세요
                </button>
              </>
            )}
          </div>
        ) : (
          <div className="space-y-4">
            {artifacts.map((art) => (
              <div
                key={art.artifactId}
                className="flex bg-white dark:bg-gray-800 rounded-lg shadow cursor-pointer overflow-hidden border border-gray-100 dark:border-gray-700 hover:shadow-md transition-shadow h-24"
                onClick={() => navigate(`/result/${art.artifactId}`)}
              >
                {/* Thumbnail */}
                <div
                  className="w-24 bg-secondary/10 dark:bg-gray-700 bg-cover bg-center flex-shrink-0"
                  style={{ backgroundImage: `url(${art.thumbnailUrl})` }}
                />

                {/* Content */}
                <div className="flex-1 p-3 flex flex-col justify-center min-w-0">
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-2">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{art.date}</span>
                    <span className="px-1.5 py-0.5 bg-secondary/20 dark:bg-gray-700 rounded text-[10px] uppercase tracking-wide">{art.stylePreset}</span>
                  </div>
                  <div className="font-medium truncate text-gray-900 dark:text-white">{art.summary}</div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Floating Action Button for Mobile (Optional, currently using TopBar action) */}
    </AppShell>
  );
};
