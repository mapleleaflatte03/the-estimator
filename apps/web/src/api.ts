import type {
  BenchmarkMetrics,
  EstimateVersion,
  HistoricalCase,
  Project,
} from './types';

const API_BASE = '/api/v1';

export async function fetchProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error('Failed to fetch projects');
  return res.json();
}

export async function createProject(payload: {
  title: string;
  project_type: string;
  brief_text: string;
  documents?: Record<string, string>;
}): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Creation failed' }));
    throw new Error(err.detail || 'Failed to create project');
  }
  return res.json();
}

export async function estimateProject(projectId: string): Promise<EstimateVersion> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/estimate`, {
    method: 'POST',
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Estimation failed' }));
    throw new Error(err.detail || 'Failed to generate estimate');
  }
  return res.json();
}

export async function fetchVersions(projectId: string): Promise<EstimateVersion[]> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/versions`);
  if (!res.ok) throw new Error('Failed to fetch versions');
  return res.json();
}

export async function answerClarification(
  projectId: string,
  questionId: string,
  answer: boolean,
  notes?: string
): Promise<EstimateVersion> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/clarify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question_id: questionId, answer, notes }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Clarification failed' }));
    throw new Error(err.detail || 'Failed to answer clarification');
  }
  return res.json();
}

export async function recordActuals(
  projectId: string,
  actualHours: number,
  deviationReasons?: string[]
): Promise<{
  actual_id: string;
  project_id: string;
  baseline_version_id: string;
  estimated_p50: number;
  actual_hours: number;
  delta_hours: number;
  percentage_error: number;
  inside_p10_p90: boolean;
}> {
  const res = await fetch(`${API_BASE}/projects/${projectId}/actuals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      actual_hours: actualHours,
      deviation_reasons: deviationReasons,
    }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Actuals recording failed' }));
    throw new Error(err.detail || 'Failed to record actuals');
  }
  return res.json();
}

export async function fetchHistoricalCases(domain?: string): Promise<HistoricalCase[]> {
  const url = domain ? `${API_BASE}/historical-cases?domain=${domain}` : `${API_BASE}/historical-cases`;
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch historical cases');
  return res.json();
}

export async function runBenchmark(): Promise<BenchmarkMetrics> {
  const res = await fetch(`${API_BASE}/benchmark/run`, { method: 'POST' });
  if (!res.ok) throw new Error('Failed to run benchmark');
  return res.json();
}
