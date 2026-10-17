import React, { useEffect, useState } from 'react';
import { CheckCircle2, Gauge, KeyRound, RotateCcw, Sparkles, TrendingDown } from 'lucide-react';
import type { BenchmarkReport, JournalEntry, ReaderEvaluation, ReaderSummary } from '../types';
import { fetchReaderEvaluation } from '../api';
import { KIND_LABELS, card } from '../ui';
import { GroupedBars } from './charts';
import { TONE, type Tone } from './tone';

interface EvidenceScreenProps {
  onRunBenchmark: () => Promise<BenchmarkReport>;
}

const frac = (s?: string | null): [number, number] => {
  const [a, b] = String(s ?? '0/0').split('/').map(Number);
  return [a || 0, b || 0];
};
const vn = (v: unknown) => `${Number(v).toLocaleString('vi-VN', { maximumFractionDigits: 1 })}%`;
const hours1 = (v: number) => `${v.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} giờ`;
const find = (j: JournalEntry[], tag: string) => [...j].reverse().find((e) => e.tag === tag);
const reader = (rows: Partial<ReaderSummary>[] | undefined, name: string) => rows?.find((r) => r.reader === name);
const promise = (e: JournalEntry | undefined) =>
  (e?.summary?.[0]?.test_odd_projects ?? null) as null | Record<string, number | string>;

