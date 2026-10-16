import React, { useEffect, useState } from 'react';
import { CheckCircle2, RefreshCw } from 'lucide-react';
import type { ActualsResult, EstimateVersion, HistoricalCase } from '../types';
import { fetchHistoricalCases } from '../api';
import { PROJECT_TYPES, card, hours } from '../ui';
import { GroupedBars } from './charts';

const typeLabel = (t: string) => PROJECT_TYPES.find((p) => p.value === t)?.label.toLowerCase() ?? t;

interface AccuracyLearningScreenProps {
  version: EstimateVersion;
  onRecordActuals: (actualHours: number, reasons: string[]) => Promise<ActualsResult>;
  onReestimate: () => Promise<void>;
  onOpenEvidence: () => void;
  isLoading: boolean;
}

const pct = (v: number) => `${Math.abs(Math.round(v))}%`;
const diffText = (actual: number, estimate: number) => {
  const d = ((actual - estimate) / estimate) * 100;
  if (Math.abs(d) < 1) return 'đúng bằng dự toán';
  return d > 0 ? `nhiều hơn dự toán ${pct(d)}` : `ít hơn dự toán ${pct(d)}`;
};

export const AccuracyLearningScreen: React.FC<AccuracyLearningScreenProps> = ({
  version,
  onRecordActuals,
  onReestimate,
  onOpenEvidence,
  isLoading,
}) => {
  const [actualHours, setActualHours] = useState('');
  const [note, setNote] = useState('');
  const [result, setResult] = useState<ActualsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [completed, setCompleted] = useState<HistoricalCase[]>([]);

  useEffect(() => {
    fetchHistoricalCases()
      .then(setCompleted)
      .catch((err) => console.error('Error fetching completed projects:', err));
  }, []);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const h = parseFloat(actualHours);
    if (isNaN(h) || h <= 0) return;
    setSaving(true);
    setError(null);
    try {
      setResult(await onRecordActuals(h, note ? [note] : []));
      setCompleted(await fetchHistoricalCases());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSaving(false);
    }
  };


  const adjust = result
    ? (result.calibration.type_multiplier_after / result.calibration.type_multiplier_before - 1) * 100
    : 0;

  return (
    <div className="max-w-3xl mx-auto space-y-6 animate-fadeIn">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">Dự án đã xong?</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-1">
          Nhập tổng số giờ thực tế đã làm. Hệ thống sẽ rút kinh nghiệm để các dự toán sau sát hơn.
        </p>
      </div>

      <form onSubmit={submit} className={`${card} p-6 space-y-4`}>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label htmlFor="actual-hours" className="text-sm font-semibold">
              Số giờ thực tế
            </label>
            <input
              id="actual-hours"
              type="number"
              step="0.5"
              min="1"
              value={actualHours}
              onChange={(e) => setActualHours(e.target.value)}
              placeholder={`Dự toán: ${Math.round(version.forecast.p50_hours)}`}
              className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20"
              required
            />
          </div>
          <div className="sm:col-span-2 space-y-1.5">
            <label htmlFor="actual-note" className="text-sm font-semibold">
              Ghi chú <span className="font-normal text-slate-600 dark:text-slate-400">(không bắt buộc)</span>
            </label>
            <input
              id="actual-note"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="VD: khách đổi yêu cầu"
              className="w-full px-4 py-2.5 rounded-xl bg-white dark:bg-[#0b0f1a] border border-slate-300 dark:border-slate-700 focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20"
            />
          </div>
        </div>
        <button
          type="submit"
          disabled={saving || !actualHours}
          className="px-6 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold disabled:opacity-50 cursor-pointer"
        >
          {saving ? 'Đang lưu…' : 'Lưu'}
        </button>

        {error && (
          <p role="alert" className="text-sm text-rose-700 dark:text-rose-400">
            {error}
          </p>
        )}

        {result && (
          <div aria-live="polite" className="p-4 rounded-xl bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-800 space-y-2">
            <p className="flex items-start gap-2 font-semibold text-emerald-900 dark:text-emerald-100">
              <CheckCircle2 className="w-5 h-5 flex-shrink-0 mt-0.5" />
              Đã lưu. Thực tế {hours(result.actual_hours)}, {diffText(result.actual_hours, result.estimated_p50)} ({hours(result.estimated_p50)}).
            </p>
            {Math.abs(adjust) >= 0.5 && (
              <>
                <p className="text-sm text-slate-700 dark:text-slate-300">
                  Từ giờ, dự toán mới cho dự án loại “{typeLabel(result.calibration.project_type)}” sẽ được điều chỉnh{' '}
                  {adjust > 0 ? 'tăng' : 'giảm'} khoảng {pct(adjust)} (học từ {result.calibration.type_observations} dự án cùng loại; các loại
                  khác điều chỉnh ít hơn).
                </p>
                <button
                  type="button"
                  onClick={onReestimate}
                  disabled={isLoading}
                  className="inline-flex items-center gap-1.5 text-sm font-bold text-indigo-700 dark:text-cyan-300 underline cursor-pointer disabled:opacity-50"
                >
                  <RefreshCw className="w-4 h-4" /> Tính lại dự toán của dự án này
                </button>
              </>
            )}
          </div>
        )}
      </form>

      <section className={`${card} p-6`}>
        <h2 className="text-lg font-bold mb-3">Các dự án đã xong</h2>
        {completed.length === 0 ? (
          <p className="text-slate-600 dark:text-slate-400">Chưa có dự án nào được nhập giờ thực tế.</p>
        ) : (
          <>
          <div className="mb-5">
            <GroupedBars
              series={[
                { key: 'est', label: 'Dự toán', tone: 'primary' },
                { key: 'act', label: 'Thực tế', tone: 'attention' },
              ]}
              groups={completed.slice(-6).map((c) => {
                const top = Math.max(c.actual_hours, c.estimated_p50_hours ?? 0, 1);
                return {
                  key: c.case_id,
                  label: c.title,
                  values: [
                    ...(c.estimated_p50_hours
                      ? [{ series: 'est', value: c.estimated_p50_hours / top, display: hours(c.estimated_p50_hours) }]
                      : []),
                    { series: 'act', value: c.actual_hours / top, display: hours(c.actual_hours) },
                  ],
                };
              })}
            />
          </div>
          <ul className="sm:hidden divide-y divide-slate-100 dark:divide-slate-800 text-sm">
            {completed.map((c) => {
              const d = c.estimated_p50_hours ? ((c.actual_hours - c.estimated_p50_hours) / c.estimated_p50_hours) * 100 : null;
              return (
                <li key={c.case_id} className="py-3 space-y-1.5">
                  <div className="font-semibold break-words">{c.title}</div>
                  <dl className="grid grid-cols-3 gap-2 tabular-nums">
                    <div>
                      <dt className="text-xs text-slate-600 dark:text-slate-400">Dự toán</dt>
                      <dd>{c.estimated_p50_hours ? hours(c.estimated_p50_hours) : '—'}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-slate-600 dark:text-slate-400">Thực tế</dt>
                      <dd className="font-semibold">{hours(c.actual_hours)}</dd>
                    </div>
                    <div>
                      <dt className="text-xs text-slate-600 dark:text-slate-400">Chênh lệch</dt>
                      <dd className={`font-bold ${d != null && d > 0 ? 'text-rose-700 dark:text-rose-400' : 'text-emerald-700 dark:text-emerald-400'}`}>
                        {d == null ? '—' : `${d > 0 ? '+' : '−'}${pct(d)}`}
                      </dd>
                    </div>
                  </dl>
                </li>
              );
            })}
          </ul>
          <div className="hidden sm:block overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="text-left text-slate-600 dark:text-slate-400 border-b border-slate-200 dark:border-slate-800">
                <tr>
                  <th scope="col" className="py-2 pr-3 font-semibold">Dự án</th>
                  <th scope="col" className="py-2 px-3 font-semibold text-right">Dự toán</th>
                  <th scope="col" className="py-2 px-3 font-semibold text-right">Thực tế</th>
                  <th scope="col" className="py-2 pl-3 font-semibold text-right">Chênh lệch</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                {completed.map((c) => {
                  const d = c.estimated_p50_hours ? ((c.actual_hours - c.estimated_p50_hours) / c.estimated_p50_hours) * 100 : null;
                  return (
                    <tr key={c.case_id}>
                      <td className="py-2 pr-3">{c.title}</td>
                      <td className="py-2 px-3 text-right whitespace-nowrap">{c.estimated_p50_hours ? hours(c.estimated_p50_hours) : '—'}</td>
                      <td className="py-2 px-3 text-right whitespace-nowrap font-semibold">{hours(c.actual_hours)}</td>
                      <td className={`py-2 pl-3 text-right whitespace-nowrap ${d != null && d > 0 ? 'text-rose-700 dark:text-rose-400' : 'text-emerald-700 dark:text-emerald-400'}`}>
                        {d == null ? '—' : `${d > 0 ? '+' : '−'}${pct(d)}`}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          </>
        )}
      </section>

      <button
        type="button"
        onClick={onOpenEvidence}
        className={`${card} w-full p-5 text-left hover:border-indigo-300 dark:hover:border-indigo-700 cursor-pointer`}
      >
        <div className="font-bold">Có thể tin dự toán này đến đâu? →</div>
        <div className="text-sm text-slate-600 dark:text-slate-400">
          Xem kết quả kiểm chứng trên dữ liệu thật: AI đọc mô tả, học từ giờ thực tế, nhật ký từng lần thử.
        </div>
      </button>
    </div>
  );
};
