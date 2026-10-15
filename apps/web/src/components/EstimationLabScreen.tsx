import React, { useMemo, useState } from 'react';
import { AlertTriangle, HelpCircle } from 'lucide-react';
import type { EstimateVersion } from '../types';
import { card, hours } from '../ui';

interface EstimationLabScreenProps {
  version: EstimateVersion;
  openQuestions: number;
  onGoToQuestions: () => void;
}

type Currency = 'VND' | 'USD';

const HIDDEN_NOTES = new Set(['scope_breadth', 'quality_gate']);
const X0 = 10;
const X1 = 790;
const Y_BASE = 150;
const Y_TOP = 10;
const HOURS_PER_PERSON_WEEK = 32;

export const EstimationLabScreen: React.FC<EstimationLabScreenProps> = ({ version, openQuestions, onGoToQuestions }) => {
  const { forecast } = version;
  const [confidence, setConfidence] = useState(80);
  const [currency, setCurrency] = useState<Currency>('VND');
  const [rate, setRate] = useState<Record<Currency, number>>({ VND: 500000, USD: 25 });
  const [people, setPeople] = useState(3);

  const curve = useMemo(() => {
    const pts = new Map<number, number>();
    (forecast.percentile_curve || []).forEach(([p, h]) => pts.set(p, h));
    pts.set(10, forecast.p10_hours);
    pts.set(50, forecast.p50_hours);
    pts.set(80, forecast.p80_hours);
    pts.set(90, forecast.p90_hours);
    return [...pts.entries()].sort((a, b) => a[0] - b[0]);
  }, [forecast]);

  const hoursAt = (pct: number) => {
    if (pct <= curve[0][0]) return curve[0][1];
    for (let i = 1; i < curve.length; i++) {
      if (pct <= curve[i][0]) {
        const [pa, ha] = curve[i - 1];
        const [pb, hb] = curve[i];
        return ha + ((pct - pa) / (pb - pa)) * (hb - ha);
      }
    }
    return curve[curve.length - 1][1];
  };

  const maxPct = curve[curve.length - 1][0];
  const chosen = Math.round(hoursAt(confidence));
  const cost = chosen * rate[currency];
  const weeks = chosen / (people * HOURS_PER_PERSON_WEEK);
  const formatCost = (v: number) =>
    currency === 'VND'
      ? `${(v / 1_000_000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} triệu đồng`
      : `$${v.toLocaleString('en-US', { maximumFractionDigits: 0 })}`;

  const histogram = forecast.histogram || [];
  const hasChart = histogram.length > 1;
  const hMin = hasChart ? histogram[0].start : 0;
  const hMax = hasChart ? histogram[histogram.length - 1].end : 1;
  const xOf = (h: number) => X0 + ((Math.min(Math.max(h, hMin), hMax) - hMin) / (hMax - hMin || 1)) * (X1 - X0);
  const maxShare = Math.max(...histogram.map((b) => b.share), 1e-9);
  const line = histogram
    .map((b, i) => `${i ? 'L' : 'M'} ${xOf((b.start + b.end) / 2).toFixed(1)},${(Y_BASE - (b.share / maxShare) * (Y_BASE - Y_TOP)).toFixed(1)}`)
    .join(' ');
  const area = hasChart
    ? `M ${xOf((histogram[0].start + histogram[0].end) / 2).toFixed(1)},${Y_BASE} ${line.slice(1)} L ${xOf(
        (histogram[histogram.length - 1].start + histogram[histogram.length - 1].end) / 2,
      ).toFixed(1)},${Y_BASE} Z`
    : '';

  const notes = version.critic_findings.filter((f) => !HIDDEN_NOTES.has(f.category));

  return (
    <div className="max-w-4xl mx-auto space-y-6 animate-fadeIn">
      {openQuestions > 0 && (
        <div className="p-4 rounded-2xl bg-amber-50 dark:bg-amber-950/40 border border-amber-200 dark:border-amber-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-amber-900 dark:text-amber-100">
            <HelpCircle className="w-5 h-5 flex-shrink-0" />
            <span>Còn {openQuestions} câu hỏi chưa trả lời. Trả lời để dự toán sát hơn.</span>
          </div>
          <button onClick={onGoToQuestions} className="px-4 py-2 rounded-xl bg-amber-600 hover:bg-amber-500 text-white font-bold text-sm cursor-pointer">
            Trả lời ngay
          </button>
        </div>
      )}

      <section className={`${card} p-6 sm:p-8 text-center`}>
        <p className="text-slate-600 dark:text-slate-400">Ước tính khối lượng công việc</p>
        <p className="text-4xl sm:text-5xl font-extrabold tracking-tight mt-1">{hours(forecast.p50_hours)}</p>
        <p className="text-slate-700 dark:text-slate-300 mt-3">
          Thường dao động từ <strong>{hours(forecast.p10_hours)}</strong> đến <strong>{hours(forecast.p90_hours)}</strong>
        </p>
        {forecast.reference_class_p50 != null && (
          <p className="text-sm text-slate-600 dark:text-slate-400 mt-2">
            Các dự án cùng loại đã làm trước đây: khoảng {hours(forecast.reference_class_p50)}
          </p>
        )}
      </section>

      <section className={`${card} p-6 space-y-5`}>
        <div>
          <h2 className="text-lg font-bold">Lập kế hoạch</h2>
          <p className="text-sm text-slate-600 dark:text-slate-400">Càng muốn chắc chắn đủ thời gian, càng cần dự trù nhiều giờ hơn.</p>
        </div>

        {hasChart && (
          <svg viewBox="0 0 800 160" className="w-full h-28" aria-hidden="true">
            <defs>
              <clipPath id="chosenClip">
                <rect x="0" y="0" width={xOf(chosen)} height="160" />
              </clipPath>
            </defs>
            <path d={area} className="fill-slate-200 dark:fill-slate-800" />
            <path d={area} className="fill-indigo-400/60 dark:fill-cyan-500/50" clipPath="url(#chosenClip)" />
            <path d={line} fill="none" className="stroke-indigo-600 dark:stroke-cyan-400" strokeWidth="2" />
            <line x1={xOf(chosen)} x2={xOf(chosen)} y1="0" y2={Y_BASE} className="stroke-indigo-700 dark:stroke-cyan-300" strokeWidth="2" />
          </svg>
        )}

        <div className="space-y-2">
          <label htmlFor="confidence" className="flex justify-between text-sm font-semibold">
            <span>Mức chắc chắn</span>
            <span>{confidence}%</span>
          </label>
          <input
            id="confidence"
            type="range"
            min={50}
            max={maxPct}
            step={5}
            value={confidence}
            onChange={(e) => setConfidence(Number(e.target.value))}
            className="w-full accent-indigo-600 dark:accent-cyan-400 cursor-pointer"
          />
          <div className="flex justify-between text-xs text-slate-600 dark:text-slate-400">
            <span>Vừa đủ</span>
            <span>Rất an toàn</span>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div className="p-4 rounded-xl bg-indigo-50 dark:bg-indigo-950/40">
            <div className="text-sm text-slate-700 dark:text-slate-300">Nên dự trù</div>
            <div className="text-2xl font-extrabold">{hours(chosen)}</div>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900">
            <label htmlFor="rate" className="text-sm text-slate-700 dark:text-slate-300 flex items-center justify-between">
              <span>Chi phí</span>
              <span className="flex gap-1">
                {(['VND', 'USD'] as Currency[]).map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => setCurrency(c)}
                    aria-pressed={currency === c}
                    className={`px-1.5 rounded text-xs font-bold cursor-pointer ${currency === c ? 'bg-indigo-600 text-white' : 'text-slate-600 dark:text-slate-400'}`}
                  >
                    {c}
                  </button>
                ))}
              </span>
            </label>
            <div className="text-2xl font-extrabold">{formatCost(cost)}</div>
            <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 mt-1">
              <input
                id="rate"
                type="number"
                min={0}
                value={rate[currency]}
                onChange={(e) => setRate({ ...rate, [currency]: Number(e.target.value) || 0 })}
                className="w-28 px-2 py-0.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0b0f1a]"
              />
              <span>{currency === 'VND' ? 'đ' : '$'} / giờ</span>
            </div>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-900">
            <label htmlFor="people" className="text-sm text-slate-700 dark:text-slate-300">
              Thời gian với
            </label>
            <div className="text-2xl font-extrabold">khoảng {Math.max(1, Math.ceil(weeks))} tuần</div>
            <div className="flex items-center gap-1 text-xs text-slate-600 dark:text-slate-400 mt-1">
              <input
                id="people"
                type="number"
                min={1}
                max={20}
                value={people}
                onChange={(e) => setPeople(Math.max(1, Number(e.target.value) || 1))}
                className="w-14 px-2 py-0.5 rounded border border-slate-300 dark:border-slate-700 bg-white dark:bg-[#0b0f1a]"
              />
              <span>người làm</span>
            </div>
          </div>
        </div>
      </section>

      {notes.length > 0 && (
        <section className={`${card} p-6 space-y-3`}>
          <h2 className="text-lg font-bold flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            Cần lưu ý
          </h2>
          <ul className="space-y-2 list-disc pl-5 text-slate-700 dark:text-slate-300">
            {notes.map((f) => (
              <li key={f.finding_id}>{f.claim}</li>
            ))}
          </ul>
        </section>
      )}

      <details className="text-sm text-slate-600 dark:text-slate-400">
        <summary className="cursor-pointer font-semibold">Con số này được tính thế nào?</summary>
        <p className="mt-2 leading-relaxed">
          Mỗi công việc được ước tính số giờ ít nhất, thường gặp và nhiều nhất. Hệ thống chạy thử 10.000 kịch bản, trong đó mức
          chênh lệch giữa dự toán và thực tế được lấy từ dữ liệu thật của hơn 10.000 công việc phần mềm đã làm. Khi bạn nhập giờ thực
          tế của các dự án đã xong, các dự toán sau sẽ tự điều chỉnh
          {forecast.calibration_multiplier !== 1 && ` (hiện đang nhân ×${forecast.calibration_multiplier.toFixed(2)})`}.
        </p>
      </details>
    </div>
  );
};
