import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { Button } from '../components/common/Button';

import Surprised from '../assets/moods/surprised.png';
import VeryHappy from '../assets/moods/very_happy.png';
import SoftSmile from '../assets/moods/soft_smile.png';
import Motivated from '../assets/moods/motivated.png';
import Emotionless from '../assets/moods/emotionless.png';
import Sad from '../assets/moods/sad.png';
import Crying from '../assets/moods/crying.png';
import Curious from '../assets/moods/curious.png';
import Sigh from '../assets/moods/sigh.png';
import Normal from '../assets/moods/normal.png';

export const WriteDiaryScreen: React.FC = () => {
  const navigate = useNavigate();
  const [text, setText] = useState('');

  const moods = [
    { id: 'surprised', img: Surprised, label: 'Surprised' },
    { id: 'very_happy', img: VeryHappy, label: 'Very Happy' },
    { id: 'soft_smile', img: SoftSmile, label: 'Soft Smile' },
    { id: 'motivated', img: Motivated, label: 'Motivated' },
    { id: 'emotionless', img: Emotionless, label: 'Emotionless' },
    { id: 'sad', img: Sad, label: 'Sad' },
    { id: 'crying', img: Crying, label: 'Crying' },
    { id: 'curious', img: Curious, label: 'Curious' },
    { id: 'sigh', img: Sigh, label: 'Sigh' },
    { id: 'normal', img: Normal, label: 'Normal' },
  ];

  const [mood, setMood] = useState(moods[2].id); // Default to Soft Smile

  const handleNext = () => {
    if (text.trim().length < 5) return; // Simple validation
    // Save to local storage or state management would go here
    localStorage.setItem('draftDiary', JSON.stringify({ text, mood }));
    navigate('/options');
  };

  return (
    <AppShell>
      <TopBar title="New Diary" showBack />

      <main className="flex-1 p-4 flex flex-col">
        <label className="block text-sm font-medium mb-2">How was your day?</label>
        <div className="flex gap-4 mb-6 overflow-x-auto pb-4 pt-10 px-4">
          {moods.map((m) => (
            <button
              key={m.id}
              onClick={() => setMood(m.id)}
              className={`p-3 rounded-2xl transition-all duration-300 shrink-0 flex flex-col items-center gap-2 ${mood === m.id
                ? 'bg-accent shadow-lg shadow-primary/20 scale-125 -translate-y-2 ring-4 ring-primary z-10'
                : 'bg-secondary/20 hover:bg-accent/60'
                }`}
              title={m.label}
            >
              <img src={m.img} alt={m.label} className="w-20 h-20 object-contain drop-shadow-sm" />
            </button>
          ))}
        </div>

        <label className="block text-sm font-medium mb-2">Write your story</label>
        <textarea
          className="flex-1 w-full p-4 border border-secondary/50 rounded-lg resize-none bg-secondary/10 focus:ring-2 focus:ring-primary outline-none placeholder-primary/60"
          placeholder="What happened today?"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <div className="text-right text-xs text-primary mt-2">
          {text.length} chars
        </div>
      </main>

      <div className="p-4 border-t border-primary/20">
        <Button
          className="w-full"
          onClick={handleNext}
          disabled={text.trim().length < 5}
        >
          Turn into a Comic
        </Button>
      </div>
    </AppShell>
  );
};
