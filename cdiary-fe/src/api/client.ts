import { DiaryEntryRequest, JobResponse, ArtifactResponse, ArtifactSummary } from '../types';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5050/api';


export const api = {
  async generateDiary(data: DiaryEntryRequest): Promise<{ jobId: string }> {
    const response = await fetch(`${API_BASE_URL}/diary/generate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to start generation');
    return response.json();
  },

  async register(data: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Registration failed');
    }
    return response.json();
  },

  async login(data: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Login failed');
    }
    return response.json();
  },

  async generateImage(prompt: string): Promise<{ image_url: string, s3_key: string, image_data: string }> {
    const response = await fetch(`${API_BASE_URL}/image/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    if (!response.ok) throw new Error('Failed to generate image');
    return response.json();
  },

  async saveProfileImage(userId: string, imageData: string, profilePrompt?: string): Promise<{ s3_key: string, image_url: string }> {
    const response = await fetch(`${API_BASE_URL}/image/save`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, imageData, profilePrompt }),
    });
    if (!response.ok) throw new Error('Failed to save profile image');
    return response.json();
  },

  async getUser(userId: string): Promise<{ id: string, username: string, email?: string, profile_image_url?: string, profile_prompt?: string }> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`);
    if (!response.ok) throw new Error('Failed to get user');
    return response.json();
  },

  async getJobStatus(jobId: string): Promise<JobResponse> {
    const response = await fetch(`${API_BASE_URL}/jobs/${jobId}`);
    if (!response.ok) throw new Error('Failed to get job status');
    return response.json();
  },

  async getArtifacts(limit: number = 20, query?: string, userId?: string): Promise<{ items: ArtifactSummary[] }> {
    if (!userId) {
      // Fallback or error if userId is missing, but usually HomeScreen has it
      return { items: [] };
    }

    let url: string;
    if (query) {
      url = `${API_BASE_URL}/diary/search?user_id=${userId}&query=${encodeURIComponent(query)}`;
    } else {
      url = `${API_BASE_URL}/diary/user/${userId}`;
    }

    const response = await fetch(url);
    if (!response.ok) throw new Error('Failed to fetch diaries');

    // The backend now returns a List[DiarySummaryResponse] which matches ArtifactSummary[]
    const items = await response.json();
    return { items: items.slice(0, limit) };
  },

  async searchDiaries(userId: string, query: string): Promise<ArtifactSummary[]> {
    const response = await fetch(`${API_BASE_URL}/diary/search?user_id=${userId}&query=${encodeURIComponent(query)}`);
    if (!response.ok) throw new Error('Failed to search diaries');
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
  },

  async updateUser(userId: string, data: any): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) throw new Error('Failed to update user');
    return response.json();
  },

  async deleteUser(userId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete user');
    return response.json();
  },

  async deleteArtifact(artifactId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/artifacts/${artifactId}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete artifact');
    return response.json();
  }
};
