import { DiaryEntryRequest, JobResponse, ArtifactResponse, ArtifactSummary } from '../types';

const API_BASE_URL = 'http://localhost:5050/api';

export const api = {
  async generateDiary(data: DiaryEntryRequest): Promise<{ jobId: string }> {
    const response = await fetch(`${API_BASE_URL}/diary/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to start generation');
    return response.json();
  },

  async getJobStatus(jobId: string): Promise<JobResponse> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to get job status');
    return response.json();
  },

  async getArtifacts(limit: number = 20): Promise<{ items: ArtifactSummary[] }> {
    const response = await fetch(`${API_BASE_URL}/artifacts?limit=${limit}`);
    if (!response.ok) throw new Error('Failed to list artifacts');
    return response.json();
  },

  async getArtifact(artifactId: string): Promise<ArtifactResponse> {
    const response = await fetch(`${API_BASE_URL}/artifacts/${artifactId}`);
    if (!response.ok) throw new Error('Failed to get artifact');
    return response.json();
  },

  async regenerate(data: any): Promise<{ jobId: string }> {
    // Placeholder for regeneration API
    console.log("Regenerate not implemented in backend fully yet", data);
    return { jobId: "mock-job-id" };
  }
};
