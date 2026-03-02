import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { Button } from '../components/common/Button';
import { Card } from '../components/common/Card';
import { api } from '../api/client';
import { useAlert } from '../context/AlertContext';
import { useLanguage } from '../context/LanguageContext';
import { ArtifactResponse } from '../types';

export const ResultScreen: React.FC = () => {
  const { artifactId } = useParams<{ artifactId: string }>();
  const navigate = useNavigate();
  const { showAlert } = useAlert();
  const { t } = useLanguage();
  const [artifact, setArtifact] = useState<ArtifactResponse | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const fetchArtifact = async () => {
    if (artifactId) {
      try {
        const data = await api.getArtifact(artifactId);
        setArtifact(data);
        return data;
      } catch (error) {
        console.error(error);
      }
    }
    return null;
  };

  useEffect(() => {
    fetchArtifact().then(art => {
      // If it's a new placeholder (no image yet), we should poll or listen for progress
      if (art && !art.finalStripUrl) {
        startPolling();
      }
    });

    // Setup SSE or Polling
    let pollInterval: any;

    const startPolling = () => {
      pollInterval = setInterval(async () => {
        const updatedArt = await fetchArtifact();
        if (updatedArt && updatedArt.finalStripUrl) {
          clearInterval(pollInterval);
        }
      }, 3000);
    };

    return () => {
      if (pollInterval) clearInterval(pollInterval);
    };
  }, [artifactId]);

  const handleRegenerate = async () => {
    if (!artifact) return;

    setIsRegenerating(true);
    try {
      await api.generateDiary({
        diaryText: artifact.diaryText,
        mood: artifact.mood || 'normal',
        stylePreset: artifact.stylePreset as any,
        diaryDate: artifact.diaryDate as any,
        options: artifact.options || { moreFunny: false, focusEmotion: false, lessText: false }
      });
      navigate('/home');
    } catch (error) {
      showAlert(t('regen_start_failed'));
      console.error(error);
    } finally {
      setIsRegenerating(false);
    }
  };

  if (!artifact) return <div className="p-4 text-center">{t('loading')}</div>;

  return (
    <AppShell>
      <TopBar title={t('your_comic')} showBack onBack={() => navigate('/home')} />

      <main className="flex-1 p-4 overflow-y-auto">
        <Card className="mb-4">
          {/* Main Strip Image */}
          <div className="w-full bg-secondary/10 flex items-center justify-center min-h-[200px]">
            {artifact.finalStripUrl ? (
              <img src={artifact.finalStripUrl} alt="Comic Strip" className="w-full h-auto object-contain animate-in fade-in duration-500" />
            ) : (
              <div className="flex flex-col items-center py-10">
                <div className="w-10 h-10 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-3" />
                <p className="text-sm text-gray-500">{t('creating_comic')}</p>
              </div>
            )}
          </div>
        </Card>

        {/* Diary Content */}
        {artifact.diaryText && (
          <Card className="p-4 mb-4">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">{t('today_diary')}</h3>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">
              {artifact.diaryText}
            </p>
          </Card>
        )}
      </main>

      <div className="p-4 border-t border-primary/10 dark:border-gray-700 bg-white dark:bg-gray-800 flex gap-3">
        <Button
          variant="secondary"
          className="flex-1"
          onClick={handleRegenerate}
          isLoading={isRegenerating}
          disabled={!artifact.finalStripUrl}
        >
          {t('regenerate')}
        </Button>
        <Button
          className="flex-1"
          onClick={() => showAlert(t('saved_at'))}
          disabled={!artifact.finalStripUrl}
        >
          {t('save_share')}
        </Button>
      </div>
    </AppShell>
  );
};
