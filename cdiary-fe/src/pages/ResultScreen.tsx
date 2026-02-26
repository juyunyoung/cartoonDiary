import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { Button } from '../components/common/Button';
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

  useEffect(() => {
    if (artifactId) {
      api.getArtifact(artifactId).then(setArtifact).catch(console.error);
    }
  }, [artifactId]);

  const handleRegenerate = async () => {
    if (!artifact) return;

    setIsRegenerating(true);
    try {
      const { jobId } = await api.generateDiary({
        diaryText: artifact.diaryText,
        mood: artifact.mood || 'normal',
        stylePreset: artifact.stylePreset as any,
        diaryDate: artifact.diaryDate as any,
        options: artifact.options || { moreFunny: false, focusEmotion: false, lessText: false }
      });
      navigate(`/generate/${jobId}`);
    } catch (error) {
      showAlert(t('regen_start_failed'));
      console.error(error);
    } finally {
      setIsRegenerating(false);
    }
  };

  if (!artifact) return <div>{t('loading')}</div>;

  return (
    <AppShell>
      <TopBar title={t('your_comic')} showBack onBack={() => navigate('/')} />

      <main className="flex-1 p-4 overflow-y-auto">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-4">
          {/* Main Strip Image */}
          <div className="w-full bg-secondary/10 flex items-center justify-center">
            <img src={artifact.finalStripUrl} alt="Comic Strip" className="w-full h-auto object-contain" />
          </div>
        </div>

        {/* Diary Content */}
        {artifact.diaryText && (
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow p-4 mb-4">
            <h3 className="font-bold text-gray-900 dark:text-gray-100 mb-2">{t('today_diary')}</h3>
            <p className="text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed text-sm">
              {artifact.diaryText}
            </p>
          </div>
        )}
      </main>

      <div className="p-4 border-t border-primary/10 dark:border-gray-700 bg-white dark:bg-gray-800 flex gap-3">
        <Button
          variant="secondary"
          className="flex-1"
          onClick={handleRegenerate}
          isLoading={isRegenerating}
        >
          {t('regenerate')}
        </Button>
        <Button className="flex-1" onClick={() => showAlert(t('saved_at'))}>
          {t('save_share')}
        </Button>
      </div>
    </AppShell>
  );
};
