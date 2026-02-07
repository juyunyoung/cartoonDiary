import React, { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { AppShell } from '../components/common/AppShell';
import { api } from '../api/client';
import { JobStatus } from '../types';

export const GeneratingScreen: React.FC = () => {
  const { jobId } = useParams<{ jobId: string }>();
  const navigate = useNavigate();
  const [status, setStatus] = useState<string>('Initializing...');
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!jobId) return;

    const interval = setInterval(async () => {
      try {
        const job = await api.getJobStatus(jobId);
        setStatus(job.step);
        setProgress(job.progress * 100);

        if (job.status === JobStatus.DONE && job.artifactId) {
          clearInterval(interval);
          navigate(`/result/${job.artifactId}`);
        } else if (job.status === JobStatus.FAILED) {
          clearInterval(interval);
          alert('Generation Failed');
          navigate('/');
        }
      } catch (error) {
        console.error(error);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, [jobId, navigate]);

  return (
    <AppShell>
      <main className="flex-1 flex flex-col items-center justify-center p-8">
        <div className="w-16 h-16 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin mb-8" />
        <h2 className="text-xl font-bold mb-2">Creating your comic...</h2>
        <p className="text-gray-500 mb-8">{status.replace(/_/g, ' ')}</p>

        <div className="w-full bg-secondary/30 rounded-full h-2.5 dark:bg-gray-700">
          <div className="bg-primary h-2.5 rounded-full transition-all duration-500" style={{ width: `${progress}%` }}></div>
        </div>
      </main>
    </AppShell>
  );
};
