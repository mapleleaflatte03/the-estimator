import type {
  ActualsResult,
  BenchmarkReport,
  CalibrationStatus,
  EstimateVersion,
  HistoricalCase,
  ManualEdits,
  Project,
  ReaderEvaluation,
  SampleBrief,
  SipSummary,
  SystemStatus,
} from './types';

const API_BASE = '/api/v1';
const KEY_STORAGE = 'parallax_jev_key';
const WORKSPACE_STORAGE = 'parallax_workspace_v1';

/** Stable anonymous workspace: project briefs and learning stay with this browser. */
function workspaceId(): string {
  let id = localStorage.getItem(WORKSPACE_STORAGE);
  if (!id || !/^[0-9a-f]{32}$/.test(id)) {
    id = crypto.randomUUID().replaceAll('-', '');
    localStorage.setItem(WORKSPACE_STORAGE, id);
  }
  return id;
}

/** The visitor's own Jev key: kept in this browser tab only and sent with requests that read briefs. */
export const visitorKey = {
  get: () => sessionStorage.getItem(KEY_STORAGE) ?? '',
  set: (k: string) => (k.trim() ? sessionStorage.setItem(KEY_STORAGE, k.trim()) : sessionStorage.removeItem(KEY_STORAGE)),
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export let lastVisitorCredits: number | null = null;

function uiLang(): 'en' | 'vi' {
  try {
    return localStorage.getItem('parallax_lang') === 'vi' ? 'vi' : 'en';
  } catch {
    return 'en';
  }
}

async function request<T>(url: string, init?: RequestInit, fallbackError = 'Request failed'): Promise<T> {
  const key = visitorKey.get();
  // Only requests that may read a brief carry the key.
  const reads = /\/projects\/[^/]+\/(?:estimate|wbs|clarify)$/.test(url);
  const headers: Record<string, string> = {
    'Accept-Language': uiLang(),
    'X-Parallax-Workspace': workspaceId(),
    ...(init?.headers as Record<string, string> | undefined),
  };
  if (key && reads) headers['X-Jev-Key'] = key;
  const res = await fetch(url, { ...init, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: fallbackError }));
    throw new ApiError(typeof err.detail === 'string' ? err.detail : fallbackError, res.status);
  }
  const credits = res.headers.get('X-Jev-Credits-Remaining');
  if (credits != null) lastVisitorCredits = Number(credits);
  return res.json();
}

const postJson = (body: unknown): RequestInit => ({
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
});

export const fetchProjects = () => request<Project[]>(`${API_BASE}/projects`, undefined, 'Failed to fetch projects');

export const createProject = (payload: {
  title: string;
  project_type: string;
  brief_text: string;
  documents?: Record<string, string>;
}) => request<Project>(`${API_BASE}/projects`, postJson(payload), 'Failed to create project');

export const estimateProject = (projectId: string) =>
  request<EstimateVersion>(`${API_BASE}/projects/${projectId}/estimate`, { method: 'POST' }, 'Failed to generate estimate');

export const fetchVersions = (projectId: string) =>
  request<EstimateVersion[]>(`${API_BASE}/projects/${projectId}/versions`, undefined, 'Failed to fetch versions');

export const answerClarification = (projectId: string, questionId: string, answer: boolean, notes?: string) =>
  request<EstimateVersion>(
    `${API_BASE}/projects/${projectId}/clarify`,
    postJson({ question_id: questionId, answer, notes }),
    'Failed to answer clarification',
  );

export const recordActuals = (
  projectId: string,
  actualHours: number,
  deviationReasons?: string[],
  requirementActuals?: Record<string, number>,
) =>
  request<ActualsResult>(
    `${API_BASE}/projects/${projectId}/actuals`,
    postJson({ actual_hours: actualHours, deviation_reasons: deviationReasons, requirement_actuals: requirementActuals }),
    'Failed to record actuals',
  );

export const fetchHistoricalCases = (domain?: string) =>
  request<HistoricalCase[]>(
    domain ? `${API_BASE}/historical-cases?domain=${encodeURIComponent(domain)}` : `${API_BASE}/historical-cases`,
    undefined,
    'Failed to fetch completed projects',
  );

export const runBenchmark = () =>
  request<BenchmarkReport>(`${API_BASE}/benchmark/run`, { method: 'POST' }, 'Failed to run benchmark');

export const fetchSystemStatus = () => request<SystemStatus>(`${API_BASE}/system/status`, undefined, 'Status unavailable');

export const fetchSampleBriefs = () => request<SampleBrief[]>(`${API_BASE}/sample-briefs`, undefined, 'Samples unavailable');

export const fetchCalibration = () =>
  request<CalibrationStatus>(`${API_BASE}/calibration`, undefined, 'Calibration unavailable');

export const fetchSipSummary = () => request<SipSummary>(`${API_BASE}/datasets/sip`, undefined, 'Dataset unavailable');

export const updateWbs = (projectId: string, edits: ManualEdits) =>
  request<EstimateVersion>(
    `${API_BASE}/projects/${projectId}/wbs`,
    { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(edits) },
    'Failed to save edits',
  );

export const proposalUrl = (
  projectId: string,
  p: { confidence: number; rate: number; currency: string; people: number; lang: 'en' | 'vi' },
) =>
  `${API_BASE}/projects/${projectId}/export/proposal.md?` +
  new URLSearchParams({
    confidence: String(p.confidence),
    rate: String(p.rate),
    currency: p.currency,
    people: String(p.people),
    lang: p.lang,
  }).toString();

export const wbsCsvUrl = (projectId: string, lang: 'en' | 'vi') =>
  `${API_BASE}/projects/${projectId}/export/wbs.csv?lang=${lang}`;

export const fetchReaderEvaluation = () =>
  request<ReaderEvaluation>(`${API_BASE}/reader/evaluation`, undefined, 'Evaluation unavailable');
