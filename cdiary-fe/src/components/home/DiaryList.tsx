import React, { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { API_BASE_URL } from '../../api/client';
import { ArtifactSummary } from '../../types';
import { DiaryItem } from './DiaryItem';

interface DiaryListProps {
  artifacts: ArtifactSummary[];
  onDelete: (e: React.MouseEvent, id: string) => void;
  onJobDone: (showLoading?: boolean) => void;
}

export const DiaryList: React.FC<DiaryListProps> = ({ artifacts, onDelete, onJobDone }) => {
  const navigate = useNavigate();
  const [activeJobs, setActiveJobs] = useState<Record<string, any>>({});
  const completedJobIds = useRef(new Set<string>());

  useEffect(() => {
    const sseUrl = `${API_BASE_URL}/jobs/stream`;
    const sse = new EventSource(sseUrl);

    sse.onmessage = (event) => {
      try {
        const jobsData = JSON.parse(event.data) as Record<string, any>;
        setActiveJobs(jobsData);

        const newlyDoneJobs = Object.entries(jobsData).filter(([id, job]) =>
          job.status === "DONE" && !completedJobIds.current.has(id)
        );

        if (newlyDoneJobs.length > 0) {
          newlyDoneJobs.forEach(([id]) => completedJobIds.current.add(id));
          onJobDone(false);
        }
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };

    return () => sse.close();
  }, [onJobDone]);

  return (
    <div className="space-y-4">
      {artifacts.map((art) => (
        <DiaryItem
          key={art.artifactId}
          art={art}
          activeJob={Object.values(activeJobs).find(job =>
            job.artifactId &&
            art.artifactId &&
            job.artifactId.toLowerCase() === art.artifactId.toLowerCase()
          )}
          onDelete={onDelete}
          onClick={() => navigate(`/result/${art.artifactId}`)}
        />
      ))}
    </div>
  );
};
