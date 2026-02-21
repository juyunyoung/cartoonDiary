export enum StylePreset {
  CUTE = "cute",
  COMEDY = "comedy",
  DRAMA = "drama",
  MINIMAL = "minimal"
}

export interface GenerationOptions {
  moreFunny: boolean;
  focusEmotion: boolean;
  lessText: boolean;
}

export interface DiaryEntryRequest {
  diaryText: string;
  mood: string;
  stylePreset: StylePreset;
  protagonistName?: string;
  options: GenerationOptions;
}

export enum JobStatus {
  READING_DIARY = "READING_DIARY",
  BUILDING_STORYBOARD = "BUILDING_STORYBOARD",
  GENERATING_IMAGES = "GENERATING_IMAGES",
  COMPOSING_STRIP = "COMPOSING_STRIP",
  DONE = "DONE",
  FAILED = "FAILED"
}

export interface JobResponse {
  jobId: string;
  status: JobStatus;
  step: string;
  progress: number;
  artifactId?: string;
  error?: string;
}

export interface Panel {
  text: string;
  // Add other panel properties as needed
}

export interface Storyboard {
  panels: Panel[];
}

export interface ArtifactResponse {
  artifactId: string;
  finalStripUrl: string;
  panelUrls: string[];
  storyboard: Storyboard;
  stylePreset: string;
  createdAt: string;
  diaryText: string;
}

export interface ArtifactSummary {
  artifactId: string;
  thumbnailUrl: string;
  date: string;
  summary: string;
  stylePreset: string;
}
