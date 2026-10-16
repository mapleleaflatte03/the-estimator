import React from 'react';
import { TONE, type Tone } from './tone';

export interface BarRow {
  key: string;
  label: string;
  value: number;
  display?: string;
  tone?: Tone;
  tag?: { text: string; tone: Tone };
}

/** Horizontal bars, largest first; the top row is emphasised. */
export const HBarList: React.FC<{ rows: BarRow[]; max?: number; emphasiseTop?: boolean }> = ({ rows, max, emphasiseTop = true }) => {
  const top = max ?? Math.max(...rows.map((r) => r.value), 1);
  return (
    <ul className="space-y-2.5">
      {rows.map((r, i) => {
        const tone = TONE[r.tone ?? 'primary'];
        const lead = emphasiseTop && i === 0;
        return (
          <li key={r.key}>
            <div className="flex items-baseline justify-between gap-3 text-sm">
              <span className={`min-w-0 truncate ${lead ? 'font-bold text-slate-900 dark:text-white' : 'text-slate-700 dark:text-slate-300'}`} title={r.label}>
                {r.label}
                {r.tag && (
                  <span className={`ml-2 text-[11px] font-bold px-1.5 py-0.5 rounded ${TONE[r.tag.tone].soft} ${TONE[r.tag.tone].text}`}>{r.tag.text}</span>
                )}
              </span>
              <span className={`whitespace-nowrap tabular-nums ${lead ? 'font-extrabold text-slate-900 dark:text-white' : 'font-semibold text-slate-700 dark:text-slate-300'}`}>
                {r.display ?? r.value}
              </span>
            </div>
            <div className="mt-1 h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden" aria-hidden="true">
              <div className={`h-full rounded-full ${tone.bar}`} style={{ width: `${Math.max(2, (r.value / top) * 100)}%` }} />
            </div>
          </li>
        );
      })}
    </ul>
  );
};

/** P10–P90 range with the median and an optional chosen plan marker. */
export const RangeBar: React.FC<{ low: number; mid: number; high: number; plan?: number; format: (n: number) => string }> = ({
  low,
  mid,
  high,
  plan,
  format,
}) => {
  const lo = low * 0.9;
  const hi = high * 1.05;
  const x = (v: number) => `${((Math.min(Math.max(v, lo), hi) - lo) / (hi - lo || 1)) * 100}%`;
  return (
    <div className="pt-3 pb-8" role="img" aria-label={`Khoảng dao động ${format(low)} đến ${format(high)}, ước tính ${format(mid)}`}>
      <div className="relative h-3 rounded-full bg-slate-100 dark:bg-slate-800">
        <div className="absolute inset-y-0 rounded-full bg-indigo-200 dark:bg-indigo-900" style={{ left: x(low), right: `calc(100% - ${x(high)})` }} />
        <div className="absolute -top-1 bottom-[-4px] w-1 rounded bg-indigo-700 dark:bg-indigo-300" style={{ left: x(mid) }} />
        {plan != null && (
          <>
            <div className="absolute -top-1.5 bottom-[-6px] w-1 rounded bg-amber-500" style={{ left: x(plan) }} />
            <span className="absolute top-5 -translate-x-1/2 text-xs font-bold text-amber-800 dark:text-amber-300 whitespace-nowrap" style={{ left: x(plan) }}>
              Dự trù {format(plan)}
            </span>
          </>
        )}
        <span className="absolute top-5 text-[11px] text-slate-600 dark:text-slate-400 whitespace-nowrap" style={{ left: x(low) }}>
          {format(low)}
        </span>
        <span className="absolute top-5 -translate-x-full text-[11px] text-slate-600 dark:text-slate-400 whitespace-nowrap" style={{ left: x(high) }}>
          {format(high)}
        </span>
      </div>
    </div>
  );
};

/** Small multiple: one row per group, bars for each series, values as fractions (0–1). */
export const GroupedBars: React.FC<{
  groups: { key: string; label: string; values: { series: string; value: number; display: string }[] }[];
  series: { key: string; label: string; tone: Tone }[];
}> = ({ groups, series }) => (
  <div className="space-y-3">
    <div className="flex flex-wrap gap-3 text-xs text-slate-700 dark:text-slate-300">
      {series.map((s) => (
        <span key={s.key} className="inline-flex items-center gap-1.5">
          <span className={`w-3 h-2.5 rounded ${TONE[s.tone].bar}`} /> {s.label}
        </span>
      ))}
    </div>
    {groups.map((g) => (
      <div key={g.key} className="space-y-1">
        <div className="text-xs font-semibold text-slate-700 dark:text-slate-300">{g.label}</div>
        {series.map((s) => {
          const v = g.values.find((x) => x.series === s.key);
          if (!v) return null;
          return (
            <div key={s.key} className="flex items-center gap-2">
              <div className="flex-1 h-2.5 rounded-full bg-slate-100 dark:bg-slate-800 overflow-hidden" aria-hidden="true">
                <div className={`h-full rounded-full ${TONE[s.tone].bar}`} style={{ width: `${Math.max(2, v.value * 100)}%` }} />
              </div>
              <span className="w-14 text-right text-xs tabular-nums font-semibold text-slate-800 dark:text-slate-200">{v.display}</span>
            </div>
          );
        })}
      </div>
    ))}
  </div>
);
