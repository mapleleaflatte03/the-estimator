import type { ManualEdits } from './types';

const STORAGE_KEY = 'parallax_projects_v2';
const LEGACY_KEY = 'parallax_last_project_v1';

export interface SavedActuals {
  hours: number;
  reasons: string[];
  perRequirement?: Record<string, number>;
}

export interface SavedAnswer {
  question_id: string;
  answer: boolean;
  notes?: string;
}

/** Browser copy of one project. Survives a free-host restart that wipes the server disk. */
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

function validProject(value: unknown): value is SavedProject {
  if (!value || typeof value !== 'object') return false;
  const p = value as Partial<SavedProject>;
  return typeof p.title === 'string' && typeof p.brief_text === 'string'
    && typeof p.server_project_id === 'string' && !!p.title && !!p.brief_text && !!p.server_project_id;
}

export function loadSavedProjects(): SavedProject[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed: unknown = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed.filter(validProject) : [];
    }
    const legacy = localStorage.getItem(LEGACY_KEY);
    const parsed: unknown = legacy ? JSON.parse(legacy) : null;
    return validProject(parsed) ? [parsed] : [];
  } catch {
    return [];
  }
}

export function loadSavedProject(projectId: string): SavedProject | null {
  return loadSavedProjects().find((p) => p.server_project_id === projectId) ?? null;
}

export function saveProject(project: SavedProject): boolean {
  try {
    const other = loadSavedProjects().filter((p) => p.server_project_id !== project.server_project_id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([project, ...other]));
    return true;
  } catch {
    return false;
  }
}

export function replaceSavedProject(oldId: string, project: SavedProject): boolean {
  try {
    const other = loadSavedProjects().filter((p) => p.server_project_id !== oldId && p.server_project_id !== project.server_project_id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify([project, ...other]));
    return true;
  } catch {
    return false;
  }
}
