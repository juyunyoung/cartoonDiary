import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { Button } from '../components/common/Button';
import { StylePreset } from '../types';
import { api } from '../api/client';

export const OptionsScreen: React.FC = () => {
  const navigate = useNavigate();
  const [style, setStyle] = useState<StylePreset>(StylePreset.CUTE);
  const [loading, setLoading] = useState(false);

  const handleGenerate = async () => {
    const draft = localStorage.getItem('draftDiary');
    if (!draft) return;
    const { text, mood } = JSON.parse(draft);

    setLoading(true);
    try {
      const { jobId } = await api.generateDiary({
        diaryText: text,
        mood,
        stylePreset: style,
        options: { moreFunny: false, focusEmotion: false, lessText: false }
      });
      navigate(`/generate/${jobId}`);
    } catch (error) {
      alert('Failed to start generation');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <TopBar title="Style & Options" showBack />

      <main className="flex-1 p-4">
        <h2 className="text-lg font-bold mb-4">Choose a Style</h2>
        <div className="grid grid-cols-2 gap-3 mb-6">
          {Object.values(StylePreset).map((preset) => (
            <button
              key={preset}
              onClick={() => setStyle(preset)}
              className={`p-4 rounded-lg border-2 text-left transition-all ${style === preset
                ? 'border-primary bg-primary/10 dark:bg-primary/20'
                : 'border-gray-200 dark:border-gray-700 hover:border-blue-200'
                }`}
            >
              <div className="capitalize font-bold">{preset}</div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                {preset === 'cute' ? 'Soft & Adorable' :
                  preset === 'comedy' ? 'Funny & Exaggerated' :
                    preset === 'drama' ? 'Serious & Emotional' : 'Clean & Simple'}
              </div>
            </button>
          ))}
        </div>

        {/* Placeholder for more options */}
        <div className="border-t pt-4 mt-4">
          <h3 className="text-sm font-medium mb-2">Advanced Options</h3>
          <div className="text-xs text-gray-400">More options coming soon...</div>
        </div>
      </main>

      <div className="p-4 border-t border-gray-100 dark:border-gray-700">
        <Button
          className="w-full"
          onClick={handleGenerate}
          isLoading={loading}
        >
          Generate Comic
        </Button>
      </div>
    </AppShell>
  );
};
