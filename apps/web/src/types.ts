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
  components?: string[];
  in_scope?: boolean;
  ai_reading?: {
    kind: string;
    confidence: number;
    tentative: number;
    model: string;
    added_component?: string | null;
    suggested_component?: string | null;
    flagged_tentative: boolean;
    overrun?: number | null;
    dropped_components?: string[];
  } | null;
  estimated_hours_raw?: number | null;
  risk_group?: number | null;
  adjustment_factor?: number | null;
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
  basis?: string | null;
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
  sensitivity_spread_hours: number;
  affected_item_ids: string[];
  evidence: EvidenceSpan[];
  current_assumption: boolean;
  answer?: boolean | null;
}

export interface HistogramBin {
  start: number;
  end: number;
  share: number;
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
  calibration_multiplier: number;
  uncalibrated_p50_hours?: number | null;
  uncertainty_source?: string | null;
  n_simulations?: number | null;
  percentile_curve: [number, number][];
  histogram: HistogramBin[];
  p99_hours?: number | null;
  max_hours?: number | null;
  tail_start_hours?: number | null;
  critical_path_hours?: number | null;
  critical_path_ids?: string[];
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
  clarification_answers: Record<string, boolean>;
  reader?: string;
  reader_model?: string | null;
  manual_edits?: ManualEdits;
}

export interface ManualEdits {
  overrides?: Record<string, { name?: string; hours?: number }>;
  removed?: string[];
  added?: { name: string; hours: number; req_id?: string; role?: string; item_id?: string }[];
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
  estimated_p50_hours?: number | null;
  completed_at?: string | null;
  tags: string[];
  notes?: string | null;
}

export interface Metrics {
  n_cases: number;
  mae: number;
  mdape: number;
  wape: number;
  pred_25: number;
  interval_coverage: number | null;
  mean_interval_width: number | null;
}

export interface DatasetInfo {
  name: string;
  publisher: string;
  source_url: string;
  source_commit: string;
  paper: string;
  license: string;
  n_tasks: number;
  period: string;
}

export interface LearningCurvePoint {
  year: number;
  n_history: number;
  n_test: number;
  baseline_mae: number;
  frozen_mae: number;
  rolling_mae: number;
  baseline_pred_25: number;
  rolling_pred_25: number;
  frozen_coverage: number;
  rolling_coverage: number;
}

export interface InAppEvaluation {
  n_observations: number;
  multiplier: number;
  status: 'ok' | 'insufficient_data';
  message?: string;
  uncalibrated_mae?: number;
  calibrated_mae?: number;
  uncalibrated_mdape?: number;
  calibrated_mdape?: number;
  improved?: boolean;
}

export interface BenchmarkReport {
  run_id: string;
  created_at: string;
  sip: {
    dataset: DatasetInfo;
    method: string;
    holdout: {
      train_period: string;
      test_period: string;
      n_train: number;
      n_test: number;
      baseline: Metrics;
      calibrated: Metrics;
    };
    holdout_by_bucket: {
      bucket: string;
      n_test: number;
      baseline_mae: number;
      calibrated_mae: number;
      calibrated_coverage: number;
      train_ratio_p50: number;
    }[];
    learning_curve: { frozen_after_year: number; points: LearningCurvePoint[] };
    aggregate_level: {
      n_aggregates: number;
      n_train: number;
      n_test: number;
      note: string;
      baseline?: Metrics;
      calibrated?: Metrics;
    };
  };
  in_app: InAppEvaluation;
}

export interface CalibrationStatus {
  multiplier: number;
  n_observations: number;
  prior_strength: number;
  updated_at?: string | null;
  observations: {
    project_id: string;
    project_type: string;
    version_id: string;
    uncalibrated_p50: number;
    actual_hours: number;
    ratio: number;
    recorded_at: string;
  }[];
}

export interface ActualsResult {
  actual_id: string;
  project_id: string;
  baseline_version_id: string;
  estimated_p50: number;
  estimated_p10: number;
  estimated_p90: number;
  actual_hours: number;
  delta_hours: number;
  percentage_error: number;
  inside_p10_p90: boolean;
  initial_version: {
    version_id: string;
    estimated_p50: number;
    percentage_error: number;
    inside_p10_p90: boolean;
  };
  calibration: {
    multiplier_before: number;
    multiplier_after: number;
    n_observations: number;
    prior_strength: number;
    applies_to: string;
    project_type: string;
    type_multiplier_before: number;
    type_multiplier_after: number;
    type_observations: number;
    range_level_before?: number;
    range_level_after?: number;
    range_hits?: number;
    range_checks?: number;
  };
  learning?: { requirements_recorded: number; before: Learning; after: Learning };
}

export interface Learning {
  question: string | null;
  thresholds: number[] | null;
  sip_factors: number[] | null;
  sip_train_counts: number[] | null;
  sip_test_ratio_p50: (number | null)[] | null;
  group_factors: number[];
  group_observations: number[];
  component_factors: Record<string, number>;
  component_observations: Record<string, number>;
}

export interface SipStudyMetrics {
  n: number;
  mae: number;
  mdape: number;
  pred_25: number;
  coverage_p10_p90: number | null;
}