/** One-line result of a journal entry, in the same words as the charts. */
const resultText = (e: JournalEntry): string => {
  const odd = promise(e);
  if (odd) return `giữ lại ${vn(odd.retention_pct)} · hiệu năng ${vn(odd.performance_recall_pct)} · bảo mật ${vn(odd.security_recall_pct)}`;
  const first = e.summary?.[0];
  if (first && 'spearman_log_ratio' in first)
    return e.summary.map((s) => `${String(s.question).split('@')[0]} ρ=${s.spearman_log_ratio}`).join(' · ');
  const jevRow = e.summary?.find((s) => String(s.reader ?? '').startsWith('jev:'));
  const sizeRow = e.summary?.find((s) => String(s.reader) === 'size-only');
  if (jevRow && sizeRow) return `sai lệch ${sizeRow.mae} → ${jevRow.mae} giờ · PRED(25) ${sizeRow.pred_25}% → ${jevRow.pred_25}%`;
  if (first && 'mae_change_pct' in first) return `sai lệch ${String(first.mae_change_pct).replace('.', ',')}% (${first.baseline_mae} → ${first.calibrated_mae} giờ)`;
  if (first && 'retention_pct' in first) return `giữ lại ${vn(first.retention_pct)}`;
  const r = reader(e.summary, 'shipped') ?? reader(e.summary, 'rules');
  if (!r) return '';
  const who = r.reader === 'shipped' ? 'Luật + AI' : 'Chỉ luật';
  return `${who}: loại việc ${r.primary_kind_found}/${r.n_clauses} · chưa chốt ${r.tentative_caught}`;
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
    return <div className="max-w-5xl mx-auto text-slate-600 dark:text-slate-400">{error ?? 'Đang tải kết quả kiểm thử…'}</div>;
  }
  const journal = ev.journal ?? [];
  const r1 = ev.held_out?.summary;
  const r2 = find(journal, 'round2')?.summary;
  const r4 = find(journal, 'round4_heldout')?.summary;
  const r5 = find(journal, 'round5_heldout')?.summary;
  const rounds = [
    { key: 'r1', label: `Vòng 1 · ${reader(r1, 'rules')?.n_clauses ?? 0} câu`, rows: r1 },
    { key: 'r2', label: `Vòng 2 · ${reader(r2, 'rules')?.n_clauses ?? 0} câu`, rows: r2 },
    { key: 'r4', label: `Vòng 4 · ${reader(r4, 'rules')?.n_clauses ?? 0} câu`, rows: r4 },
    { key: 'r5', label: `Vòng 5 (mới nhất) · ${reader(r5, 'rules')?.n_clauses ?? 0} câu`, rows: r5 },
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
      label: `Tiếng Việt, câu mới (vòng 3 · ${r3After.n_clauses} câu): đúng loại việc chính`,
      values: [
        { series: 'before', value: ratio(r3Before.primary_kind_found ?? 0, r3Before.n_clauses ?? 1), display: `${r3Before.primary_kind_found}/${r3Before.n_clauses}` },
        { series: 'after', value: ratio(r3After.primary_kind_found ?? 0, r3After.n_clauses ?? 1), display: `${r3After.primary_kind_found}/${r3After.n_clauses}` },
      ],
    },
    pBefore && pAfter && {
      key: 'pret',
      label: `Tiếng Anh thật (PROMISE · ${pAfter.n_requirements} yêu cầu): giữ lại đủ yêu cầu`,
      values: [
        { series: 'before', value: Number(pBefore.retention_pct) / 100, display: vn(pBefore.retention_pct) },
        { series: 'after', value: Number(pAfter.retention_pct) / 100, display: vn(pAfter.retention_pct) },
      ],
    },
    pBefore && pAfter && {
      key: 'pperf',
      label: 'PROMISE: nhận ra yêu cầu hiệu năng',
      values: [
        { series: 'before', value: Number(pBefore.performance_recall_pct) / 100, display: vn(pBefore.performance_recall_pct) },
        { series: 'after', value: Number(pAfter.performance_recall_pct) / 100, display: vn(pAfter.performance_recall_pct) },
      ],
    },
    pBefore && pAfter && {
      key: 'psec',
      label: 'PROMISE: nhận ra yêu cầu bảo mật',
      values: [
        { series: 'before', value: Number(pBefore.security_recall_pct) / 100, display: vn(pBefore.security_recall_pct) },
        { series: 'after', value: Number(pAfter.security_recall_pct) / 100, display: vn(pAfter.security_recall_pct) },
      ],
    },
  ].filter(Boolean) as { key: string; label: string; values: { series: string; value: number; display: string }[] }[];

  const holdout = bench?.sip.holdout;
  const sip = find(journal, 'sip_holdout')?.summary?.[0] as undefined | Record<string, number | string>;
  const r4All = find(journal, 'round4_rules_before')?.summary;
  const labelledClauses = [r1, r2, r3After ? [r3After] : undefined, r4All, r5].reduce((s, rows) => s + Number(reader(rows, 'rules')?.n_clauses ?? 0), 0);
  const fb = ev.feedback;
  const study = ev.sip_study;
  const rep = study?.report;
  const st = ev.status;
  const replay = ev.operational_replay;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Kiểm chứng bằng dữ liệu thật</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Mỗi vòng thử dùng câu mới, đáp án gán tay <strong>trước</strong> khi chạy. Phần dùng để sửa luật được tách riêng với phần dùng
          để chấm.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Kpi
          tone="ai"
          icon={<Sparkles className="w-4 h-4" />}
          label="AI nhận ra yêu cầu chưa chốt"
          value={`${tShip}/${tAll}`}
          sub={`Chỉ dùng luật: ${tRules}/${tAll}. Không báo nhầm câu nào.`}
        />
        {replay && (
          <Kpi
            tone="good"
            icon={<Gauge className="w-4 h-4" />}
            label="Vận hành thật 2011–2014"
            value={`${vn(replay.all_tasks.online.sa)}`}
            sub={`Độ chính xác so với đoán ngẫu nhiên; ước lượng của lập trình viên: ${vn(replay.all_tasks.human.sa)} (${replay.all_tasks.human.n.toLocaleString('vi-VN')} việc).`}
          />
        )}
        {sip && (
          <Kpi
            tone="good"
            icon={<TrendingDown className="w-4 h-4" />}
            label="Học từ giờ thực tế"
            value={`${String(sip.mae_change_pct).replace('.', ',')}%`}
            sub={`Sai lệch trung bình trên ${Number(sip.n_test).toLocaleString('vi-VN')} công việc thật chưa từng thấy (SiP 2011–2014).`}
          />
        )}
        {pBefore && pAfter && (
          <Kpi
            tone="primary"
            icon={<CheckCircle2 className="w-4 h-4" />}
            label="Yêu cầu tiếng Anh được giữ lại"
            value={vn(pAfter.retention_pct)}
            sub={`Trước khi sửa luật: ${vn(pBefore.retention_pct)} (PROMISE, phần dữ liệu chấm).`}
          />
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <section className={`${card} p-6 space-y-4`}>
          <h2 className="text-lg font-bold">Nhận ra yêu cầu khách chưa chốt</h2>
          <GroupedBars
            series={[
              { key: 'rules', label: 'Chỉ luật', tone: 'muted' },
              { key: 'shipped', label: 'Luật + AI (đang dùng)', tone: 'ai' },
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
          <h2 className="text-lg font-bold">Đúng loại việc chính</h2>
          <GroupedBars
            series={[
              { key: 'rules', label: 'Chỉ luật', tone: 'muted' },
              { key: 'jev', label: 'Chỉ AI', tone: 'attention' },
              { key: 'shipped', label: 'Luật + AI (đang dùng)', tone: 'ai' },
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
            Khi AI thấy loại việc mà luật bỏ sót, app hỏi bạn thay vì tự cộng giờ, nên số ở đây chưa tính các gợi ý được bạn chấp nhận.
          </p>
        </section>
      </div>

      {rep && study && (
        <section className={`${card} p-6 space-y-5`}>
          <div>
            <h2 className="text-lg font-bold">AI đọc công việc thật: việc nào sẽ tốn hơn vẻ ngoài?</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Jev đọc mô tả của {rep.groups_train.reduce((s, g) => s + g.n_train, 0) + rep.groups_test.reduce((s, g) => s + g.n_test, 0)} công
              việc lập trình thật (SiP, ước tính từ 20 giờ trở lên) và trả lời đúng câu hỏi app đặt cho mỗi câu trong mô tả của khách:{' '}
              <em>“người làm lâu năm có thấy việc này sẽ tốn thời gian hơn vẻ ngoài không?”</em>. Ngưỡng chia nhóm lấy từ các năm trước 2011;
              các năm 2011–2014 chỉ dùng để chấm, một lần.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">
                Giờ thực tế / giờ ước tính (trung vị) theo đánh giá của AI
              </div>
              <GroupedBars
                series={[
                  { key: 'train', label: 'Năm trước (để học)', tone: 'muted' },
                  { key: 'test', label: 'Năm sau (chưa từng thấy)', tone: 'ai' },
                ]}
                groups={[0, 1, 2].map((g) => {
                  const tr = rep.groups_train.find((x) => x.group === g);
                  const te = rep.groups_test.find((x) => x.group === g);
                  const top = Math.max(...rep.groups_train.map((x) => x.ratio_p50), ...rep.groups_test.map((x) => x.test_ratio_p50));
                  return {
                    key: `g${g}`,
                    label: `${['Ít rủi ro', 'Rủi ro vừa', 'Dễ vượt giờ'][g]} (${tr?.n_train ?? 0} + ${te?.n_test ?? 0} việc)`,
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
                Trên năm chưa từng thấy, thứ tự vẫn giữ nguyên: việc AI đánh giá <strong>dễ vượt giờ</strong> tốn gấp{' '}
                <strong>
                  {(rep.groups_test[2].test_ratio_p50 / rep.groups_test[0].test_ratio_p50).toLocaleString('vi-VN', { maximumFractionDigits: 2 })}
                </strong>{' '}
                lần (so với ước tính) việc ít rủi ro. Tương quan thứ hạng {rep.spearman_test.toLocaleString('vi-VN')}, AUC{' '}
                {rep.auc_overrun_25pct_test.toLocaleString('vi-VN')} cho việc vượt quá 25%.
              </p>
              {ev.itemlet_replication && (
                <p>
                  Thử lại nguyên câu hỏi và ngưỡng đó trên {ev.itemlet_replication.n_read} việc của {ev.itemlet_replication.projects} dự án
                  mã nguồn mở khác (Itemlet): cùng chiều nhưng yếu hơn nhiều (tỷ lệ cao/thấp ×
                  {ev.itemlet_replication.high_vs_low_ratio_p50?.toLocaleString('vi-VN')}, tương quan{' '}
                  {ev.itemlet_replication.spearman.toLocaleString('vi-VN')}), và nhân giờ theo hệ số của SiP làm sai lệch tăng (
                  {ev.itemlet_replication.mae_raw_estimate.toLocaleString('vi-VN')} →{' '}
                  {ev.itemlet_replication.mae_with_sip_factors.toLocaleString('vi-VN')} giờ).
                </p>
              )}
              <p className="font-semibold">
                Vì vậy app chỉ gắn cờ những câu AI đánh giá dễ vượt giờ để xem kỹ, không tự cộng giờ. Mức cộng (nếu có) được học từ giờ thực tế
                của chính nhóm bạn.
              </p>
              <p className="text-xs text-slate-600 dark:text-slate-400">
                Nói thẳng: dự báo từng việc chưa chính xác hơn rõ rệt (sai lệch trung bình {rep.calibrated_size_only.mae.toLocaleString('vi-VN')} →{' '}
                {rep.calibrated_with_jev.mae.toLocaleString('vi-VN')} giờ, khoảng tin cậy 95% của mức giảm: {rep.mae_gain_95ci_h[0]} đến{' '}
                {rep.mae_gain_95ci_h[1]} giờ); tỷ lệ việc sai dưới 25% tăng {rep.calibrated_size_only.pred_25.toLocaleString('vi-VN')}% →{' '}
                {rep.calibrated_with_jev.pred_25.toLocaleString('vi-VN')}%. Câu hỏi được chọn trong {study.pilot.candidates.length} câu thử trên{' '}
                {study.pilot.size} việc của các năm trước.
              </p>
            </div>
          </div>
        </section>
      )}

      {improvement.length > 0 && (
        <section className={`${card} p-6 space-y-4`}>
          <div>
            <h2 className="text-lg font-bold">Luật được cải tiến qua từng vòng</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">Đo trên dữ liệu không dùng để sửa luật (câu soạn sau, hoặc phần dự án để riêng).</p>
          </div>
          <GroupedBars
            series={[
              { key: 'before', label: 'Trước khi sửa', tone: 'muted' },
              { key: 'after', label: 'Sau khi sửa', tone: 'good' },
            ]}
            groups={improvement}
          />
        </section>
      )}

      <section className={`${card} p-6 space-y-4`}>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-lg font-bold">Học từ giờ thực tế có chính xác hơn không?</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">10.022 công việc thật (SiP, 2004–2014): học từ các năm trước, kiểm tra trên các năm sau.</p>
          </div>
          {!bench && (
            <button
              type="button"
              onClick={runBench}
              disabled={running}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 font-semibold hover:border-indigo-400 inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              <RotateCcw className={`w-4 h-4 ${running ? 'animate-spin' : ''}`} /> {running ? 'Đang chạy (~15 giây)…' : 'Chạy kiểm tra'}
            </button>
          )}
        </div>
        {holdout && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <GroupedBars
              series={[
                { key: 'base', label: 'Ước lượng gốc của người làm', tone: 'muted' },
                { key: 'cal', label: 'Sau khi học từ dữ liệu cũ', tone: 'good' },
              ]}
              groups={[
                {
                  key: 'mae',
                  label: `Sai lệch trung bình mỗi công việc (${holdout.n_test.toLocaleString('vi-VN')} việc)`,
                  values: [
                    { series: 'base', value: 1, display: hours1(holdout.baseline.mae) },
                    { series: 'cal', value: holdout.calibrated.mae / holdout.baseline.mae, display: hours1(holdout.calibrated.mae) },
                  ],
                },
              ]}
            />
            <div className="space-y-2">
              <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">Sai lệch theo năm: học liên tục so với học một lần</div>
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
                <span className="inline-block w-2.5 h-2.5 bg-slate-300 dark:bg-slate-600 mr-1 align-middle" />học một lần ·
                <span className="inline-block w-2.5 h-2.5 bg-emerald-500 mx-1 align-middle" />học thêm mỗi năm (thấp hơn ={' '}
                {bench!.sip.learning_curve.points.filter((p) => p.rolling_mae < p.frozen_mae).length}/{bench!.sip.learning_curve.points.length} năm)
              </p>
            </div>
          </div>
        )}
      </section>

      {replay && (
        <section className={`${card} p-6 space-y-4`}>
          <div>
            <h2 className="text-lg font-bold">Chạy thử như đang vận hành thật (2011–2014)</h2>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Phát lại {replay.all_tasks.human.n.toLocaleString('vi-VN')} công việc thật theo đúng ngày: mỗi dự toán chỉ được học từ những
              việc <strong>đã xong</strong> trước ngày ước tính, giờ thực tế được nạp vào đúng ngày việc hoàn thành.
            </p>
          </div>
          <GroupedBars
            series={[
              { key: 'human', label: 'Ước lượng của lập trình viên', tone: 'muted' },
              { key: 'online', label: 'App học liên tục', tone: 'good' },
            ]}
            groups={[
              {
                key: 'mae',
                label: 'Sai lệch trung bình mỗi việc',
                values: [
                  { series: 'human', value: 1, display: hours1(replay.all_tasks.human.mae) },
                  { series: 'online', value: replay.all_tasks.online.mae / replay.all_tasks.human.mae, display: hours1(replay.all_tasks.online.mae) },
                ],
              },
              {
                key: 'sa',
                label: 'Độ chính xác so với đoán ngẫu nhiên (SA, cao hơn là tốt)',
                values: [
                  { series: 'human', value: replay.all_tasks.human.sa / 100, display: vn(replay.all_tasks.human.sa) },
                  { series: 'online', value: replay.all_tasks.online.sa / 100, display: vn(replay.all_tasks.online.sa) },
                ],
              },
            ]}
          />
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Kiểm định Wilcoxon (từng cặp việc): p = {replay.all_tasks.online.wilcoxon_vs_human_p}. Khoảng 80% (P10–P90) chứa đúng{' '}
            {vn(replay.all_tasks.online.coverage_p10_p90)} giờ thực tế. Với việc lớn AI đã đọc, lớp “dễ vượt giờ” không làm sai lệch giảm (
            {replay.dev_tasks_20h_read_by_jev.online.mae} → {replay.dev_tasks_20h_read_by_jev['online+jev'].mae} giờ), nên không được dùng để cộng
            giờ.
          </p>
        </section>
      )}

      <section className={`${card} p-6 space-y-3`}>
        <h2 className="text-lg font-bold">Phản hồi từ người dùng trong app</h2>
        {fb && fb.answered > 0 ? (
          <>
            <p className="text-sm text-slate-700 dark:text-slate-300">
              Gợi ý của AI được chấp nhận <strong>{fb.accepted}/{fb.answered}</strong> lần. Loại gợi ý nào bị từ chối liên tục (≥ 3 lần,
              tỷ lệ nhận dưới 30%) sẽ tự tắt.
            </p>
            <ul className="text-sm space-y-1">
              {fb.by_component.map((c) => (
                <li key={c.component} className="flex justify-between">
                  <span>{KIND_LABELS[c.component] ?? c.component}</span>
                  <span className={c.muted ? 'text-rose-700 dark:text-rose-400 font-semibold' : ''}>
                    {c.accepted}/{c.answered} {c.muted ? '· đã tắt gợi ý' : ''}
                  </span>
                </li>
              ))}
            </ul>
          </>
        ) : (
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Chưa có phản hồi. Mỗi lần bạn trả lời câu hỏi "Gợi ý từ AI" hoặc xóa công việc AI thêm vào, hệ thống ghi lại để điều chỉnh gợi ý.
          </p>
        )}
      </section>

      <section className={`${card} p-6 space-y-3`}>
        <h2 className="text-lg font-bold flex items-center gap-2">
          <KeyRound className="w-5 h-5" /> AI Jev đang chạy
        </h2>
        <p className="text-sm text-slate-700 dark:text-slate-300">
          {st.configured
            ? `${st.keys_usable ?? 0}/${st.keys_total ?? 0} khóa dùng được${st.credits_remaining != null ? ` · còn khoảng ${st.credits_remaining} lượt (mỗi lượt 5 câu hỏi)` : ''} · ${st.cached_clauses} câu trả lời đã lưu, đọc lại không tốn phí.`
            : 'Chưa cấu hình khóa Jev: app chỉ tính được các mô tả mẫu đã đọc sẵn.'}{' '}
          {st.required !== false && 'Mỗi dự toán đều phải được AI đọc đủ mọi câu.'}
        </p>
        {st.halted && <p className="text-sm text-rose-700 dark:text-rose-400">Đã tạm dừng để bảo vệ credit: {st.halted}</p>}
      </section>

      <details className={`${card} p-6`}>
        <summary className="font-bold cursor-pointer">Nhật ký kiểm thử ({journal.length} lần chạy)</summary>
        <div className="overflow-x-auto mt-3">
          <table className="w-full text-xs">
            <thead className="text-left text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
              <tr>
                <th scope="col" className="py-1.5 pr-2 font-semibold">Thời gian</th>
                <th scope="col" className="py-1.5 px-2 font-semibold">Lần chạy</th>
                <th scope="col" className="py-1.5 px-2 font-semibold">Kết quả</th>
                <th scope="col" className="py-1.5 pl-2 font-semibold">Ghi chú</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
              {journal.map((e, i) => (
                <tr key={i}>
                  <td className="py-1.5 pr-2 whitespace-nowrap">{e.date.replace('T', ' ').slice(0, 16)}</td>
                  <td className="py-1.5 px-2 font-mono">{e.tag}</td>
                  <td className="py-1.5 px-2 min-w-48 font-semibold tabular-nums text-slate-800 dark:text-slate-200">{resultText(e)}</td>
                  <td className="py-1.5 pl-2 min-w-64 text-slate-700 dark:text-slate-300">{e.note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="text-xs text-slate-600 dark:text-slate-400 mt-3">
          Mô hình AI: {ev.held_out?.model ?? 'jev-1.13.0'} (Jev của TypeSafe, qua JevStation). Dữ liệu: SiP (CC BY-NC-ND 4.0; chỉ lưu mã
          công việc và xác suất AI, không sao chép nội dung), PROMISE_exp (Lima et al., 2019). Bộ câu gán tay còn nhỏ ({labelledClauses} câu, chủ yếu tiếng Việt), cần thêm mô tả thật của khách để kết luận chắc chắn.
        </p>
      </details>
    </div>
  );
};
