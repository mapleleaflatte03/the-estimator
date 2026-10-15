import React, { useEffect, useState } from 'react';
import { CheckCircle2, RefreshCw } from 'lucide-react';
import type { ActualsResult, BenchmarkReport, EstimateVersion, HistoricalCase } from '../types';
import { fetchHistoricalCases } from '../api';
import { card, hours } from '../ui';

interface AccuracyLearningScreenProps {
  version: EstimateVersion;
  onRecordActuals: (actualHours: number, reasons: string[]) => Promise<ActualsResult>;
  onRunBenchmark: () => Promise<BenchmarkReport>;
  onReestimate: () => Promise<void>;
  isLoading: boolean;
}

const pct = (v: number) => `${Math.abs(Math.round(v))}%`;
const hours1 = (v: number) => `${v.toLocaleString('vi-VN', { maximumFractionDigits: 1 })} giờ`;
const diffText = (actual: number, estimate: number) => {
  const d = ((actual - estimate) / estimate) * 100;
  if (Math.abs(d) < 1) return 'đúng bằng dự toán';
  return d > 0 ? `nhiều hơn dự toán ${pct(d)}` : `ít hơn dự toán ${pct(d)}`;
};

export const AccuracyLearningScreen: React.FC<AccuracyLearningScreenProps> = ({
  version,
  onRecordActuals,
  onRunBenchmark,
  onReestimate,
  isLoading,
}) => {
  const [actualHours, setActualHours] = useState('');
  const [note, setNote] = useState('');
  const [result, setResult] = useState<ActualsResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [completed, setCompleted] = useState<HistoricalCase[]>([]);
  const [report, setReport] = useState<BenchmarkReport | null>(null);
  const [checking, setChecking] = useState(false);

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

  const runCheck = async () => {
    setChecking(true);
    try {
      setReport(await onRunBenchmark());
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setChecking(false);
    }
  };

  const adjust = result ? (result.calibration.multiplier_after - result.calibration.multiplier_before) * 100 : 0;
  const holdout = report?.sip.holdout;
  const curve = report?.sip.learning_curve.points ?? [];
  const rollingWins = curve.filter((p) => p.rolling_mae < p.frozen_mae).length;

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
              placeholder="VD: khách đổi yêu cầu giữa chừng"
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
                  Từ giờ, các dự toán mới sẽ được điều chỉnh {adjust > 0 ? 'tăng' : 'giảm'} khoảng {pct(adjust)}.
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
          <div className="overflow-x-auto">
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
        )}
      </section>

      <details className={`${card} p-6`}>
        <summary className="font-bold cursor-pointer">Có thể tin dự toán này đến đâu?</summary>
        <div className="mt-3 space-y-3 text-sm text-slate-700 dark:text-slate-300 leading-relaxed">
          <p>
            Cách tính được kiểm tra trên dữ liệu thật của một công ty phần mềm (hơn 10.000 công việc, 2004–2014): học từ các năm
            trước, rồi so với kết quả thực tế của các năm sau.
          </p>
          {!report ? (
            <button
              type="button"
              onClick={runCheck}
              disabled={checking}
              className="px-4 py-2 rounded-xl border border-slate-300 dark:border-slate-700 font-semibold hover:border-indigo-400 cursor-pointer disabled:opacity-50"
            >
              {checking ? 'Đang kiểm tra…' : 'Chạy kiểm tra'}
            </button>
          ) : (
            holdout && (
              <ul className="list-disc pl-5 space-y-1">
                <li>
                  Trên {holdout.n_test.toLocaleString('vi-VN')} công việc chưa từng thấy, sai lệch trung bình giảm từ{' '}
                  {hours1(holdout.baseline.mae)} xuống {hours1(holdout.calibrated.mae)} mỗi công việc (giảm{' '}
                  {pct(((holdout.calibrated.mae - holdout.baseline.mae) / holdout.baseline.mae) * 100)}) so với ước lượng ban đầu của người làm.
                </li>
                {holdout.calibrated.interval_coverage != null && (
                  <li>Kết quả thực tế nằm trong khoảng dao động dự báo ở {Math.round(holdout.calibrated.interval_coverage)}% số trường hợp.</li>
                )}
                {curve.length > 0 && (
                  <li>
                    Khi được học thêm dữ liệu mới mỗi năm, kết quả tốt hơn so với không học thêm ở {rollingWins}/{curve.length} năm.
                  </li>
                )}
                {report.in_app.status === 'ok' && report.in_app.uncalibrated_mae != null && report.in_app.calibrated_mae != null && (
                  <li>
                    Với các dự án của bạn: sai lệch trung bình {hours(report.in_app.uncalibrated_mae)} →{' '}
                    {hours(report.in_app.calibrated_mae)} sau khi điều chỉnh.
                  </li>
                )}
                <li>
                  Lưu ý: số giờ cho từng loại công việc vẫn là ước tính ban đầu, sẽ sát dần khi bạn nhập giờ thực tế của nhiều dự án
                  hơn.
                </li>
              </ul>
            )
          )}
          <p className="text-xs text-slate-600 dark:text-slate-400">
            Nguồn dữ liệu:{' '}
            <a href="https://github.com/Derek-Jones/SiP_dataset" target="_blank" rel="noreferrer" className="underline">
              SiP dataset
            </a>{' '}
            (CC BY-NC-ND 4.0).
          </p>
        </div>
      </details>
    </div>
  );
};
