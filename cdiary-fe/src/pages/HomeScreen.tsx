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

  useEffect(() => {
    loadArtifacts();
  }, []);

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
            <p className="mb-4">No diaries yet.</p>
            <button
              onClick={() => navigate('/write')}
              className="text-primary font-medium hover:underline"
            >
              Write your first diary!
            </button>
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
