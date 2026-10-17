import type { ManualEdits } from './types';

const STORAGE_KEY = 'parallax_last_project_v1';

export interface SavedActuals {
  hours: number;
  reasons: string[];
  perRequirement?: Record<string, number>;
}

export interface SavedAnswer {
  question_id: string;
  answer: boolean;
}

/** Last project this browser estimated. Survives a free-host restart that wipes the server disk. */
export interface SavedProject {
  title: string;
  project_type: string;
  brief_text: string;
  documents?: Record<string, string>;
  server_project_id: string;
  answers: SavedAnswer[];
  edits: ManualEdits | null;
  actuals: SavedActuals | null;
  saved_at: string;
}

export function loadSavedProject(): SavedProject | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as SavedProject;
    if (!parsed.brief_text || !parsed.title || !parsed.server_project_id) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function saveProject(project: SavedProject): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(project));
}
