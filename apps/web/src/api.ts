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

async function request<T>(url: string, init?: RequestInit, fallbackError = 'Request failed'): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: fallbackError }));
    throw new Error(typeof err.detail === 'string' ? err.detail : fallbackError);
  }
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

export const proposalUrl = (projectId: string, p: { confidence: number; rate: number; currency: string; people: number }) =>
  `${API_BASE}/projects/${projectId}/export/proposal.md?` +
  new URLSearchParams({
    confidence: String(p.confidence),
    rate: String(p.rate),
    currency: p.currency,
    people: String(p.people),
  }).toString();

export const wbsCsvUrl = (projectId: string) => `${API_BASE}/projects/${projectId}/export/wbs.csv`;

export const fetchReaderEvaluation = () =>
  request<ReaderEvaluation>(`${API_BASE}/reader/evaluation`, undefined, 'Evaluation unavailable');
