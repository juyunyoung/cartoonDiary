import React, { useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';

export const GeneratingScreen: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    if (!jobId) return;

    // Navigate to home immediately (or after a very short delay to show "Starting")
    const timeout = setTimeout(() => {
      navigate('/', { replace: true });
    }, 1000); // 1 second delay just to visually confirm start, then go to home

    return () => clearTimeout(timeout);
  }, [jobId, navigate]);

  return (
    <AppShell>
      <main className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-8" />
        <h2 className="text-xl font-bold mb-2">Creating your comic...</h2>
        <p className="text-gray-500 mb-8">Please wait...</p>
      </main>
    </AppShell>
  );
};