export interface SipStudy {
  pilot: {
    seed: number;
    size: number;
    chosen: string;
    reason: string;
    candidates: { question: string; n: number; spearman_log_ratio: number; auc_overrun_25pct: number; mean_p: number }[];
  };
  report?: {
    question: string;
    population: string;
    train: string;
    test: string;
    thresholds_from_train: number[];
    groups_train: { group: number; n_train: number; ratio_p10: number; ratio_p50: number; ratio_p90: number }[];
    groups_test: { group: number; n_test: number; test_ratio_p50: number }[];
    spearman_test: number;
    auc_overrun_25pct_test: number;
    human_estimate: SipStudyMetrics;
    calibrated_size_only: SipStudyMetrics;
    calibrated_with_jev: SipStudyMetrics;
    mae_gain_vs_size_only_h: number;
    mae_gain_95ci_h: number[];
  };
}

export interface JevKeyStatus {
  name: string;
  provider: string;
  credits: number | null;
  calls: number;
  charged: number;
  cooling_down: boolean;
  last_error: string | null;
}

export interface ReaderStatus {
  configured: boolean;
  provider: string | null;
  model?: string;
  available: boolean;
  credits_remaining: number | null;
  cached_clauses: number;
  keys_total?: number;
  keys_usable?: number;
  keys?: JevKeyStatus[];
  questions?: string[];
  halted?: string | null;
  required?: boolean;
}

export interface ReaderSummary {
  reader: 'rules' | 'jev' | 'hybrid' | 'shipped';
  n_clauses: number;
  primary_kind_found: number;
  kind_recall_pct: number;
  kind_precision_pct: number;
  tentative_correct: number;
  tentative_caught: string;
  false_tentative: number;
  primary_kind_suggested_as_question?: number;
}

export interface JournalEntry {
  date: string;
  tag: string;
  labels: string;
  rules_version: string;
  model: string | null;
  note: string;
  summary: (Partial<ReaderSummary> & Record<string, unknown>)[];
}

export interface FeedbackSummary {
  answered: number;
  accepted: number;
  by_component: { component: string; answered: number; accepted: number; acceptance: number; muted: boolean }[];
}

export interface ReaderEvaluation {
  held_out?: { note?: string; model: string; summary: ReaderSummary[] };
  latest?: { model: string; summary: ReaderSummary[] };
  status: ReaderStatus;
  feedback?: FeedbackSummary;
  journal?: JournalEntry[];
  sip_study?: SipStudy | null;
  learning?: Learning;
  itemlet_replication?: {
    n_read: number;
    n_population: number;
    projects: number;
    groups: { group: number; n: number; ratio_p50: number | null; share_overrun_25pct: number | null }[];
    high_vs_low_ratio_p50: number | null;
    spearman: number;
    auc_overrun_25pct: number;
    mae_raw_estimate: number;
    mae_with_sip_factors: number;
    mae_gain_95ci: number[];
  } | null;
  conformal?: {
    gamma: number;
    without: ConformalRun;
    with: ConformalRun;
  } | null;
  operational_replay?: {
    all_tasks: Record<'human' | 'frozen' | 'online', ReplayMetrics>;
    dev_tasks_20h_read_by_jev: Record<'human' | 'online' | 'online+jev', ReplayMetrics>;
    by_year: { year: number; n: number; human: number; frozen: number; online: number }[];
  } | null;
}

export interface ConformalRun {
  overall_coverage: number;
  worst_bucket_gap: number;
  mean_width_h: number;
  by_bucket: Record<string, { n: number; coverage: number; mean_width_h: number }>;
}

export interface ReplayMetrics {
  n: number;
  mae: number;
  mdae: number;
  sa: number;
  pred_25: number;
  coverage_p10_p90: number | null;
  wilcoxon_vs_human_p?: number | null;
  effect_vs_human?: number | null;
}

export interface SystemStatus {
  model_tag: string;
  n_simulations: number;
  dataset: {
    available: boolean;
    name?: string;
    n_tasks?: number;
    n_aggregates?: number;
    period?: string;
    license?: string;
    error?: string;
  };
  calibration: { multiplier: number; n_observations: number };
  reference_class_projects: number;
  ai_reader?: ReaderStatus;
  learning?: Learning & { requirement_observations: number };
  last_benchmark: {
    run_id: string;
    created_at: string;
    metrics: Record<string, number>;
  } | null;
}

export interface SampleBrief {
  id: string;
  title: string;
  project_type: string;
  brief_text: string;
}

export interface SipSummary extends Omit<DatasetInfo, 'n_tasks'> {
  n_tasks: number;
  n_projects: number;
  share_exact_estimates: number;
  task_ratio_quantiles: Record<string, number>;
  aggregate_ratio_quantiles: Record<string, number>;
  n_aggregates: number;
  categories: {
    category: string;
    subcategory: string;
    n_tasks: number;
    median_estimate: number;
    median_actual: number;
    median_ratio: number;
    share_underestimated: number;
  }[];
  aggregates: {
    aggregate_id: string;
    n_tasks: number;
    estimate_hours: number;
    actual_hours: number;
    ratio: number;
    first_estimated_on: string;
    last_estimated_on: string;
  }[];
}
