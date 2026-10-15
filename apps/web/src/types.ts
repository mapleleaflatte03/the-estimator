export type VerificationStatus = 'confirmed' | 'assumed' | 'missing';

export interface EvidenceSpan {
  source_doc: string;
  quote: string;
  location?: string | null;
}

export interface RequirementNode {
  req_id: string;
  title: string;
  description: string;
  status: VerificationStatus;
  evidence: EvidenceSpan[];
}

export interface WorkItem {
  item_id: string;
  req_ids: string[];
  name: string;
  role: string;
  dependencies: string[];
  optimistic_hours: number;
  most_likely_hours: number;
  pessimistic_hours: number;
  assumption_id?: string | null;
}

export interface CriticFinding {
  finding_id: string;
  category: string;
  claim: string;
  verified_by_evidence: boolean;
  supporting_evidence: EvidenceSpan[];
  action_taken: string;
}

export interface ClarificationQuestion {
  question_id: string;
  assumption_id: string;
  question_text: string;
  context_reason: string;
  hours_if_false: number;
  hours_if_true: number;
  prior_probability?: number | null;
  sensitivity_spread_hours?: number;
}

export interface ProbabilisticForecast {
  p10_hours: number;
  p50_hours: number;
  p80_hours: number;
  p90_hours: number;
  mean_hours: number;
  std_hours: number;
  bottom_up_p50: number;
  reference_class_p50?: number | null;
  divergence_warning?: string | null;
  insufficient_historical_evidence: boolean;
}

export interface EstimateVersion {
  version_id: string;
  project_id: string;
  parent_version_id?: string | null;
  created_at: string;
  model_tag: string;
  requirements: RequirementNode[];
  wbs: WorkItem[];
  critic_findings: CriticFinding[];
  clarifications: ClarificationQuestion[];
  forecast: ProbabilisticForecast;
}

export interface Project {
  project_id: string;
  title: string;
  project_type: string;
  brief_text: string;
  documents: Record<string, string>;
  created_at: string;
  status: string;
  current_version_id?: string | null;
}

export interface HistoricalCase {
  case_id: string;
  title: string;
  domain: string;
  actual_hours: number;
  task_count: number;
  complexity_score: number;
  tags: string[];
  notes?: string | null;
}

export interface BenchmarkMetrics {
  model_name: string;
  split: string;
  n_cases: number;
  mae: number;
  mdape: number;
  wape: number;
  pred_25: number;
  interval_coverage: number;
  mean_interval_width: number;
}
