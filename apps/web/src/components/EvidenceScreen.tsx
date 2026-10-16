import React, { useEffect, useState } from 'react';
import { CheckCircle2, RotateCcw, Sparkles, TrendingDown } from 'lucide-react';
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
  const rounds = [
    { key: 'r1', label: `Vòng 1 · ${reader(r1, 'rules')?.n_clauses ?? 0} câu`, rows: r1 },
    { key: 'r2', label: `Vòng 2 · ${reader(r2, 'rules')?.n_clauses ?? 0} câu`, rows: r2 },
    { key: 'r4', label: `Vòng 4 (lần cuối) · ${reader(r4, 'rules')?.n_clauses ?? 0} câu`, rows: r4 },
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
  const labelledClauses = [r1, r2, r3After ? [r3After] : undefined, r4All].reduce((s, rows) => s + Number(reader(rows, 'rules')?.n_clauses ?? 0), 0);
  const fb = ev.feedback;

  return (
    <div className="max-w-5xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl sm:text-3xl font-extrabold tracking-tight">Kiểm chứng bằng dữ liệu thật</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Mỗi vòng thử dùng câu mới, đáp án gán tay <strong>trước</strong> khi chạy. Phần dùng để sửa luật được tách riêng với phần dùng
          để chấm.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Kpi
          tone="ai"
          icon={<Sparkles className="w-4 h-4" />}
          label="AI nhận ra yêu cầu chưa chốt"
          value={`${tShip}/${tAll}`}
          sub={`Chỉ dùng luật: ${tRules}/${tAll}. Không báo nhầm câu nào.`}
        />
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
          Mô hình AI: {ev.held_out?.model ?? 'jev-1.13.0'} (Jev của TypeSafe, qua JevStation). Dữ liệu: SiP (CC BY-NC-ND 4.0), PROMISE_exp (Lima et
          al., 2019). Bộ câu gán tay còn nhỏ ({labelledClauses} câu, chủ yếu tiếng Việt), cần thêm mô tả thật của khách để kết luận chắc chắn.
        </p>
      </details>
    </div>
  );
};
