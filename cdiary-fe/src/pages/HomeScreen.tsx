import React, { useEffect, useState, useCallback } from 'react';

import { useNavigate } from 'react-router-dom';
import { Plus, User as UserIcon, Search, X } from 'lucide-react';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { api } from '../api/client';

import { ArtifactSummary } from '../types';
import { DiaryList } from '../components/home/DiaryList';


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

  const loadArtifacts = useCallback(async (showLoading = true) => {
    try {
      if (showLoading) setLoading(true);
      const userId = localStorage.getItem('userId');
      const data = await api.getArtifacts(20, searchQuery, userId || undefined);
      setArtifacts(data.items);
    } catch (error) {
      console.error(error);
    } finally {
      if (showLoading) setLoading(false);
    }
  }, [searchQuery]);



  const handleDelete = useCallback(async (e: React.MouseEvent, artifactId: string) => {
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
  }, []);

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
            {searchQuery ? (
              <div className="text-center">
                <Search className="w-12 h-12 text-gray-300 mb-3 mx-auto" />
                <p className="text-lg">검색 결과가 없습니다.</p>
                <p className="text-sm text-gray-400 mt-1">다른 키워드로 검색해 보세요.</p>
              </div>
            ) : userProfile?.profile_image_url ? (
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
          <DiaryList
            artifacts={artifacts}
            onDelete={handleDelete}
            onJobDone={loadArtifacts}
          />
        )}
      </main>

      {/* Floating Action Button for Mobile (Optional, currently using TopBar action) */}
    </AppShell>
  );
};
