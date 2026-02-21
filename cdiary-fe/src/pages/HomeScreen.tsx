import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, User as UserIcon, Trash2, Search, X } from 'lucide-react';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';
import { ArtifactSummary } from '../types';

export const HomeScreen: React.FC = () => {
  const navigate = useNavigate();
  const [artifacts, setArtifacts] = useState<ArtifactSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [userProfile, setUserProfile] = useState<{ profile_image_url?: string } | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [isSearching, setIsSearching] = useState(false);

  useEffect(() => {
    loadUserProfile();
  }, []);

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      loadArtifacts();
    }, 500);
    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

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
      setLoading(true);
      const data = await api.getArtifacts(20, searchQuery);
      setArtifacts(data.items);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, artifactId: string) => {
    e.stopPropagation();
    if (window.confirm('Are you sure you want to delete this diary?')) {
      try {
        await api.deleteArtifact(artifactId);
        setArtifacts(prev => prev.filter(a => a.artifactId !== artifactId));
      } catch (error) {
        console.error("Failed to delete artifact", error);
        alert("Failed to delete diary.");
      }
    }
  };

  return (
    <AppShell>
      <TopBar
        title="Cartoon Diary"
        rightAction={
          <div className="flex items-center gap-1">
            <button
              onClick={() => {
                setIsSearching(!isSearching);
                if (isSearching) setSearchQuery('');
              }}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors"
              title="Search Diaries"
            >
              <Search className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/profile')}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-gray-600 dark:text-gray-300 transition-colors"
              title="Edit Profile"
            >
              <UserIcon className="w-5 h-5" />
            </button>
            <button
              onClick={() => navigate('/write')}
              className="p-2 rounded-full hover:bg-gray-100 dark:hover:bg-gray-700 text-primary transition-colors"
              title="New Diary"
            >
              <Plus className="w-6 h-6" />
            </button>
          </div>
        }
      />

      {/* Search Bar - conditionally rendered */}
      <div
        className={`bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 transition-all duration-300 ease-in-out overflow-hidden ${isSearching ? 'max-h-16 opacity-100' : 'max-h-0 opacity-0'
          }`}
      >
        <div className="px-4 py-3 flex items-center gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="일기 내용 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-8 py-2 bg-gray-100 dark:bg-gray-700 border-transparent rounded-full text-sm focus:border-primary focus:ring-1 focus:ring-primary dark:text-white"
              autoFocus={isSearching}
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      </div>

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
                  className="w-24 bg-secondary/10 dark:bg-gray-700 flex-shrink-0 flex items-center justify-center relative overflow-hidden"
                >
                  {art.thumbnailUrl ? (
                    <img
                      src={art.thumbnailUrl}
                      alt="Thumbnail"
                      className="w-full h-full object-cover object-top"
                    />
                  ) : (
                    <div className="flex flex-col items-center justify-center bg-gray-50 dark:bg-gray-800 w-full h-full">
                      <div className="w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-1" />
                      <span className="text-[10px] text-gray-500 font-medium">Generating</span>
                    </div>
                  )}
                </div>


                {/* Content */}
                <div className="flex-1 p-3 flex flex-col justify-center min-w-0">
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-1 flex items-center gap-2">
                    <span className="font-medium text-gray-700 dark:text-gray-300">{art.date}</span>
                    <span className="px-1.5 py-0.5 bg-secondary/20 dark:bg-gray-700 rounded text-[10px] uppercase tracking-wide">{art.stylePreset}</span>
                  </div>
                  <div className="font-medium truncate text-gray-900 dark:text-white">{art.summary}</div>
                </div>

                <button
                  onClick={(e) => handleDelete(e, art.artifactId)}
                  className="p-3 flex items-center justify-center text-gray-400 hover:text-red-500 hover:bg-red-50 transition-colors"
                  title="Delete"
                >
                  <Trash2 size={20} />
                </button>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Floating Action Button for Mobile (Optional, currently using TopBar action) */}
    </AppShell>
  );
};
