import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { TopBar } from '../components/common/TopBar';
import { Button } from '../components/common/Button';
import { api } from '../api/client';
import { ArtifactResponse } from '../types';

export const ResultScreen: React.FC = () => {
  const { artifactId } = useParams<{ artifactId: string }>();
  const navigate = useNavigate();
  const [artifact, setArtifact] = useState<ArtifactResponse | null>(null);

  useEffect(() => {
    if (artifactId) {
      api.getArtifact(artifactId).then(setArtifact).catch(console.error);
    }
  }, [artifactId]);

  if (!artifact) return <div>Loading...</div>;

  return (
    <AppShell>
      <TopBar title="Your Comic" showBack onBack={() => navigate('/')} />

      <main className="flex-1 p-4 overflow-y-auto">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden mb-4">
          {/* Main Strip Image */}
          <div className="aspect-[1/3] w-full bg-secondary/10 flex items-center justify-center">
            <img src={artifact.finalStripUrl} alt="Comic Strip" className="w-full h-full object-contain" />
          </div>
        </div>
      </main>

      <div className="p-4 border-t border-primary/10 dark:border-gray-700 bg-white dark:bg-gray-800 flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={() => alert('Regenerate clicked')}>
          Regenerate
        </Button>
        <Button className="flex-1" onClick={() => alert('Saved!')}>
          Save & Share
        </Button>
      </div>
    </AppShell>
  );
};
