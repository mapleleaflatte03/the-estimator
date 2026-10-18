import React, { useEffect, useState } from 'react';
import { CheckCircle2, Gauge, KeyRound, RotateCcw, Sparkles, TrendingDown } from 'lucide-react';
import type { BenchmarkReport, JournalEntry, ReaderEvaluation, ReaderSummary } from '../types';
import { fetchReaderEvaluation } from '../api';
import { useI18n } from '../i18n';
import { card } from '../ui';
import { GroupedBars } from './charts';
import { TONE, type Tone } from './tone';

interface EvidenceScreenProps {
  onRunBenchmark: () => Promise<BenchmarkReport>;
}

const frac = (s?: string | null): [number, number] => {
  const [a, b] = String(s ?? '0/0').split('/').map(Number);
  return [a || 0, b || 0];
};
const find = (j: JournalEntry[], tag: string) => [...j].reverse().find((e) => e.tag === tag);
const reader = (rows: Partial<ReaderSummary>[] | undefined, name: string) => {
  if (name !== 'shipped') return rows?.find((r) => r.reader === name);
  // "Shipped" = the reader the app used when that round ran (later rounds add verification steps).
  for (const n of ['shipped+verify+add', 'shipped+verify', 'shipped']) {
    const row = rows?.find((r) => String(r.reader) === n);
    if (row) return row;
  }
  return undefined;
};
const promise = (e: JournalEntry | undefined) =>
  (e?.summary?.[0]?.test_odd_projects ?? null) as null | Record<string, number | string>;

type Say = (vi: string, en: string) => string;

/** One-line result of a journal entry, in the same words as the charts. */
const resultText = (e: JournalEntry, t: Say, pct: (v: unknown) => string): string => {
  const odd = promise(e);
  if (odd) return t(
    `giữ lại ${pct(odd.retention_pct)} · hiệu năng ${pct(odd.performance_recall_pct)} · bảo mật ${pct(odd.security_recall_pct)}`,
    `kept ${pct(odd.retention_pct)} · performance ${pct(odd.performance_recall_pct)} · security ${pct(odd.security_recall_pct)}`,
  );
  const first = e.summary?.[0];
  if (first && 'spearman_log_ratio' in first)
    return e.summary.map((s) => `${String(s.question).split('@')[0]} ρ=${s.spearman_log_ratio}`).join(' · ');
  const jevRow = e.summary?.find((s) => String(s.reader ?? '').startsWith('jev:'));
  const sizeRow = e.summary?.find((s) => String(s.reader) === 'size-only');
  if (jevRow && sizeRow) return t(
    `sai lệch ${sizeRow.mae} → ${jevRow.mae} giờ · PRED(25) ${sizeRow.pred_25}% → ${jevRow.pred_25}%`,
    `error ${sizeRow.mae} → ${jevRow.mae} hours · PRED(25) ${sizeRow.pred_25}% → ${jevRow.pred_25}%`,
  );
  if (first && 'mae_change_pct' in first) return t(
    `sai lệch ${String(first.mae_change_pct).replace('.', ',')}% (${first.baseline_mae} → ${first.calibrated_mae} giờ)`,
    `error ${first.mae_change_pct}% (${first.baseline_mae} → ${first.calibrated_mae} hours)`,
  );
  if (first && 'retention_pct' in first) return t(`giữ lại ${pct(first.retention_pct)}`, `kept ${pct(first.retention_pct)}`);
  const r = reader(e.summary, 'shipped') ?? reader(e.summary, 'rules');
  if (!r) return '';
  const who = r.reader === 'shipped' ? t('Luật + AI', 'Rules + AI') : t('Chỉ luật', 'Rules only');
  return t(
    `${who}: loại việc ${r.primary_kind_found}/${r.n_clauses} · chưa chốt ${r.tentative_caught}`,
    `${who}: kind of work ${r.primary_kind_found}/${r.n_clauses} · uncommitted ${r.tentative_caught}`,
  );
};

const Kpi: React.FC<{ tone: Tone; icon: React.ReactNode; value: string; label: string; sub: string }> = ({ tone, icon, value, label, sub }) => (
  <div className={`p-5 rounded-2xl border-2 ${TONE[tone].soft} border-current/10`}>
    <div className={`flex items-center gap-1.5 text-xs font-bold uppercase tracking-wide ${TONE[tone].text}`}>
      {icon} {label}
    </div>
    <div className="text-4xl font-extrabold tracking-tight text-slate-900 dark:text-white mt-1">{value}</div>
    <div className="text-sm text-slate-700 dark:text-slate-300 mt-1">{sub}</div>
  </div>
);

export const EvidenceScreen: React.FC<EvidenceScreenProps> = ({ onRunBenchmark }) => {
  const { locale, t, pct, hours1, kinds, risks } = useI18n();
  const [ev, setEv] = useState<ReaderEvaluation | null>(null);
  const [bench, setBench] = useState<BenchmarkReport | null>(null);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchReaderEvaluation()
      .then(setEv)
      .catch((err) => setError((err as Error).message));
  }, []);

  const runBench = async () => {
    setRunning(true);
    try {
      setBench(await onRunBenchmark());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setRunning(false);
    }
  };

  if (!ev) {
    return <div className="max-w-5xl mx-auto text-slate-600 dark:text-slate-400">{error ?? t('Đang tải kết quả kiểm thử…', 'Loading the measured results…')}</div>;
  }
  const journal = ev.journal ?? [];
  const r1 = ev.held_out?.summary;
  const r2 = find(journal, 'round2')?.summary;
  const r4 = find(journal, 'round4_heldout')?.summary;
  const r5 = find(journal, 'round5_heldout')?.summary;
  const r6 = find(journal, 'round6_heldout')?.summary;
  const r7 = find(journal, 'round7_heldout')?.summary;
  const r8 = find(journal, 'round8_heldout')?.summary;
  const roundLabel = (n: string, clauses: number, note = '') => t(
    `Vòng ${n}${note} · ${clauses} câu`,
    `Round ${n}${note} · ${clauses} clauses`,
  );
  const rounds = [
    { key: 'r1', label: roundLabel('1', reader(r1, 'rules')?.n_clauses ?? 0), rows: r1 },
    { key: 'r2', label: roundLabel('2', reader(r2, 'rules')?.n_clauses ?? 0), rows: r2 },
    { key: 'r4', label: roundLabel('4', reader(r4, 'rules')?.n_clauses ?? 0), rows: r4 },
    { key: 'r5', label: roundLabel('5', reader(r5, 'rules')?.n_clauses ?? 0), rows: r5 },
    { key: 'r6', label: roundLabel('6', reader(r6, 'rules')?.n_clauses ?? 0, t(' · quỹ đầu tư', ' · private equity')), rows: r6 },
    { key: 'r7', label: roundLabel('7', reader(r7, 'rules')?.n_clauses ?? 0), rows: r7 },
    { key: 'r8', label: roundLabel('8', reader(r8, 'rules')?.n_clauses ?? 0, t(' (mới nhất)', ' (latest)')), rows: r8 },
  ].filter((r) => r.rows);

  const tentTotals = (name: string) =>
    rounds.reduce<[number, number]>((acc, r) => {
      const [a, b] = frac(reader(r.rows, name)?.tentative_caught as string);
      return [acc[0] + a, acc[1] + b];
    }, [0, 0]);
  const [tRules, tAll] = tentTotals('rules');
  const [tShip] = tentTotals('shipped');

  const r3Before = find(journal, 'round3_rules_before')?.summary?.[0];
  const r3After = find(journal, 'round3_rules_after_english')?.summary?.[0] ?? find(journal, 'round3_rules_after')?.summary?.[0];
  const pBefore = promise(find(journal, 'promise_split_before'));
  const pAfter = promise(find(journal, 'promise_split_after'));
  const ratio = (a: number, b: number) => (b ? a / b : 0);

  const improvement = [
    r3Before && r3After && {
      key: 'r3k',
      label: t(
        `Tiếng Việt, câu mới (vòng 3 · ${r3After.n_clauses} câu): đúng loại việc chính`,
        `Vietnamese, new clauses (round 3 · ${r3After.n_clauses} clauses): main kind of work correct`,
      ),
      values: [
        { series: 'before', value: ratio(r3Before.primary_kind_found ?? 0, r3Before.n_clauses ?? 1), display: `${r3Before.primary_kind_found}/${r3Before.n_clauses}` },
        { series: 'after', value: ratio(r3After.primary_kind_found ?? 0, r3After.n_clauses ?? 1), display: `${r3After.primary_kind_found}/${r3After.n_clauses}` },
      ],
    },
    pBefore && pAfter && {
      key: 'pret',
      label: t(
        `Tiếng Anh thật (PROMISE · ${pAfter.n_requirements} yêu cầu): giữ lại đủ yêu cầu`,
        `Real English (PROMISE · ${pAfter.n_requirements} requirements): requirements kept`,
      ),
      values: [
        { series: 'before', value: Number(pBefore.retention_pct) / 100, display: pct(pBefore.retention_pct) },
        { series: 'after', value: Number(pAfter.retention_pct) / 100, display: pct(pAfter.retention_pct) },
      ],
    },
    pBefore && pAfter && {
      key: 'pperf',
      label: t('PROMISE: nhận ra yêu cầu hiệu năng', 'PROMISE: performance requirements recognised'),
      values: [
        { series: 'before', value: Number(pBefore.performance_recall_pct) / 100, display: pct(pBefore.performance_recall_pct) },
        { series: 'after', value: Number(pAfter.performance_recall_pct) / 100, display: pct(pAfter.performance_recall_pct) },
      ],
    },
    pBefore && pAfter && {
      key: 'psec',
      label: t('PROMISE: nhận ra yêu cầu bảo mật', 'PROMISE: security requirements recognised'),
      values: [
        { series: 'before', value: Number(pBefore.security_recall_pct) / 100, display: pct(pBefore.security_recall_pct) },
        { series: 'after', value: Number(pAfter.security_recall_pct) / 100, display: pct(pAfter.security_recall_pct) },
      ],
    },
  ].filter(Boolean) as { key: string; label: string; values: { series: string; value: number; display: string }[] }[];

  const holdout = bench?.sip.holdout;
  const sip = find(journal, 'sip_holdout')?.summary?.[0] as undefined | Record<string, number | string>;
  const r4All = find(journal, 'round4_rules_before')?.summary;
  const labelledClauses = [r1, r2, r3After ? [r3After] : undefined, r4All, r5, r6, r7, r8].reduce((s, rows) => s + Number(reader(rows, 'rules')?.n_clauses ?? 0), 0);
  const fb = ev.feedback;
  const study = ev.sip_study;
  const rep = study?.report;
  const st = ev.status;
  const replay = ev.operational_replay;
  const conf = ev.conformal;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">{t('Kiểm chứng bằng dữ liệu thật', 'Measured on real data')}</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          {t('Mỗi vòng thử dùng câu mới, đáp án gán tay ', 'Each round uses new clauses, labelled by hand ')}
          <strong>{t('trước', 'before')}</strong>
          {t(' khi chạy. Phần dùng để sửa luật được tách riêng với phần dùng để chấm.', ' the run. The clauses used to change the rules are kept apart from the clauses used to score them.')}
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi
          tone="ai"
          icon={<Sparkles className="w-4 h-4" />}
          label={t('AI nhận ra yêu cầu chưa chốt', 'AI catches uncommitted scope')}
          value={`${tShip}/${tAll}`}
          sub={t(
            `Chỉ dùng luật: ${tRules}/${tAll}. Không báo nhầm câu nào.`,
            `Rules only: ${tRules}/${tAll}. No false alarms.`,
          )}
        />
        {replay && (
          <Kpi
            tone="good"
            icon={<Gauge className="w-4 h-4" />}
            label={t('Vận hành thật 2011–2014', 'Production replay 2011–2014')}
            value={`${pct(replay.all_tasks.online.sa)}`}
            sub={t(
              `Độ chính xác so với đoán ngẫu nhiên; ước lượng của lập trình viên: ${pct(replay.all_tasks.human.sa)} (${replay.all_tasks.human.n.toLocaleString(locale)} việc).`,
              `Accuracy against a random guess; the developers' own estimates: ${pct(replay.all_tasks.human.sa)} (${replay.all_tasks.human.n.toLocaleString(locale)} tasks).`,
            )}
          />
        )}
        {sip && (
          <Kpi
            tone="good"
            icon={<TrendingDown className="w-4 h-4" />}
            label={t('Học từ giờ thực tế', 'Learning from actual hours')}
            value={pct(sip.mae_change_pct)}
            sub={t(
              `Sai lệch trung bình trên ${Number(sip.n_test).toLocaleString(locale)} công việc thật chưa từng thấy (SiP 2011–2014).`,
              `Mean error on ${Number(sip.n_test).toLocaleString(locale)} real tasks the model had not seen (SiP 2011–2014).`,
            )}
          />
        )}
        {pBefore && pAfter && (
          <Kpi
            tone="primary"
            icon={<CheckCircle2 className="w-4 h-4" />}
            label={t('Yêu cầu tiếng Anh được giữ lại', 'English requirements kept')}
            value={pct(pAfter.retention_pct)}
            sub={t(
              `Trước khi sửa luật: ${pct(pBefore.retention_pct)} (PROMISE, phần dữ liệu chấm).`,
              `Before the rule change: ${pct(pBefore.retention_pct)} (PROMISE, the scored split).`,
            )}
          />
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className={`${card} p-6 space-y-4`}>
          <h2 className="text-lg font-bold">{t('Nhận ra yêu cầu khách chưa chốt', 'Catching scope the client has not committed')}</h2>
          <GroupedBars
            series={[
              { key: 'rules', label: t('Chỉ luật', 'Rules only'), tone: 'muted' },
              { key: 'shipped', label: t('Luật + AI (đang dùng)', 'Rules + AI (in use)'), tone: 'ai' },
            ]}
            groups={rounds.map((r) => ({
              key: r.key,
              label: r.label,
              values: ['rules', 'shipped'].map((name) => {
                const [a, b] = frac(reader(r.rows, name)?.tentative_caught as string);
                return { series: name, value: ratio(a, b), display: `${a}/${b}` };
              }),
            }))}
          />
        </section>
        <section className={`${card} p-6 space-y-4`}>
          <h2 className="text-lg font-bold">{t('Đúng loại việc chính', 'Main kind of work correct')}</h2>
          <GroupedBars
            series={[
              { key: 'rules', label: t('Chỉ luật', 'Rules only'), tone: 'muted' },
              { key: 'jev', label: t('Chỉ AI', 'AI only'), tone: 'attention' },
              { key: 'shipped', label: t('Luật + AI (đang dùng)', 'Rules + AI (in use)'), tone: 'ai' },
            ]}
            groups={rounds.map((r) => ({
              key: r.key,
              label: r.label,
              values: ['rules', 'jev', 'shipped'].map((name) => {
                const x = reader(r.rows, name);
                const n = x?.n_clauses ?? 1;
                return { series: name, value: ratio(x?.primary_kind_found ?? 0, n), display: `${x?.primary_kind_found ?? 0}/${n}` };
              }),
            }))}
          />
          <p className="text-xs text-slate-600 dark:text-slate-400">
            {t(
              'Khi AI thấy loại việc mà luật bỏ sót, app hỏi bạn thay vì tự cộng giờ, nên số ở đây chưa tính các gợi ý được bạn chấp nhận.',
              'When the AI sees a kind of work the rules missed, the app asks you instead of adding hours, so these counts do not include suggestions you accepted.',
            )}
          </p>
        </section>
      </div>

      {rep && study && (
        <section className={`${card} p-6 space-y-5`}>
          <div>
            <h2 className="text-lg font-bold">{t('AI đọc công việc thật: việc nào sẽ tốn hơn vẻ ngoài?', 'The AI reads real tasks: which ones take longer than they look?')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {t(
                `Jev đọc mô tả của ${rep.groups_train.reduce((s, g) => s + g.n_train, 0) + rep.groups_test.reduce((s, g) => s + g.n_test, 0)} công việc lập trình thật (SiP, ước tính từ 20 giờ trở lên) và trả lời đúng câu hỏi app đặt cho mỗi câu trong mô tả của khách: `,
                `Jev read the descriptions of ${rep.groups_train.reduce((s, g) => s + g.n_train, 0) + rep.groups_test.reduce((s, g) => s + g.n_test, 0)} real programming tasks (SiP, estimates of 20 hours or more) and answered the same question the app asks of every clause in a client brief: `,
              )}
              <em>{t('“người làm lâu năm có thấy việc này sẽ tốn thời gian hơn vẻ ngoài không?”', '“would someone experienced expect this to take longer than it looks?”')}</em>
              {t(
                '. Ngưỡng chia nhóm lấy từ các năm trước 2011; các năm 2011–2014 chỉ dùng để chấm, một lần.',
                ' Group boundaries come from the years before 2011; 2011–2014 were used only to score, once.',
              )}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                {t('Giờ thực tế / giờ ước tính (trung vị) theo đánh giá của AI', 'Actual hours / estimated hours (median), by the AI’s rating')}
              </div>
              <GroupedBars
                series={[
                  { key: 'train', label: t('Năm trước (để học)', 'Earlier years (used to learn)'), tone: 'muted' },
                  { key: 'test', label: t('Năm sau (chưa từng thấy)', 'Later years (never seen)'), tone: 'ai' },
                ]}
                groups={[0, 1, 2].map((g) => {
                  const tr = rep.groups_train.find((x) => x.group === g);
                  const te = rep.groups_test.find((x) => x.group === g);
                  const top = Math.max(...rep.groups_train.map((x) => x.ratio_p50), ...rep.groups_test.map((x) => x.test_ratio_p50));
                  const name = risks[g] ?? '';
                  const label = name ? name.charAt(0).toLocaleUpperCase(locale) + name.slice(1) : String(g);
                  return {
                    key: `g${g}`,
                    label: t(
                      `${label} (${tr?.n_train ?? 0} + ${te?.n_test ?? 0} việc)`,
                      `${label} (${tr?.n_train ?? 0} + ${te?.n_test ?? 0} tasks)`,
                    ),
                    values: [
                      { series: 'train', value: (tr?.ratio_p50 ?? 0) / top, display: `×${(tr?.ratio_p50 ?? 0).toFixed(2)}` },
                      { series: 'test', value: (te?.test_ratio_p50 ?? 0) / top, display: `×${(te?.test_ratio_p50 ?? 0).toFixed(2)}` },
                    ],
                  };
                })}
              />
            </div>
            <div className="space-y-3 text-sm text-slate-700 dark:text-slate-300">
              <p>
                {t('Trên năm chưa từng thấy, thứ tự vẫn giữ nguyên: việc AI đánh giá ', 'On the years it had never seen, the order holds: tasks the AI rates as ')}
                <strong>{risks[2]}</strong>
                {t(' tốn gấp ', ' take ')}
                <strong>
                  {(rep.groups_test[2].test_ratio_p50 / rep.groups_test[0].test_ratio_p50).toLocaleString(locale, { maximumFractionDigits: 2 })}
                </strong>
                {t(
                  ` lần (so với ước tính) việc ${risks[0]}. Tương quan thứ hạng ${rep.spearman_test.toLocaleString(locale)}, AUC ${rep.auc_overrun_25pct_test.toLocaleString(locale)} cho việc vượt quá 25%.`,
                  ` times as long, versus the estimate, as ${risks[0]} tasks. Rank correlation ${rep.spearman_test.toLocaleString(locale)}, AUC ${rep.auc_overrun_25pct_test.toLocaleString(locale)} for tasks that overrun by more than 25%.`,
                )}
              </p>
              {ev.itemlet_replication && (
                <p>
                  {t(
                    `Thử lại nguyên câu hỏi và ngưỡng đó trên ${ev.itemlet_replication.n_read} việc của ${ev.itemlet_replication.projects} dự án mã nguồn mở khác (Itemlet): cùng chiều nhưng yếu hơn nhiều (tỷ lệ cao/thấp ×${ev.itemlet_replication.high_vs_low_ratio_p50?.toLocaleString(locale)}, tương quan ${ev.itemlet_replication.spearman.toLocaleString(locale)}), và nhân giờ theo hệ số của SiP làm sai lệch tăng (${ev.itemlet_replication.mae_raw_estimate.toLocaleString(locale)} → ${ev.itemlet_replication.mae_with_sip_factors.toLocaleString(locale)} giờ).`,
                    `The same question and the same boundaries, tried again on ${ev.itemlet_replication.n_read} tasks from ${ev.itemlet_replication.projects} other open-source projects (Itemlet): the same direction, but much weaker (high/low ratio ×${ev.itemlet_replication.high_vs_low_ratio_p50?.toLocaleString(locale)}, correlation ${ev.itemlet_replication.spearman.toLocaleString(locale)}). Multiplying hours by the SiP factors made the error worse (${ev.itemlet_replication.mae_raw_estimate.toLocaleString(locale)} → ${ev.itemlet_replication.mae_with_sip_factors.toLocaleString(locale)} hours).`,
                  )}
                </p>
              )}
              <p className="font-semibold">
                {t(
                  'Vì vậy app chỉ gắn cờ những câu AI đánh giá dễ vượt giờ để xem kỹ, không tự cộng giờ. Mức cộng (nếu có) được học từ giờ thực tế của chính nhóm bạn.',
                  'So the app only flags clauses the AI rates as likely to overrun, for a closer look. It does not add hours. Any uplift is learned from your own team’s actual hours.',
                )}
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                {t(
                  `Nói thẳng: dự báo từng việc chưa chính xác hơn rõ rệt (sai lệch trung bình ${rep.calibrated_size_only.mae.toLocaleString(locale)} → ${rep.calibrated_with_jev.mae.toLocaleString(locale)} giờ, khoảng tin cậy 95% của mức giảm: ${rep.mae_gain_95ci_h[0]} đến ${rep.mae_gain_95ci_h[1]} giờ); tỷ lệ việc sai dưới 25% tăng ${rep.calibrated_size_only.pred_25.toLocaleString(locale)}% → ${rep.calibrated_with_jev.pred_25.toLocaleString(locale)}%. Câu hỏi được chọn trong ${study.pilot.candidates.length} câu thử trên ${study.pilot.size} việc của các năm trước.`,
                  `Stated plainly: the per-task forecast is not clearly more accurate (mean error ${rep.calibrated_size_only.mae.toLocaleString(locale)} → ${rep.calibrated_with_jev.mae.toLocaleString(locale)} hours; 95% confidence interval of the reduction: ${rep.mae_gain_95ci_h[0]} to ${rep.mae_gain_95ci_h[1]} hours). The share of tasks within 25% rose from ${rep.calibrated_size_only.pred_25.toLocaleString(locale)}% to ${rep.calibrated_with_jev.pred_25.toLocaleString(locale)}%. The question was chosen from ${study.pilot.candidates.length} candidates tried on ${study.pilot.size} tasks from the earlier years.`,
                )}
              </p>
            </div>
          </div>
        </section>
      )}

      {improvement.length > 0 && (
        <section className={`${card} p-6 space-y-4`}>
          <div>
            <h2 className="text-lg font-bold">{t('Luật được cải tiến qua từng vòng', 'The rules improved across rounds')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('Đo trên dữ liệu không dùng để sửa luật (câu soạn sau, hoặc phần dự án để riêng).', 'Scored on data that was not used to change the rules (clauses written later, or a held-out set of projects).')}</p>
          </div>
          <GroupedBars
            series={[
              { key: 'before', label: t('Trước khi sửa', 'Before the change'), tone: 'muted' },
              { key: 'after', label: t('Sau khi sửa', 'After the change'), tone: 'good' },
            ]}
            groups={improvement}
          />
        </section>
      )}

      <section className={`${card} p-6 space-y-4`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold">{t('Học từ giờ thực tế có chính xác hơn không?', 'Does learning from actual hours make the estimate more accurate?')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">{t('10.022 công việc thật (SiP, 2004–2014): học từ các năm trước, kiểm tra trên các năm sau.', '10,022 real tasks (SiP, 2004–2014): learn from earlier years, test on later years.')}</p>
          </div>
          {!bench && (
            <button
              type="button"
              onClick={runBench}
              disabled={running}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 font-semibold hover:border-indigo-400 inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <RotateCcw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} /> {running ? t('Đang chạy (~15 giây)…', 'Running (~15 seconds)…') : t('Chạy kiểm tra', 'Run the check')}
            </button>
          )}
        </div>
        {holdout && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GroupedBars
              series={[
                { key: 'base', label: t('Ước lượng gốc của người làm', 'The person’s original estimate'), tone: 'muted' },
                { key: 'cal', label: t('Sau khi học từ dữ liệu cũ', 'After learning from earlier data'), tone: 'good' },
              ]}
              groups={[
                {
                  key: 'mae',
                  label: t(
                    `Sai lệch trung bình mỗi công việc (${holdout.n_test.toLocaleString(locale)} việc)`,
                    `Mean error per task (${holdout.n_test.toLocaleString(locale)} tasks)`,
                  ),
                  values: [
                    { series: 'base', value: 1, display: hours1(holdout.baseline.mae) },
                    { series: 'cal', value: holdout.calibrated.mae / holdout.baseline.mae, display: hours1(holdout.calibrated.mae) },
                  ],
                },
              ]}
            />
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">{t('Sai lệch theo năm: học liên tục so với học một lần', 'Error by year: learning every year, versus fitting once')}</div>
              <div className="flex items-end gap-1.5 h-28" aria-hidden="true">
                {bench!.sip.learning_curve.points.map((p) => {
                  const top = Math.max(...bench!.sip.learning_curve.points.map((x) => x.frozen_mae));
                  return (
                    <div key={p.year} className="flex-1 flex flex-col items-center gap-1">
                      <div className="w-full flex items-end gap-0.5 h-24">
                        <div className="flex-1 rounded-t bg-slate-300 dark:bg-slate-600" style={{ height: `${(p.frozen_mae / top) * 100}%` }} />
                        <div className="flex-1 rounded-t bg-emerald-500" style={{ height: `${(p.rolling_mae / top) * 100}%` }} />
                      </div>
                      <span className="text-[10px] text-slate-600 dark:text-slate-400">{String(p.year).slice(2)}</span>
                    </div>
                  );
                })}
              </div>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                <span className="inline-block w-2.5 h-2.5 bg-slate-300 dark:bg-slate-600 mr-1 align-middle" />{t('học một lần', 'fitted once')} ·
                <span className="inline-block w-2.5 h-2.5 bg-emerald-500 mx-1 align-middle" />
                {t(
                  `học thêm mỗi năm (thấp hơn = ${bench!.sip.learning_curve.points.filter((p) => p.rolling_mae < p.frozen_mae).length}/${bench!.sip.learning_curve.points.length} năm)`,
                  `updated each year (lower = ${bench!.sip.learning_curve.points.filter((p) => p.rolling_mae < p.frozen_mae).length}/${bench!.sip.learning_curve.points.length} years)`,
                )}
              </p>
            </div>
          </div>
        )}
      </section>

      {replay && (
        <section className={`${card} p-6 space-y-4`}>
          <div>
            <h2 className="text-lg font-bold">{t('Chạy thử như đang vận hành thật (2011–2014)', 'Replayed as if it were in production (2011–2014)')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {t(
                `Phát lại ${replay.all_tasks.human.n.toLocaleString(locale)} công việc thật theo đúng ngày: mỗi dự toán chỉ được học từ những việc `,
                `Replayed ${replay.all_tasks.human.n.toLocaleString(locale)} real tasks in date order: each estimate may learn only from work `,
              )}
              <strong>{t('đã xong', 'already finished')}</strong>
              {t(
                ' trước ngày ước tính, giờ thực tế được nạp vào đúng ngày việc hoàn thành.',
                ' before the estimate date, and actual hours are added on the day the work was finished.',
              )}
            </p>
          </div>
          <GroupedBars
            series={[
              { key: 'human', label: t('Ước lượng của lập trình viên', 'The developers’ estimate'), tone: 'muted' },
              { key: 'online', label: t('App học liên tục', 'The app, learning as it goes'), tone: 'good' },
            ]}
            groups={[
              {
                key: 'mae',
                label: t('Sai lệch trung bình mỗi việc', 'Mean error per task'),
                values: [
                  { series: 'human', value: 1, display: hours1(replay.all_tasks.human.mae) },
                  { series: 'online', value: replay.all_tasks.online.mae / replay.all_tasks.human.mae, display: hours1(replay.all_tasks.online.mae) },
                ],
              },
              {
                key: 'sa',
                label: t('Độ chính xác so với đoán ngẫu nhiên (SA, cao hơn là tốt)', 'Accuracy against a random guess (SA, higher is better)'),
                values: [
                  { series: 'human', value: replay.all_tasks.human.sa / 100, display: pct(replay.all_tasks.human.sa) },
                  { series: 'online', value: replay.all_tasks.online.sa / 100, display: pct(replay.all_tasks.online.sa) },
                ],
              },
            ]}
          />
          <p className="text-xs text-slate-600 dark:text-slate-400">
            {t(
              `Kiểm định Wilcoxon (từng cặp việc): p = ${replay.all_tasks.online.wilcoxon_vs_human_p}. Khoảng 80% (P10–P90) chứa đúng ${pct(replay.all_tasks.online.coverage_p10_p90)} giờ thực tế. Với việc lớn AI đã đọc, lớp “dễ vượt giờ” không làm sai lệch giảm (${replay.dev_tasks_20h_read_by_jev.online.mae} → ${replay.dev_tasks_20h_read_by_jev['online+jev'].mae} giờ), nên không được dùng để cộng giờ.`,
              `Wilcoxon test (paired by task): p = ${replay.all_tasks.online.wilcoxon_vs_human_p}. The 80% range (P10–P90) contains the actual hours ${pct(replay.all_tasks.online.coverage_p10_p90)} of the time. On the large tasks the AI had read, the “likely to overrun” group did not reduce the error (${replay.dev_tasks_20h_read_by_jev.online.mae} → ${replay.dev_tasks_20h_read_by_jev['online+jev'].mae} hours), so it is not used to add hours.`,
            )}
          </p>
        </section>
      )}

      {conf && (
        <section className={`${card} p-6 space-y-4`}>
          <div>
            <h2 className="text-lg font-bold">{t('Khoảng “80% chắc chắn” có trung thực không?', 'Is the “80% sure” range honest?')}</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              {t(
                'Cùng phép chạy như vận hành thật 2011–2014. Mỗi khi một việc hoàn thành, app kiểm tra giờ thực tế có nằm trong khoảng đã báo không và tự nới hoặc thu hẹp khoảng cho những dự toán sau (Adaptive Conformal Inference). Bước điều chỉnh được chọn trên 2008–2010.',
                'The same production-style replay for 2011–2014. Each time a task finishes, the app checks whether the actual hours fell inside the range it quoted, then widens or narrows the range for later estimates (Adaptive Conformal Inference). The step size was chosen on 2008–2010.',
              )}
            </p>
          </div>
          <GroupedBars
            series={[
              { key: 'without', label: t('Khoảng cố định', 'Fixed range'), tone: 'muted' },
              { key: 'with', label: t('Khoảng tự điều chỉnh (đang dùng)', 'Self-adjusting range (in use)'), tone: 'good' },
            ]}
            groups={['0-4h', '4-8h', '8-20h', '20-50h', '>= 50h']
              .filter((b) => conf.without.by_bucket[b])
              .map((b) => ({
                key: b,
                label: t(
                  `Việc ${b.replace('>= ', '≥ ').replace('h', ' giờ')} (${conf.without.by_bucket[b].n} việc): tỷ lệ giờ thực tế nằm trong khoảng`,
                  `Tasks of ${b.replace('>= ', '≥ ').replace('h', ' hours')} (${conf.without.by_bucket[b].n} tasks): share of actual hours inside the range`,
                ),
                values: [
                  { series: 'without', value: conf.without.by_bucket[b].coverage / 100, display: pct(conf.without.by_bucket[b].coverage) },
                  { series: 'with', value: conf.with.by_bucket[b].coverage / 100, display: pct(conf.with.by_bucket[b].coverage) },
                ],
              }))}
          />
          <p className="text-xs text-slate-600 dark:text-slate-400">
            {t('Tổng: ', 'Overall: ')}
            {pct(conf.without.overall_coverage)} → <strong>{pct(conf.with.overall_coverage)}</strong>
            {t(
              ` (mục tiêu 80%); cỡ việc lệch nhiều nhất: ${conf.without.worst_bucket_gap} → ${conf.with.worst_bucket_gap} điểm. Đánh đổi: khoảng cho việc 20–50 giờ rộng gần gấp đôi, việc nhỏ hẹp lại. Nhóm ≥ 50 giờ chỉ có ${conf.with.by_bucket['>= 50h']?.n ?? 0} việc nên chưa kết luận được.`,
              ` (target 80%); the size band furthest from the target: ${conf.without.worst_bucket_gap} → ${conf.with.worst_bucket_gap} points. The tradeoff: the range for 20–50 hour tasks nearly doubles, and small tasks get a narrower range. The ≥ 50 hour band has only ${conf.with.by_bucket['>= 50h']?.n ?? 0} tasks, so it is not settled.`,
            )}
          </p>
        </section>
      )}

      <section className={`${card} p-6 space-y-3`}>
        <h2 className="text-lg font-bold">{t('Phản hồi từ người dùng trong app', 'Feedback from people using the app')}</h2>
        {fb && fb.answered > 0 ? (
          <>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              {t('Gợi ý của AI được chấp nhận ', 'AI suggestions were accepted ')}
              <strong>{fb.accepted}/{fb.answered}</strong>
              {t(
                ' lần. Loại gợi ý nào bị từ chối liên tục (≥ 3 lần, tỷ lệ nhận dưới 30%) sẽ tự tắt.',
                ' times. A kind of suggestion that keeps being rejected (3 or more times, accepted under 30%) turns itself off.',
              )}
            </p>
            <ul className="text-sm space-y-1">
              {fb.by_component.map((c) => (
                <li key={c.component} className="flex justify-between">
                  <span>{kinds[c.component] ?? c.component}</span>
                  <span className={c.muted ? 'text-rose-700 dark:text-rose-400 font-semibold' : ''}>
                    {c.accepted}/{c.answered} {c.muted ? t('· đã tắt gợi ý', '· suggestion turned off') : ''}
                  </span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-sm text-slate-600 dark:text-slate-400">
            {t(
              'Chưa có phản hồi. Mỗi lần bạn trả lời câu hỏi "Gợi ý từ AI" hoặc xóa công việc AI thêm vào, hệ thống ghi lại để điều chỉnh gợi ý.',
              'No feedback yet. Each time you answer an “AI suggestion” question, or remove work the AI added, the app records it and adjusts later suggestions.',
            )}
          </p>
        )}
      </section>

      <section className={`${card} p-6 space-y-3`}>
        <h2 className="text-lg font-bold flex items-center gap-2">
          <KeyRound className="w-5 h-5" /> {t('AI Jev đang chạy', 'Jev is running')}
        </h2>
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {st.configured
            ? t(
                `${st.keys_usable ?? 0}/${st.keys_total ?? 0} khóa dùng được${st.credits_remaining != null ? ` · còn khoảng ${st.credits_remaining} lượt (mỗi lượt 5 câu hỏi)` : ''} · ${st.cached_clauses} câu trả lời đã lưu, đọc lại không tốn phí.`,
                `${st.keys_usable ?? 0}/${st.keys_total ?? 0} keys usable${st.credits_remaining != null ? ` · about ${st.credits_remaining} calls left (5 questions each)` : ''} · ${st.cached_clauses} saved answers, free to read again.`,
              )
            : t(
                'Chưa cấu hình khóa Jev: app chỉ tính được các mô tả mẫu đã đọc sẵn.',
                'No Jev key is configured: only the sample briefs that were already read can be estimated.',
              )}{' '}
          {st.required !== false && t('Mỗi dự toán đều phải được AI đọc đủ mọi câu.', 'Every estimate needs the AI to read every clause.')}{' '}
          {t(`Mô hình đang gọi: ${st.model ?? 'jev-1.13.0'}.`, `Model in use: ${st.model ?? 'jev-1.13.0'}.`)}
        </p>
        {st.halted && <p className="text-sm text-rose-700 dark:text-rose-400">{t(`Đã tạm dừng để bảo vệ credit: ${st.halted}`, `Paused to protect credits: ${st.halted}`)}</p>}
      </section>

      <details className={`${card} p-6`}>
        <summary className="font-bold cursor-pointer">{t(`Nhật ký kiểm thử (${journal.length} lần chạy)`, `Test journal (${journal.length} runs)`)}</summary>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs">
            <thead className="text-left text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th scope="col" className="py-1.5 pr-2 font-semibold">{t('Thời gian', 'When')}</th>
                <th scope="col" className="py-1.5 px-2 font-semibold">{t('Lần chạy', 'Run')}</th>
                <th scope="col" className="py-1.5 px-2 font-semibold">{t('Kết quả', 'Result')}</th>
                <th scope="col" className="py-1.5 pl-2 font-semibold">{t('Ghi chú', 'Note')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {journal.map((e, i) => (
                <tr key={i}>
                  <td className="py-1.5 pr-2 whitespace-nowrap">{e.date.replace('T', ' ').slice(0, 16)}</td>
                  <td className="py-1.5 px-2 font-mono">{e.tag}</td>
                  <td className="py-1.5 px-2 min-w-48 font-semibold tabular-nums text-slate-800 dark:text-slate-200">{resultText(e, t, pct)}</td>
                  <td className="py-1.5 pl-2 min-w-64 text-slate-700 dark:text-slate-300">{e.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-3">
          {t(
            `Mô hình AI: ${ev.held_out?.model ?? 'jev-1.13.0'} (Jev của TypeSafe, qua JevStation). Dữ liệu: SiP (CC BY-NC-ND 4.0; chỉ lưu mã công việc và xác suất AI, không sao chép nội dung), PROMISE_exp (Lima et al., 2019). Bộ câu gán tay còn nhỏ (${labelledClauses} câu, chủ yếu tiếng Việt), cần thêm mô tả thật của khách để kết luận chắc chắn.`,
            `AI model: ${ev.held_out?.model ?? 'jev-1.13.0'} (Jev by TypeSafe, through JevStation). Data: SiP (CC BY-NC-ND 4.0; only task ids and the AI’s probabilities are stored, not the text), PROMISE_exp (Lima et al., 2019). The hand-labelled set is still small (${labelledClauses} clauses, mostly Vietnamese) and needs more real client briefs before the conclusion is firm.`,
          )}
        </p>
      </details>
    </div>
  );
};
